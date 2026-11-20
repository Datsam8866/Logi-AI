"""CLI acceptance tests using disposable, synthetic local reports."""
import hashlib
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import zipfile

CLI = Path(__file__).resolve().parents[1] / 'coleco_kb.py'


class LocalKbTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = self.root / 'kb.sqlite3'

    def run_cli(self, *args, ok=True):
        result = subprocess.run(
            [sys.executable, '-B', str(CLI), '--db', str(self.db), *map(str, args)],
            capture_output=True, text=True, encoding='utf-8',
        )
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertTrue(result.stdout.strip().startswith('{'), result.stderr + result.stdout)
        return json.loads(result.stdout)

    def write_text(self, name='report.md', text='Thermal evidence\nCPU measurement\n'):
        path = self.root / name
        path.write_text(text, encoding='utf-8')
        return path

    def zip_file(self, name, parts):
        path = self.root / name
        with zipfile.ZipFile(path, 'w') as z:
            for part, text in parts.items():
                z.writestr(part, text)
        return path

    def test_init_and_read_only_status(self):
        result = self.run_cli('init')
        self.assertEqual(result['status'], 'ready')
        before = self.db.read_bytes()
        state = self.run_cli('status')
        self.assertEqual(state['integrity'], 'ok')
        self.assertEqual(self.db.read_bytes(), before)

    def test_missing_database_status_does_not_create_database(self):
        result = self.run_cli('status', ok=False)
        self.assertEqual(result['error_code'], 'missing_database')
        self.assertFalse(self.db.exists())

    def test_duplicate_ingestion_preserves_original_and_single_version(self):
        path = self.write_text()
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(self.run_cli('ingest', path)['results'][0]['status'], 'imported')
        self.assertEqual(self.run_cli('ingest', path)['results'][0]['status'], 'unchanged')
        self.assertEqual(self.run_cli('status')['versions'], 1)
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before)

    def test_updated_content_keeps_history_and_only_current_search_results(self):
        path = self.write_text(text='ObsoleteUniqueEvidence')
        self.run_cli('ingest', path)
        old = self.run_cli('search', 'ObsoleteUniqueEvidence')['hits'][0]
        path.write_text('CurrentUniqueEvidence', encoding='utf-8')
        self.run_cli('ingest', path)
        self.assertEqual(self.run_cli('status')['versions'], 2)
        self.assertEqual(self.run_cli('search', 'ObsoleteUniqueEvidence')['hits'], [])
        self.assertEqual(len(self.run_cli('search', 'CurrentUniqueEvidence')['hits']), 1)
        read = self.run_cli('read', old['kind'], old['id'])
        self.assertFalse(read['is_current'])
        self.assertEqual(read['text'], 'ObsoleteUniqueEvidence')
        path.write_text('ObsoleteUniqueEvidence', encoding='utf-8')
        self.assertEqual(self.run_cli('ingest', path)['results'][0]['status'], 'reused')
        self.assertEqual(self.run_cli('status')['versions'], 2)

    def test_failed_update_does_not_replace_current_version(self):
        path = self.write_text(text='PreservedEvidence')
        self.run_cli('ingest', path)
        path.write_bytes(b'\xff\xfe\x00invalid')
        result = self.run_cli('ingest', path, ok=False)
        self.assertEqual(result['results'][0]['status'], 'error')
        self.assertEqual(self.run_cli('status')['versions'], 1)
        self.assertTrue(self.run_cli('search', 'PreservedEvidence')['hits'])
        self.assertEqual(self.run_cli('status')['failed_ingestions'], 1)

    def test_atomic_write_failure_is_logged_without_replacing_current_version(self):
        path = self.write_text(text='PreservedEvidence')
        self.run_cli('ingest', path)
        with closing(sqlite3.connect(self.db)) as c:
            c.execute("CREATE TRIGGER block_write BEFORE INSERT ON local_chunks WHEN new.text='BlockedWrite' BEGIN SELECT RAISE(ABORT,'synthetic failure'); END")
            c.commit()
        path.write_text('BlockedWrite', encoding='utf-8')
        result = self.run_cli('ingest', path, ok=False)
        self.assertIn('results', result)
        self.assertEqual(result['results'][0]['error_code'], 'database_write_failed')
        self.assertEqual(self.run_cli('status')['versions'], 1)
        self.assertEqual(self.run_cli('status')['failed_ingestions'], 1)
        self.assertTrue(self.run_cli('search', 'PreservedEvidence')['hits'])

    def test_late_matches_have_centered_snippets_and_bounded_read_offsets(self):
        path = self.write_text(text='prefix ' * 1000 + 'LateUniqueEvidence')
        self.run_cli('ingest', path)
        hit = self.run_cli('search', 'LateUniqueEvidence')['hits'][0]
        self.assertIn('LateUniqueEvidence', hit['snippet'])
        self.assertGreater(hit['snippet_start'], 0)
        read = self.run_cli('read', hit['kind'], hit['id'], '--offset', str(hit['snippet_start']), '--max-chars', '320')
        self.assertIn('LateUniqueEvidence', read['text'])

    def test_search_has_source_hash_locator_and_readback(self):
        path = self.write_text('report.txt', 'first line\nExactQuotedEvidence\n')
        self.run_cli('ingest', path)
        hit = self.run_cli('search', 'ExactQuotedEvidence')['hits'][0]
        self.assertEqual(hit['locator'], 'lines 2-2')
        self.assertEqual(hit['source_path'], str(path.resolve()))
        self.assertEqual(hit['sha256'], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertTrue(hit['imported_at_utc'])
        self.assertEqual(self.run_cli('read', hit['kind'], hit['id'])['text'], 'ExactQuotedEvidence')

    def test_literal_unicode_and_sql_like_queries(self):
        path = self.write_text(text='中文散熱驗證\nLiteral 100%_value\n')
        self.run_cli('ingest', path)
        self.assertTrue(self.run_cli('search', '散熱')['hits'])
        self.assertTrue(self.run_cli('search', '100%_value')['hits'])
        self.assertEqual(self.run_cli('search', "x' OR 1=1 --")['hits'], [])
        self.assertEqual(self.run_cli('search', '"')['hits'], [])
        self.run_cli('search', 'x', '--limit', '0', ok=False)
        self.run_cli('search', ' ', ok=False)

    def test_csv_and_tsv_preserve_headers_and_row_locations(self):
        for suffix, delimiter in [('csv', ','), ('tsv', '\t')]:
            path = self.write_text('data.' + suffix, f'Condition{delimiter}Value\nFanEvidence{delimiter}3.25\n')
            self.run_cli('ingest', path)
        hits = self.run_cli('search', 'FanEvidence')['hits']
        self.assertEqual(len(hits), 2)
        self.assertTrue(all(h['locator'] == 'row 2' for h in hits))
        self.assertTrue(all('Value: 3.25' in h['snippet'] for h in hits))

    def test_xlsx_cached_formula_and_exact_cell_details(self):
        path = self.zip_file('report.xlsx', {
            'xl/workbook.xml': '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Test" sheetId="1" r:id="rId1"/></sheets></workbook>',
            'xl/_rels/workbook.xml.rels': '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>',
            'xl/worksheets/sheet1.xml': '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>CachedEvidence</t></is></c><c r="B1"><f>1+2</f><v>3</v></c><c r="C1"><f>2+2</f></c></row></sheetData></worksheet>',
        })
        self.run_cli('ingest', path)
        hit = self.run_cli('search', 'CachedEvidence')['hits'][0]
        read = self.run_cli('read', hit['kind'], hit['id'])
        self.assertEqual(read['locator'], "'Test'!A1:C1")
        self.assertEqual(read['details']['cells'][1]['formula'], '=1+2')
        self.assertEqual(read['details']['cells'][1]['raw_value'], '3')
        self.assertIsNone(read['details']['cells'][2]['raw_value'])
        self.assertIn('cached value unavailable', read['text'])

    def test_docx_paragraph_and_table_extraction(self):
        path = self.zip_file('report.docx', {'word/document.xml': '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>ParagraphEvidence</w:t></w:r></w:p><w:tbl><w:tr><w:tc><w:p><w:r><w:t>TableEvidence</w:t></w:r></w:p></w:tc></w:tr></w:tbl></w:body></w:document>'})
        self.run_cli('ingest', path)
        self.assertEqual(self.run_cli('search', 'ParagraphEvidence')['hits'][0]['locator'], 'paragraph 1')
        self.assertEqual(self.run_cli('search', 'TableEvidence')['hits'][0]['locator'], 'table 1, row 1')

    def test_pptx_slide_extraction(self):
        path = self.zip_file('report.pptx', {
            'ppt/presentation.xml': '<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><p:sldIdLst><p:sldId id="256" r:id="rId1"/></p:sldIdLst></p:presentation>',
            'ppt/_rels/presentation.xml.rels': '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="slides/slide1.xml"/></Relationships>',
            'ppt/slides/slide1.xml': '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>SlideEvidence</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld></p:sld>',
        })
        self.run_cli('ingest', path)
        self.assertEqual(self.run_cli('search', 'SlideEvidence')['hits'][0]['locator'], 'slide 1, paragraph 1')

    def test_pdf_page_extraction_and_scanned_pdf_failure(self):
        from reportlab.pdfgen import canvas
        from pypdf import PdfWriter
        path = self.root / 'report.pdf'
        pdf = canvas.Canvas(str(path))
        pdf.drawString(50, 750, 'PdfPageEvidence')
        pdf.showPage()
        pdf.save()
        self.run_cli('ingest', path)
        self.assertEqual(self.run_cli('search', 'PdfPageEvidence')['hits'][0]['locator'], 'page 1')
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        blank = self.root / 'scanned.pdf'
        writer.write(str(blank))
        result = self.run_cli('ingest', blank, ok=False)
        self.assertEqual(result['results'][0]['error_code'], 'no_extractable_text')

    def test_missing_unsupported_and_corrupt_inputs_report_errors(self):
        self.run_cli('init')
        for path in [self.root / 'missing.txt', self.write_text('legacy.xls'), self.write_text('broken.docx')]:
            self.assertEqual(self.run_cli('ingest', path, ok=False)['results'][0]['status'], 'error')
        self.assertEqual(self.run_cli('status')['failed_ingestions'], 3)

    def test_directory_ingestion_and_bounded_results(self):
        folder = self.root / 'reports'
        folder.mkdir()
        for i in range(4):
            (folder / f'{i}.txt').write_text('RepeatedEvidence', encoding='utf-8')
        self.run_cli('ingest', folder)
        self.assertEqual(len(self.run_cli('search', 'RepeatedEvidence', '--limit', '2')['hits']), 2)

    def test_docx_table_paragraph_boundaries_do_not_merge_numbers(self):
        path = self.zip_file('paragraphs.docx', {'word/document.xml': '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:tbl><w:tr><w:tc><w:p><w:r><w:t>12.5</w:t></w:r></w:p><w:p><w:r><w:t>25.0</w:t></w:r></w:p></w:tc></w:tr></w:tbl></w:body></w:document>'})
        self.run_cli('ingest', path)
        hit = self.run_cli('search', '12.5')['hits'][0]
        self.assertEqual(self.run_cli('read', hit['kind'], hit['id'])['text'], '12.5\n25.0')

    def test_xlsx_phonetic_runs_are_not_indexed_as_cell_values(self):
        path = self.zip_file('phonetic.xlsx', {
            'xl/workbook.xml': '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Test" r:id="rId1"/></sheets></workbook>',
            'xl/_rels/workbook.xml.rels': '<Relationships><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>',
            'xl/sharedStrings.xml': '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><si><t>Temperature</t><rPh sb="0" eb="11"><t>PhoneticOnly</t></rPh></si></sst>',
            'xl/worksheets/sheet1.xml': '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="inlineStr"><is><t>Pressure</t><rPh sb="0" eb="8"><t>PhoneticOnly</t></rPh></is></c></row></sheetData></worksheet>',
        })
        self.run_cli('ingest', path)
        self.assertEqual(self.run_cli('search', 'PhoneticOnly')['hits'], [])
        hit = self.run_cli('search', 'Temperature')['hits'][0]
        self.assertEqual(self.run_cli('read', hit['kind'], hit['id'])['details']['cells'][1]['value'], 'Pressure')

    def test_malformed_csv_update_is_rejected_and_previous_version_retained(self):
        path = self.write_text('table.csv', 'Key,Value\nPreservedCsvEvidence,1\n')
        self.run_cli('ingest', path)
        path.write_text('Key,Value\nBad,"unclosed\nOther,2\n', encoding='utf-8')
        self.run_cli('ingest', path, ok=False)
        self.assertEqual(self.run_cli('status')['versions'], 1)
        self.assertTrue(self.run_cli('search', 'PreservedCsvEvidence')['hits'])

    def test_large_details_are_explicitly_omitted_from_bounded_reads(self):
        path = self.write_text('large.csv', 'Key,Value\nLargeEvidence,' + 'x' * 30000 + '\n')
        self.run_cli('ingest', path)
        hit = self.run_cli('search', 'LargeEvidence')['hits'][0]
        read = self.run_cli('read', hit['kind'], hit['id'], '--max-chars', '100')
        self.assertLess(len(json.dumps(read)), 2000)
        self.assertTrue(read['details_omitted'])
        self.assertIsNone(read['details'])

    def test_fts_and_substring_hits_are_combined_when_below_limit(self):
        self.run_cli('ingest', self.write_text(text='Thermal\nThermalEvidence\n'))
        hits = self.run_cli('search', 'Thermal')['hits']
        self.assertEqual(len(hits), 2)
        self.assertEqual(len({h['id'] for h in hits}), 2)

    def test_existing_schema_and_fan_evidence_are_preserved_with_backup(self):
        source = self.write_text('old.xlsx', 'synthetic legacy original')
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        with closing(sqlite3.connect(self.db)) as c:
            c.executescript('''
                CREATE TABLE reports(id INTEGER PRIMARY KEY,source_path TEXT,sha256 TEXT,size_bytes INTEGER,date_system TEXT,imported_at_utc TEXT);
                CREATE TABLE sheets(id INTEGER PRIMARY KEY,report_id INTEGER,name TEXT);
                CREATE TABLE cells(id INTEGER PRIMARY KEY,sheet_id INTEGER,address TEXT,text_value TEXT,raw_value TEXT,numeric_value REAL,formula TEXT);
                CREATE VIRTUAL TABLE cell_search USING fts5(text_value);
                CREATE TABLE fan_noise_measurements(dataset TEXT,source TEXT,fan_speed_rpm INTEGER,noise_dba REAL,airflow_cfm REAL);
            ''')
            c.execute('INSERT INTO reports VALUES(1,?,?,?, ?, ?)', (str(source), digest, source.stat().st_size, '1900', '2026-01-01T00:00:00Z'))
            c.execute("INSERT INTO sheets VALUES(1,1,'Legacy')")
            c.execute("INSERT INTO cells VALUES(1,1,'B2','LegacyEvidence','LegacyEvidence',NULL,NULL)")
            c.execute("INSERT INTO cell_search(rowid,text_value) VALUES(1,'LegacyEvidence')")
            c.execute("INSERT INTO fan_noise_measurements VALUES('SyntheticFan','User-provided table',1000,12.5,2.5)")
            c.commit()
        result = self.run_cli('init')
        backup = Path(result['backup_path'])
        self.assertTrue(backup.exists())
        with closing(sqlite3.connect(backup)) as c:
            self.assertEqual(c.execute('SELECT count(*) FROM cells').fetchone()[0], 1)
            self.assertFalse(c.execute("SELECT name FROM sqlite_master WHERE name='local_sources'").fetchall())
        self.assertEqual(self.run_cli('ingest', source)['results'][0]['status'], 'unchanged')
        hit = self.run_cli('search', 'LegacyEvidence')['hits'][0]
        self.assertEqual(hit['kind'], 'legacy_cell')
        self.assertEqual(hit['locator'], "'Legacy'!B2")
        self.assertEqual(self.run_cli('read', hit['kind'], hit['id'])['text'], 'LegacyEvidence')
        fan = self.run_cli('search', 'SyntheticFan')['hits'][0]
        self.assertEqual(fan['kind'], 'fan_measurement')
        self.assertEqual(fan['source_path'], 'User-provided table')
        self.assertEqual(self.run_cli('read', fan['kind'], fan['id'])['details']['noise_dba'], 12.5)
        self.assertEqual(self.run_cli('status')['legacy_cells'], 1)


if __name__ == '__main__':
    unittest.main()
