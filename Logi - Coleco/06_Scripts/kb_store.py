"""Additive SQLite storage and evidence retrieval for local Coleco reports."""
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import uuid

from local_extract import IngestError, extract
import remote_store

SCHEMA = '''
CREATE TABLE IF NOT EXISTS local_sources(
 id INTEGER PRIMARY KEY, source_key TEXT UNIQUE NOT NULL,
 source_path TEXT NOT NULL, current_version_id INTEGER REFERENCES local_versions(id));
CREATE TABLE IF NOT EXISTS local_versions(
 id INTEGER PRIMARY KEY, source_id INTEGER NOT NULL REFERENCES local_sources(id),
 sha256 TEXT NOT NULL, size_bytes INTEGER NOT NULL, format TEXT NOT NULL,
 imported_at_utc TEXT NOT NULL, source_modified_at_utc TEXT,
 warnings_json TEXT NOT NULL DEFAULT '[]', legacy_report_id INTEGER,
 UNIQUE(source_id,sha256));
CREATE TABLE IF NOT EXISTS local_chunks(
 id INTEGER PRIMARY KEY, version_id INTEGER NOT NULL REFERENCES local_versions(id),
 ordinal INTEGER NOT NULL, locator TEXT NOT NULL, text TEXT NOT NULL,
 details_json TEXT NOT NULL, UNIQUE(version_id,ordinal));
CREATE VIRTUAL TABLE IF NOT EXISTS local_search USING fts5(
 text, content='local_chunks', content_rowid='id');
CREATE TRIGGER IF NOT EXISTS local_chunks_ai AFTER INSERT ON local_chunks BEGIN
 INSERT INTO local_search(rowid,text) VALUES(new.id,new.text); END;
CREATE TRIGGER IF NOT EXISTS local_chunks_ad AFTER DELETE ON local_chunks BEGIN
 INSERT INTO local_search(local_search,rowid,text) VALUES('delete',old.id,old.text); END;
CREATE TRIGGER IF NOT EXISTS local_chunks_au AFTER UPDATE ON local_chunks BEGIN
 INSERT INTO local_search(local_search,rowid,text) VALUES('delete',old.id,old.text);
 INSERT INTO local_search(rowid,text) VALUES(new.id,new.text); END;
CREATE TABLE IF NOT EXISTS local_ingest_events(
 id INTEGER PRIMARY KEY, source_path TEXT NOT NULL, attempted_at_utc TEXT NOT NULL,
 status TEXT NOT NULL, sha256 TEXT, error_code TEXT, message TEXT);
'''


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def source_key(path):
    value = str(Path(path).resolve())
    return value.casefold() if os.name == 'nt' else value


def connect(path, readonly=False):
    path = Path(path).resolve()
    if readonly and not path.is_file():
        raise IngestError('missing_database', 'Database does not exist; run init or ingest first.')
    if not readonly:
        path.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) if readonly else sqlite3.connect(path)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    if readonly:
        c.execute('PRAGMA query_only=ON')
    return c


def has_table(c, name):
    return bool(c.execute('SELECT 1 FROM sqlite_master WHERE name=?', (name,)).fetchone())


def initialize(path, root):
    backup = None
    with closing(connect(path)) as c:
        stage = 'phase2' if not has_table(c, 'local_sources') else 'phase3'
        if (not has_table(c, 'local_sources') or not has_table(c, 'remote_records')) and c.execute("SELECT 1 FROM sqlite_master WHERE type='table' LIMIT 1").fetchone():
            backup_dir = Path(path).resolve().parent / 'backups'
            backup_dir.mkdir(exist_ok=True)
            backup = backup_dir / ('before-' + stage + '-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8] + '.sqlite3')
            with closing(sqlite3.connect(backup)) as destination:
                c.backup(destination)
        c.executescript('BEGIN IMMEDIATE;\n' + SCHEMA + remote_store.SCHEMA)
        with c:
            if has_table(c, 'reports'):
                for report in c.execute('SELECT * FROM reports').fetchall():
                    original = Path(report['source_path'])
                    original = original if original.is_absolute() else Path(root) / original
                    original = original.resolve()
                    key = source_key(original)
                    existing = c.execute('SELECT id FROM local_sources WHERE source_key=?', (key,)).fetchone()
                    if existing:
                        continue
                    sid = c.execute('INSERT INTO local_sources(source_key,source_path) VALUES(?,?)', (key, str(original))).lastrowid
                    vid = c.execute('''INSERT INTO local_versions(source_id,sha256,size_bytes,format,imported_at_utc,warnings_json,legacy_report_id)
                                       VALUES(?,?,?,?,?,?,?)''', (sid, report['sha256'], report['size_bytes'], 'xlsx', report['imported_at_utc'],
                                       json.dumps(['Legacy workbook index: saved values; embedded media remain in the original.']), report['id'])).lastrowid
                    c.execute('UPDATE local_sources SET current_version_id=? WHERE id=?', (vid, sid))
    return {'status': 'ready', 'database': str(Path(path).resolve()), 'backup_path': str(backup) if backup else None}


def event(c, path, status, digest=None, error=None):
    c.execute('''INSERT INTO local_ingest_events(source_path,attempted_at_utc,status,sha256,error_code,message)
                 VALUES(?,?,?,?,?,?)''', (str(path), utc_now(), status, digest, error.code if error else None, str(error) if error else None))


def ingest(c, path):
    path = Path(path).resolve()
    digest = None
    try:
        if not path.is_file():
            raise IngestError('missing_file', 'The input is not an existing file.')
        digest = file_hash(path)
        key = source_key(path)
        source = c.execute('SELECT * FROM local_sources WHERE source_key=?', (key,)).fetchone()
        known = c.execute('SELECT * FROM local_versions WHERE source_id=? AND sha256=?', (source['id'], digest)).fetchone() if source else None
        if known:
            state = 'unchanged' if source['current_version_id'] == known['id'] else 'reused'
            with c:
                c.execute('UPDATE local_sources SET current_version_id=? WHERE id=?', (known['id'], source['id']))
                event(c, path, state, digest)
            return {'source_path': str(path), 'status': state, 'version_id': known['id'], 'sha256': digest,
                    'warnings': json.loads(known['warnings_json'])}
        extracted = extract(path)
        if file_hash(path) != digest:
            raise IngestError('source_changed', 'File changed during extraction; nothing was published. Retry after it is saved.')
        modified = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
        with c:
            sid = source['id'] if source else c.execute('INSERT INTO local_sources(source_key,source_path) VALUES(?,?)', (key, str(path))).lastrowid
            vid = c.execute('''INSERT INTO local_versions(source_id,sha256,size_bytes,format,imported_at_utc,source_modified_at_utc,warnings_json)
                               VALUES(?,?,?,?,?,?,?)''', (sid, digest, path.stat().st_size, path.suffix.lower()[1:], utc_now(), modified,
                               json.dumps(extracted.warnings, ensure_ascii=False))).lastrowid
            c.executemany('INSERT INTO local_chunks(version_id,ordinal,locator,text,details_json) VALUES(?,?,?,?,?)',
                          [(vid, i, chunk.locator, chunk.text, json.dumps(chunk.details, ensure_ascii=False))
                           for i, chunk in enumerate(extracted.chunks, 1)])
            c.execute('UPDATE local_sources SET current_version_id=? WHERE id=?', (vid, sid))
            event(c, path, 'imported', digest)
        return {'source_path': str(path), 'status': 'imported', 'version_id': vid, 'sha256': digest,
                'chunks': len(extracted.chunks), 'warnings': extracted.warnings}
    except IngestError as exc:
        c.rollback()
        with c:
            event(c, path, 'error', digest, exc)
        return {'source_path': str(path), 'status': 'error', 'error_code': exc.code, 'message': str(exc)}
    except OSError:
        c.rollback()
        exc = IngestError('file_access_failed', 'Could not read the local source file.')
        with c:
            event(c, path, 'error', digest, exc)
        return {'source_path': str(path), 'status': 'error', 'error_code': exc.code, 'message': str(exc)}
    except sqlite3.Error:
        c.rollback()
        exc = IngestError('database_write_failed', 'Database write failed; the previous current version was retained.')
        logged = False
        try:
            with c:
                event(c, path, 'error', digest, exc)
            logged = True
        except sqlite3.Error:
            c.rollback()
        return {'source_path': str(path), 'status': 'error', 'error_code': exc.code,
                'message': str(exc), 'error_log_written': logged}


def literal_filter(column, query):
    terms = query.split()
    values = ['%' + term.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%' for term in terms]
    return ' AND '.join(column + " LIKE ? ESCAPE '\\'" for _ in terms), values


CHUNK_SELECT = '''SELECT h.id,h.text,h.locator,h.details_json,v.sha256,v.imported_at_utc,
 v.source_modified_at_utc,v.warnings_json,v.id AS version_id,s.source_path,
 (s.current_version_id=v.id) AS is_current
 FROM local_chunks h JOIN local_versions v ON v.id=h.version_id
 JOIN local_sources s ON s.id=v.source_id'''
LEGACY_SELECT = '''SELECT h.id,h.text_value AS text,h.raw_value,h.numeric_value,h.formula,
 h.address,sh.name AS sheet,v.sha256,v.imported_at_utc,v.source_modified_at_utc,
 v.warnings_json,v.id AS version_id,s.source_path,(s.current_version_id=v.id) AS is_current
 FROM cells h JOIN sheets sh ON sh.id=h.sheet_id
 JOIN local_versions v ON v.legacy_report_id=sh.report_id
 JOIN local_sources s ON s.id=v.source_id'''


def evidence(row, kind, full=False, query=''):
    data = dict(row)
    text = data.pop('text') or data.get('raw_value') or ''
    data['kind'] = kind
    data['is_current'] = bool(data['is_current'])
    data['warnings'] = json.loads(data.pop('warnings_json'))
    data['file_uri'] = Path(data['source_path']).as_uri()
    if kind == 'legacy_cell':
        sheet = data.pop('sheet')
        address = data.pop('address')
        data['locator'] = "'" + sheet.replace("'", "''") + "'!" + address
        details = {key: data.pop(key) for key in ('raw_value', 'numeric_value', 'formula')}
        details.update(sheet=sheet, address=address)
    else:
        details = json.loads(data.pop('details_json'))
    if full:
        data['text'], data['details'] = text, details
    else:
        found = re.search(re.escape(query.split()[0]), text, re.IGNORECASE) if query.split() else None
        start = max(0, found.start() - 80) if found else 0
        data['snippet_start'] = start
        data['snippet'] = text[start:start + 320]
        data['snippet_truncated'] = len(text) > 320
    return data


def fan_evidence(row, full=False):
    row = dict(row)
    rid = row.pop('id')
    text = f"{row['dataset']}: fan_speed_rpm={row['fan_speed_rpm']}; noise_dba={row['noise_dba']}; airflow_cfm={row['airflow_cfm']}"
    result = {'kind': 'fan_measurement', 'id': rid, 'source_path': row['source'], 'source_type': 'user_provided',
              'locator': f"{row['dataset']}, RPM={row['fan_speed_rpm']}", 'sha256': None,
              'imported_at_utc': None, 'is_current': True, 'warnings': ['User-provided table; not attributed to the workbook.']}
    if full:
        result.update(text=text, details=row)
    else:
        result['snippet'] = text
    return result


def search(c, query, limit=5):
    if not query.strip() or len(query) > 256 or not 1 <= limit <= 20:
        raise IngestError('invalid_query', 'Use a nonempty query up to 256 characters and a limit from 1 to 20.')
    match = ' AND '.join('"' + term.replace('"', '""') + '"' for term in query.split())
    hits = []
    if has_table(c, 'fan_noise_measurements'):
        rows = c.execute('SELECT rowid AS id,* FROM fan_noise_measurements').fetchall()
        for row in rows:
            hit = fan_evidence(row)
            if all(term.casefold() in (hit['snippet'] + ' ' + hit['source_path']).casefold() for term in query.split()):
                hits.append(hit)
    if has_table(c, 'local_search'):
        try:
            rows = c.execute(CHUNK_SELECT + ''' JOIN local_search f ON f.rowid=h.id
                WHERE local_search MATCH ? AND s.current_version_id=v.id ORDER BY bm25(local_search),h.id LIMIT ?''', (match, limit)).fetchall()
        except sqlite3.OperationalError:
            rows = []
        if len(rows) < limit:
            condition, params = literal_filter('h.text', query)
            fallback = c.execute(CHUNK_SELECT + ' WHERE s.current_version_id=v.id AND ' + condition + ' ORDER BY h.id LIMIT ?', (*params, limit)).fetchall()
            seen = {row['id'] for row in rows}
            rows.extend(row for row in fallback if row['id'] not in seen)
        hits.extend(evidence(row, 'chunk', query=query) for row in rows[:limit])
    if has_table(c, 'cells') and has_table(c, 'local_versions'):
        rows = []
        if has_table(c, 'cell_search'):
            try:
                rows = c.execute(LEGACY_SELECT + ''' JOIN cell_search f ON f.rowid=h.id
                    WHERE cell_search MATCH ? AND s.current_version_id=v.id ORDER BY bm25(cell_search),h.id LIMIT ?''', (match, limit)).fetchall()
            except sqlite3.OperationalError:
                rows = []
        if len(rows) < limit:
            condition, params = literal_filter("coalesce(h.text_value,h.raw_value,'')", query)
            fallback = c.execute(LEGACY_SELECT + ' WHERE s.current_version_id=v.id AND ' + condition + ' ORDER BY h.id LIMIT ?', (*params, limit)).fetchall()
            seen = {row['id'] for row in rows}
            rows.extend(row for row in fallback if row['id'] not in seen)
        hits.extend(evidence(row, 'legacy_cell', query=query) for row in rows[:limit])
    hits.extend(remote_store.search_remote(c, query, limit))
    return {'query': query, 'limit': limit, 'hits': hits[:limit], 'scope': 'current indexed local/remote versions; no live MCP search'}


def read(c, kind, rid, max_chars=8000, offset=0):
    if kind == 'remote':
        return remote_store.read_remote(c, rid, max_chars, offset)
    if not 1 <= max_chars <= 20000 or offset < 0:
        raise IngestError('invalid_read', 'max-chars must be from 1 to 20000; offset must be nonnegative.')
    result = None
    if kind == 'chunk' and has_table(c, 'local_chunks'):
        row = c.execute(CHUNK_SELECT + ' WHERE h.id=?', (rid,)).fetchone()
        result = evidence(row, kind, True) if row else None
    elif kind == 'legacy_cell' and has_table(c, 'cells'):
        row = c.execute(LEGACY_SELECT + ' WHERE h.id=? ORDER BY v.id LIMIT 1', (rid,)).fetchone()
        result = evidence(row, kind, True) if row else None
    elif kind == 'fan_measurement' and has_table(c, 'fan_noise_measurements'):
        row = c.execute('SELECT rowid AS id,* FROM fan_noise_measurements WHERE rowid=?', (rid,)).fetchone()
        result = fan_evidence(row, True) if row else None
    if result is None:
        raise IngestError('missing_evidence', 'No evidence with this kind and id exists.')
    if offset > len(result['text']):
        raise IngestError('invalid_read', 'Offset is beyond the stored evidence text.')
    result['text_truncated'] = offset > 0 or len(result['text']) > offset + max_chars
    result['text'] = result['text'][offset:offset + max_chars]
    result['offset'] = offset
    result['details_omitted'] = len(json.dumps(result['details'], ensure_ascii=False)) > max_chars
    if result['details_omitted']:
        result['details'] = None
    return result


def status(c):
    def count(table):
        return c.execute('SELECT count(*) FROM ' + table).fetchone()[0] if has_table(c, table) else 0
    return {'integrity': c.execute('PRAGMA quick_check').fetchone()[0],
            'foreign_key_errors': len(c.execute('PRAGMA foreign_key_check').fetchall()),
            'sources': count('local_sources'), 'versions': count('local_versions'),
            'chunks': count('local_chunks'), 'legacy_reports': count('reports'),
            'legacy_cells': count('cells'), 'fan_measurements': count('fan_noise_measurements'),
            'failed_ingestions': c.execute("SELECT count(*) FROM local_ingest_events WHERE status='error'").fetchone()[0] if has_table(c, 'local_ingest_events') else 0,
            'remote_sync': remote_store.sync_status(c), 'scheduler': 'not configured'}
