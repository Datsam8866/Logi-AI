"""Phase 4 CLI acceptance using synthetic cited evidence and disposable SQLite."""
from contextlib import closing
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
from kb_store import connect, initialize, ingest
import remote_store


class Phase4Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = self.root / 'kb.sqlite3'
        initialize(self.db, self.root)

    def cli(self, *args, ok=True):
        result = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'coleco_kb.py'),
                                 '--db', str(self.db), *map(str, args)],
                                capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0 if ok else 1, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def remote(self, text, provider='jira', remote_id='synthetic-1', revision='v1',
               completeness='full', updated='2026-01-02T00:00:00Z'):
        with closing(connect(self.db)) as c, c:
            return remote_store.upsert(c, {'provider': provider, 'remote_id': remote_id,
                'title': 'Synthetic Coleco thermal evidence', 'text': text,
                'source_url': 'https://example.test/source/' + remote_id,
                'source_created_at_utc': '2026-01-01T00:00:00Z',
                'source_updated_at_utc': updated, 'revision_tag': revision,
                'completeness': completeness, 'metadata': {}})['version_id']

    def local(self, text, name='source.txt'):
        path = self.root / name
        path.write_text(text, encoding='utf-8')
        with closing(connect(self.db)) as c:
            ingest(c, path)
        return path

    def input(self, value):
        path = self.root / 'comparison.json'
        path.write_text(json.dumps(value), encoding='utf-8')
        return path

    def comparison(self):
        conditions = {'stage': 'PA2', 'hardware_revision': 'R1', 'firmware': 'F1',
            'sample_id': 'DUT1', 'workload': 'Burn Out', 'mounting': 'Free Standing',
            'sensor_location': 'CPU DTS', 'thermal_state': 'steady_state',
            'noise_method': '1m chamber', 'ambient_temperature_c': 25,
            'som_power_w': 10, 'fan_speed_rpm': 2500}
        points = []
        for i, metrics in enumerate([{'cpu_dts_c': 85, 'noise_dba': 25.1},
                                     {'cpu_dts_c': 83, 'noise_dba': 24.9}]):
            text = '\n'.join(key + '=' + str(value) for key, value in (conditions | metrics).items())
            vid = self.remote(text, remote_id='point-' + str(i))
            points.append({'label': 'Point ' + str(i), 'basis': 'measured',
                'conditions': copy.deepcopy(conditions), 'metrics': metrics,
                'citations': {key: [{'kind': 'remote', 'id': vid}]
                              for key in conditions | metrics}})
        return {'schema_version': 1, 'varying_conditions': [], 'points': points}

    def test_ask_source_quotes_citations_and_read_only_database(self):
        self.local('The measured CPU DTS is 85 C under Burn Out at 25 C ambient.')
        before = self.db.read_bytes()
        result = self.cli('ask', 'CPU DTS', '--query', 'CPU DTS')
        self.assertEqual(result['status'], 'evidence_found')
        self.assertEqual(result['answer_mode'], 'extractive')
        self.assertFalse(result['coverage']['live_checked'])
        self.assertEqual(self.db.read_bytes(), before)
        for statement in result['source_statements']:
            cite = next(c for c in result['citations'] if c['citation_id'] == statement['citation_id'])
            source = self.cli('read', cite['kind'], cite['id'], '--max-chars', 20000)
            self.assertIn(statement['text'], source['text'])
            self.assertEqual(cite['sha256'], source['sha256'])
            self.assertTrue(cite['locator'])

    def test_ask_chinese_thermal_terms_and_remote_not_starved(self):
        for i in range(25):
            self.local('Thermal report heading', str(i) + '.txt')
        vid = self.remote('Thermal risk: CPU DTS requires a repeat measurement.')
        result = self.cli('/ask', 'Coleco 目前熱風險與溫度有哪些證據？', '--limit', 4)
        self.assertTrue(any(c['kind'] == 'remote' and c['id'] == vid for c in result['citations']))
        self.assertLessEqual(len(result['citations']), 4)
        self.assertTrue(any(c['kind'] == 'chunk' for c in result['citations']))

    def test_latest_fan_policy_remains_explicitly_unconfirmed(self):
        self.remote('Fan policy proposal: use 2500 RPM.', provider='chat', completeness='partial', updated=None)
        result = self.cli('ask', 'What is the latest fan policy?')
        self.assertEqual(result['policy_confirmation'], 'requires_authoritative_source_review')
        self.assertTrue(any('正式' in q for q in result['open_questions']))
        self.assertTrue(any(c['completeness'] == 'partial' for c in result['citations']))
        self.assertTrue(any(c['source_updated_at_utc'] is None for c in result['citations']))

    def test_latest_non_fan_policy_requires_authoritative_review(self):
        self.remote('Thermal policy proposal requires approval.')
        for question in ['What is the latest thermal policy?', '目前最新熱政策為何？']:
            result = self.cli('ask', question)
            self.assertEqual(result['policy_confirmation'], 'requires_authoritative_source_review')
            self.assertTrue(any('正式' in q for q in result['open_questions']))

    def test_no_evidence_and_unavailable_old_versions_not_promoted(self):
        old = self.remote('Thermal obsolete evidence')
        current = self.remote('Thermal new evidence', revision='v2')
        with closing(connect(self.db)) as c, c:
            remote_store.mark_unavailable(c, 'jira', 'synthetic-1', 'inaccessible')
        result = self.cli('ask', 'thermal', '--query', 'thermal')
        self.assertEqual(result['status'], 'insufficient_evidence')
        self.assertEqual(result['citations'], [])
        self.assertEqual(result['coverage']['unavailable_records'], 1)
        self.assertEqual(self.cli('read', 'remote', old)['is_current'], False)
        self.assertEqual(self.cli('read', 'remote', current)['availability'], 'inaccessible')

    def test_coverage_incomplete_and_missing_sources_are_visible(self):
        self.remote('Thermal evidence')
        with closing(connect(self.db)) as c:
            remote_store.apply_batch(c, 'jira', 'synthetic', 0, [],
                {'window_start': '2026-01-01T00:00:00Z', 'window_end': '2026-02-01T00:00:00Z',
                 'watermark': None, 'complete': False,
                 'cursor': {'pending': [{'id': 'remaining'}], 'page_token': 'secret-cursor'}}, [])
        result = self.cli('ask', 'thermal')
        self.assertIn('drive', result['coverage']['providers_without_checkpoint'])
        self.assertFalse(result['coverage']['checkpoints'][0]['complete'])
        self.assertNotIn('secret-cursor', json.dumps(result))

    def test_ask_limits_and_missing_database_are_json_errors(self):
        self.assertEqual(self.cli('ask', ' ', ok=False)['error_code'], 'invalid_ask')
        self.assertEqual(self.cli('ask', 'thermal', '--limit', 100, ok=False)['error_code'], 'invalid_ask')
        self.assertEqual(self.cli('ask', 'thermal', '--max-chars', 0, ok=False)['error_code'], 'invalid_ask')
        self.db.unlink()
        self.assertEqual(self.cli('ask', 'thermal', ok=False)['error_code'], 'missing_database')
        self.assertFalse(self.db.exists())

    def test_compare_matched_conditions_deltas_and_read_only(self):
        value = self.comparison()
        before = self.db.read_bytes()
        result = self.cli('/compare', self.input(value))
        self.assertEqual(result['status'], 'comparable')
        self.assertEqual(result['deltas']['cpu_dts_c'], -2)
        self.assertAlmostEqual(result['deltas']['noise_dba'], -0.2)
        self.assertEqual(result['points'][0]['derived']['cpu_to_ambient_delta_c'], 60)
        self.assertFalse(result['causal_inference'])
        self.assertEqual(self.db.read_bytes(), before)
        self.assertTrue(result['citations'])

    def test_compare_undeclared_difference_and_missing_fields_block_deltas(self):
        value = self.comparison()
        value['points'][1]['conditions']['ambient_temperature_c'] = 30
        result = self.cli('compare', self.input(value))
        self.assertEqual(result['status'], 'not_comparable')
        self.assertEqual(result['deltas'], {})
        self.assertIn('ambient_temperature_c', json.dumps(result['blockers']))
        value['points'][1]['conditions']['ambient_temperature_c'] = 25
        value['points'][1]['conditions']['sample_id'] = None
        result = self.cli('compare', self.input(value))
        self.assertEqual(result['status'], 'not_comparable')
        self.assertIn('sample_id', json.dumps(result['blockers']))

    def test_compare_explicit_variation_and_estimated_point(self):
        value = self.comparison()
        value['points'][1]['conditions']['fan_speed_rpm'] = 3000
        vid = self.remote('fan_speed_rpm=3000', remote_id='changed-fan')
        value['points'][1]['citations']['fan_speed_rpm'] = [{'kind': 'remote', 'id': vid}]
        value['points'][1]['basis'] = 'estimate'
        value['varying_conditions'] = ['fan_speed_rpm']
        result = self.cli('compare', self.input(value))
        self.assertEqual(result['status'], 'comparable')
        self.assertEqual(result['varying_conditions'], ['fan_speed_rpm'])
        self.assertFalse(result['measurement_validation'])
        self.assertTrue(any('估算' in text for text in result['warnings']))

    def test_compare_missing_invalid_stale_and_unavailable_citations(self):
        value = self.comparison()
        value['points'][0]['citations']['cpu_dts_c'] = []
        result = self.cli('compare', self.input(value))
        self.assertEqual(result['status'], 'not_comparable')
        value = self.comparison()
        ref = value['points'][0]['citations']['cpu_dts_c'][0]
        self.remote('Changed thermal evidence', remote_id='point-0', revision='new')
        result = self.cli('compare', self.input(value))
        self.assertIn('archived_evidence', json.dumps(result['blockers']))
        ref['id'] = 999999
        result = self.cli('compare', self.input(value))
        self.assertIn('missing_evidence', json.dumps(result['blockers']))
        value = self.comparison()
        with closing(connect(self.db)) as c, c:
            remote_store.mark_unavailable(c, 'jira', 'point-1', 'unverified')
        result = self.cli('compare', self.input(value))
        self.assertIn('unavailable_evidence', json.dumps(result['blockers']))

    def test_compare_numbers_must_be_found_in_cited_evidence(self):
        value = self.comparison()
        value['points'][0]['metrics']['cpu_dts_c'] = 99.9
        result = self.cli('compare', self.input(value))
        self.assertEqual(result['status'], 'not_comparable')
        self.assertIn('value_not_found', json.dumps(result['blockers']))

    def test_compare_rejects_unknown_fields_nonfinite_bool_and_bad_json(self):
        for mutation in ['unknown', 'infinite', 'bool', 'version', 'points', 'ref']:
            value = self.comparison()
            if mutation == 'unknown': value['points'][0]['metrics']['cpu_dts_f'] = 185
            if mutation == 'infinite': value['points'][0]['metrics']['cpu_dts_c'] = float('inf')
            if mutation == 'bool': value['points'][0]['conditions']['som_power_w'] = True
            if mutation == 'version': value['schema_version'] = 2
            if mutation == 'points': value['points'] = value['points'][:1]
            if mutation == 'ref': value['points'][0]['citations']['cpu_dts_c'] = [{'kind': 'remote', 'id': True}]
            with self.subTest(mutation=mutation):
                self.assertEqual(self.cli('compare', self.input(value), ok=False)['error_code'], 'invalid_comparison')
        path = self.root / 'bad.json'
        path.write_text('{', encoding='utf-8')
        self.assertEqual(self.cli('compare', path, ok=False)['error_code'], 'invalid_comparison')

    def test_compare_huge_integer_reports_json_error(self):
        value = self.comparison()
        value['points'][0]['metrics']['cpu_dts_c'] = 10 ** 400
        self.assertEqual(self.cli('compare', self.input(value), ok=False)['error_code'], 'invalid_comparison')

    def test_compare_note_rejects_non_string_and_nonstandard_json_constants(self):
        for note in [float('nan'), float('inf'), True, {'unexpected': 'value'}]:
            value = self.comparison()
            value['points'][0]['note'] = note
            self.assertEqual(self.cli('compare', self.input(value), ok=False)['error_code'], 'invalid_comparison')

    def test_compare_overflow_in_deltas_and_derived_values_reports_json_error(self):
        value = self.comparison()
        for i, number in enumerate([-1e308, 1e308]):
            vid = self.remote('CPU DTS ' + str(number), remote_id='overflow-' + str(i))
            value['points'][i]['metrics']['cpu_dts_c'] = number
            value['points'][i]['citations']['cpu_dts_c'] = [{'kind': 'remote', 'id': vid}]
        self.assertEqual(self.cli('compare', self.input(value), ok=False)['error_code'], 'invalid_comparison')
        value = self.comparison()
        vid = self.remote('CPU DTS 1e308 ambient -1e308', remote_id='derived-overflow')
        for point in value['points']:
            point['metrics']['cpu_dts_c'] = 1e308
            point['conditions']['ambient_temperature_c'] = -1e308
            for field in ('cpu_dts_c', 'ambient_temperature_c'):
                point['citations'][field] = [{'kind': 'remote', 'id': vid}]
        self.assertEqual(self.cli('compare', self.input(value), ok=False)['error_code'], 'invalid_comparison')


if __name__ == '__main__':
    unittest.main()
