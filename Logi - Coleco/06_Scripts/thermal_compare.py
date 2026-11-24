"""Cited two-point thermal comparisons with explicit measurement conditions."""
import json
import math
from pathlib import Path
import re

from kb_store import read, utc_now
from local_extract import IngestError
from qa import citation, coverage

CONDITIONS = ('stage', 'hardware_revision', 'firmware', 'sample_id', 'workload',
              'mounting', 'sensor_location', 'thermal_state', 'noise_method',
              'ambient_temperature_c', 'som_power_w', 'fan_speed_rpm')
METRICS = ('cpu_dts_c', 'noise_dba', 'surface_temperature_c', 'airflow_cfm')
UNITS = {'ambient_temperature_c': '°C', 'som_power_w': 'W', 'fan_speed_rpm': 'RPM',
         'cpu_dts_c': '°C', 'noise_dba': 'dBA', 'surface_temperature_c': '°C', 'airflow_cfm': 'CFM'}
KINDS = ('chunk', 'legacy_cell', 'fan_measurement', 'remote')


def invalid(message):
    raise IngestError('invalid_comparison', message)


def finite_number(value):
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def difference(left, right):
    result = right - left
    if not finite_number(result):
        invalid('A calculated difference exceeds the supported finite numerical range.')
    return result


def load_comparison(path):
    path = Path(path)
    if path.stat().st_size > 262144:
        invalid('The two-point JSON input must be at most 256 KiB.')
    try:
        value = json.loads(path.read_text(encoding='utf-8-sig'),
                           parse_constant=lambda _: invalid('Comparison JSON requires finite numbers.'))
    except (ValueError, UnicodeError):
        invalid('The comparison input must be UTF-8 JSON.')
    return value


def validate(value):
    if not isinstance(value, dict) or set(value) - {'schema_version', 'varying_conditions', 'points'}:
        invalid('Use schema_version, varying_conditions and points.')
    if type(value.get('schema_version')) is not int or value['schema_version'] != 1:
        invalid('schema_version must be 1.')
    varying = value.get('varying_conditions', [])
    if not isinstance(varying, list) or any(not isinstance(k, str) or k not in CONDITIONS for k in varying):
        invalid('varying_conditions must list known condition fields.')
    if len(set(varying)) != len(varying):
        invalid('Do not duplicate varying condition fields.')
    points = value.get('points')
    if not isinstance(points, list) or len(points) != 2:
        invalid('Supply exactly two points.')
    labels = []
    for point in points:
        if not isinstance(point, dict) or set(point) - {'label', 'basis', 'conditions', 'metrics', 'citations', 'note'}:
            invalid('Unknown point fields.')
        label = point.get('label')
        if not isinstance(label, str) or not label.strip() or len(label) > 120:
            invalid('Each point needs a nonempty label up to 120 characters.')
        labels.append(label.strip())
        if 'note' in point and (not isinstance(point['note'], str) or len(point['note']) > 1000):
            invalid('An optional note must be a string up to 1000 characters.')
        if point.get('basis') not in ('measured', 'estimate'):
            invalid('Each point basis must be measured or estimate.')
        conditions, metrics, refs = (point.get(k, {}) for k in ('conditions', 'metrics', 'citations'))
        if not isinstance(conditions, dict) or set(conditions) - set(CONDITIONS):
            invalid('Unknown condition fields; use fixed units from the template.')
        if not isinstance(metrics, dict) or set(metrics) - set(METRICS):
            invalid('Unknown metric fields; use fixed units from the template.')
        for key, datum in (conditions | metrics).items():
            if datum is None or datum == '':
                continue
            if key in UNITS:
                if not finite_number(datum):
                    invalid('Numerical fields require finite numbers with the template units.')
            elif not isinstance(datum, str) or len(datum) > 256:
                invalid('Text conditions require strings up to 256 characters.')
        if not isinstance(refs, dict) or set(refs) - set(CONDITIONS + METRICS):
            invalid('Citations must be keyed by condition or metric field.')
        for field_refs in refs.values():
            if not isinstance(field_refs, list) or len(field_refs) > 8:
                invalid('Each field accepts at most eight evidence references.')
            for ref in field_refs:
                if not isinstance(ref, dict) or set(ref) != {'kind', 'id'}:
                    invalid('An evidence reference requires kind and id.')
                if ref['kind'] not in KINDS or type(ref['id']) is not int or ref['id'] < 1:
                    invalid('Evidence references require a known kind and positive integer id.')
    if labels[0] == labels[1]:
        invalid('Point labels must differ.')


def normalized(text):
    return ' '.join(text.casefold().split())


def value_seen(value, field, evidence):
    """Check literal support only; the engineering meaning and units need source review."""
    if isinstance(value, str):
        return normalized(value) in normalized(evidence['text'])
    details = evidence.get('details') or {}
    for key in (field, 'numeric_value'):
        saved = details.get(key)
        if type(saved) in (int, float) and saved == value:
            return True
    tokens = re.findall(r'(?<![\w.])[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?(?![\w.])', evidence['text'])
    return any(float(token) == value for token in tokens)


def compare(c, value):
    validate(value)
    varying = value.get('varying_conditions', [])
    points = value['points']
    blockers, citations, cache, warnings = [], [], {}, []
    for point in points:
        supplied = point.get('conditions', {}) | point.get('metrics', {})
        for field in CONDITIONS:
            datum = supplied.get(field)
            if datum is None or (isinstance(datum, str) and not datum.strip()):
                blockers.append({'point': point['label'], 'field': field, 'code': 'missing_condition'})
        for field, datum in supplied.items():
            if datum is None or (isinstance(datum, str) and not datum.strip()):
                continue
            refs = point.get('citations', {}).get(field, [])
            if not refs:
                blockers.append({'point': point['label'], 'field': field, 'code': 'missing_citation'})
                continue
            supported = False
            for ref in refs:
                key = (ref['kind'], ref['id'])
                if key not in cache:
                    try:
                        evidence = read(c, *key, 20000)
                        code = 'archived_evidence' if not evidence['is_current'] else None
                        if evidence.get('availability', 'active') != 'active':
                            code = 'unavailable_evidence'
                        cid = 'C' + str(len(citations) + 1)
                        cite = citation(evidence, cid)
                        cite.update(text=evidence['text'][:2000],
                                    text_truncated=evidence['text_truncated'] or len(evidence['text']) > 2000,
                                    untrusted_source_text=True)
                        citations.append(cite)
                        cache[key] = (evidence, code)
                    except IngestError as exc:
                        cache[key] = (None, exc.code)
                evidence, code = cache[key]
                if code:
                    blockers.append({'point': point['label'], 'field': field, 'code': code, 'reference': ref})
                elif value_seen(datum, field, evidence):
                    supported = True
            if not supported:
                blockers.append({'point': point['label'], 'field': field, 'code': 'value_not_found'})
        if point['basis'] == 'estimate':
            warnings.append(point['label'] + ' 為估算點，仍需同條件量測驗證。')
    for field in CONDITIONS:
        left = points[0].get('conditions', {}).get(field)
        right = points[1].get('conditions', {}).get(field)
        equal = normalized(left) == normalized(right) if isinstance(left, str) and isinstance(right, str) else left == right
        if not equal and field not in varying:
            blockers.append({'field': field, 'code': 'undeclared_condition_difference',
                             'left': left, 'right': right})
    common = [field for field in METRICS if all(type(point.get('metrics', {}).get(field)) in (int, float) for point in points)]
    if not common:
        blockers.append({'code': 'no_common_metrics'})
    differences = [field for field in varying if points[0].get('conditions', {}).get(field) != points[1].get('conditions', {}).get(field)]
    if len(differences) > 1:
        warnings.append('多個條件同時變化；差值僅描述這兩個輸入點，因果關係需額外驗證。')
    if any(cite['completeness'] != 'full' or cite['text_truncated'] for cite in citations):
        warnings.append('部分引用為文字投影或截斷內容，請核對原始附件、表格及上下文。')
    warnings.append('引用值檢查只確認值出現在儲存的證據中；單位、欄位意義與量測條件需核對原始來源。')
    warnings.append('噪音差值以 dBA 報告，沒有換算為聲功率或主觀響度比例。')
    deltas = {field: difference(points[0]['metrics'][field], points[1]['metrics'][field]) for field in common} if not blockers else {}
    output_points = []
    for point in points:
        derived = {}
        if not blockers and type(point.get('metrics', {}).get('cpu_dts_c')) in (int, float):
            derived['cpu_to_ambient_delta_c'] = difference(point['conditions']['ambient_temperature_c'], point['metrics']['cpu_dts_c'])
        output_points.append(dict(point, derived=derived))
    return {'status': 'not_comparable' if blockers else 'comparable', 'generated_at_utc': utc_now(),
            'comparison_basis': 'user-supplied conditions with literal cited-value readback',
            'points': output_points, 'varying_conditions': varying, 'deltas': deltas,
            'delta_direction': 'second point minus first point', 'units': UNITS,
            'blockers': blockers, 'citations': citations, 'warnings': warnings,
            'causal_inference': False, 'measurement_validation': False, 'coverage': coverage(c)}
