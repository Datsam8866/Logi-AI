"""Versioned remote evidence, availability, checkpoint and sync-run persistence."""
from datetime import datetime, timezone
import hashlib
import json
import re

from local_extract import IngestError

SCHEMA = '''
CREATE TABLE IF NOT EXISTS remote_records(
 id INTEGER PRIMARY KEY,provider TEXT NOT NULL,remote_id TEXT NOT NULL,
 current_version_id INTEGER REFERENCES remote_versions(id),availability TEXT NOT NULL,
 last_verified_at_utc TEXT NOT NULL,UNIQUE(provider,remote_id));
CREATE TABLE IF NOT EXISTS remote_versions(
 id INTEGER PRIMARY KEY,record_id INTEGER NOT NULL REFERENCES remote_records(id),
 revision_tag TEXT NOT NULL,content_hash TEXT NOT NULL,title TEXT NOT NULL,text TEXT NOT NULL,
 source_url TEXT,source_created_at_utc TEXT,source_updated_at_utc TEXT,
 observed_at_utc TEXT NOT NULL,completeness TEXT NOT NULL,metadata_json TEXT NOT NULL,
 UNIQUE(record_id,revision_tag,content_hash));
CREATE VIRTUAL TABLE IF NOT EXISTS remote_search USING fts5(
 title,text,content='remote_versions',content_rowid='id');
CREATE TRIGGER IF NOT EXISTS remote_versions_ai AFTER INSERT ON remote_versions BEGIN
 INSERT INTO remote_search(rowid,title,text) VALUES(new.id,new.title,new.text);END;
CREATE TABLE IF NOT EXISTS remote_memberships(
 record_id INTEGER NOT NULL REFERENCES remote_records(id),scope_key TEXT NOT NULL,
 PRIMARY KEY(record_id,scope_key));
CREATE TABLE IF NOT EXISTS sync_checkpoints(
 provider TEXT NOT NULL,scope_key TEXT NOT NULL,generation INTEGER NOT NULL,
 window_start TEXT NOT NULL,window_end TEXT NOT NULL,cursor_json TEXT NOT NULL,
 complete INTEGER NOT NULL,watermark TEXT,updated_at_utc TEXT NOT NULL,
 PRIMARY KEY(provider,scope_key));
CREATE TABLE IF NOT EXISTS sync_runs(
 id INTEGER PRIMARY KEY,provider TEXT NOT NULL,scope_key TEXT NOT NULL,
 finished_at_utc TEXT NOT NULL,status TEXT NOT NULL,window_start TEXT NOT NULL,
 window_end TEXT NOT NULL,created INTEGER NOT NULL,updated INTEGER NOT NULL,
 unchanged INTEGER NOT NULL,errors_json TEXT NOT NULL);
'''
PROVIDERS = {'jira', 'gmail', 'drive', 'chat', 'slack'}
STATES = {'active', 'deleted', 'inaccessible', 'unverified'}


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


def exists(c, table):
    return bool(c.execute('SELECT 1 FROM sqlite_master WHERE name=?', (table,)).fetchone())


def upsert(c, item):
    if item.get('provider') not in PROVIDERS or item.get('state', 'active') not in STATES:
        raise IngestError('invalid_remote_record', 'Unknown remote provider or availability state.')
    if not isinstance(item.get('remote_id'), str) or not 1 <= len(item['remote_id']) <= 512:
        raise IngestError('invalid_remote_record', 'Remote record requires a stable source ID.')
    text, title = item.get('text', ''), item.get('title', '')
    if not isinstance(text, str) or not isinstance(title, str):
        raise IngestError('invalid_remote_record', 'Remote title and evidence text must be strings.')
    metadata = json.dumps(item.get('metadata', {}), ensure_ascii=False, sort_keys=True)
    revision = item.get('revision_tag') or ''
    digest = hashlib.sha256(json.dumps([title, text, metadata, item.get('state', 'active'),
                                       item.get('completeness', 'full'), item.get('source_url')], ensure_ascii=False).encode()).hexdigest()
    record = c.execute('SELECT * FROM remote_records WHERE provider=? AND remote_id=?', (item['provider'], item['remote_id'])).fetchone()
    if record and item.get('source_updated_at_utc'):
        previous = c.execute('SELECT source_updated_at_utc FROM remote_versions WHERE id=?', (record['current_version_id'],)).fetchone()
        if previous and previous[0] and datetime.fromisoformat(item['source_updated_at_utc'].replace('Z', '+00:00')) < datetime.fromisoformat(previous[0].replace('Z', '+00:00')):
            return {'status': 'outdated', 'version_id': record['current_version_id'], 'record_id': record['id'],
                    'provider': item['provider'], 'remote_id': item['remote_id']}
    rid = record['id'] if record else c.execute('''INSERT INTO remote_records(provider,remote_id,availability,last_verified_at_utc)
                 VALUES(?,?,?,?)''', (item['provider'], item['remote_id'], item.get('state', 'active'), now())).lastrowid
    known = c.execute('SELECT id FROM remote_versions WHERE record_id=? AND revision_tag=? AND content_hash=?', (rid, revision, digest)).fetchone()
    if known:
        vid = known['id']
        state = 'unchanged' if record and record['current_version_id'] == vid else 'reused'
    else:
        vid = c.execute('''INSERT INTO remote_versions(record_id,revision_tag,content_hash,title,text,source_url,
                          source_created_at_utc,source_updated_at_utc,observed_at_utc,completeness,metadata_json)
                          VALUES(?,?,?,?,?,?,?,?,?,?,?)''', (rid, revision, digest, title, text, item.get('source_url'),
                          item.get('source_created_at_utc'), item.get('source_updated_at_utc'), now(),
                          item.get('completeness', 'full'), metadata)).lastrowid
        state = 'updated' if record else 'created'
    c.execute('UPDATE remote_records SET current_version_id=?,availability=?,last_verified_at_utc=? WHERE id=?',
              (vid, item.get('state', 'active'), now(), rid))
    return {'status': state, 'version_id': vid, 'record_id': rid, 'provider': item['provider'], 'remote_id': item['remote_id']}


def mark_unavailable(c, provider, remote_id, availability):
    if availability not in STATES - {'active'}:
        raise IngestError('invalid_availability', 'Unknown unavailable state.')
    c.execute('UPDATE remote_records SET availability=?,last_verified_at_utc=? WHERE provider=? AND remote_id=?',
              (availability, now(), provider, remote_id))


def checkpoint(c, provider, key):
    if not exists(c, 'sync_checkpoints'):
        return None
    row = c.execute('SELECT * FROM sync_checkpoints WHERE provider=? AND scope_key=?', (provider, key)).fetchone()
    if not row:
        return None
    result = dict(row)
    result['cursor'] = json.loads(result.pop('cursor_json'))
    result['complete'] = bool(result['complete'])
    return result


def apply_batch(c, provider, key, generation, observations, state, errors):
    if not c.in_transaction:
        c.execute('BEGIN IMMEDIATE')
    with c:
        current = checkpoint(c, provider, key)
        if (current['generation'] if current else 0) != generation:
            raise IngestError('stale_checkpoint', 'Another run advanced this checkpoint; collected results were not published.')
        saved = [upsert(c, item) for item in observations]
        c.executemany('INSERT OR IGNORE INTO remote_memberships VALUES(?,?)', [(item['record_id'], key) for item in saved])
        safe_errors = [{'code': e.get('code', 'unknown_error'), 'remote_id': e.get('remote_id')}
                       for e in errors]
        for error in safe_errors:
            if error['remote_id'] and error['code'] != 'out_of_scope':
                unavailable = 'inaccessible' if error['code'] in ('permission_denied', 'not_found', 'authentication_required') else 'unverified'
                mark_unavailable(c, provider, error['remote_id'], unavailable)
        watermark = state['window_end'] if state['complete'] else state.get('watermark')
        c.execute('''INSERT INTO sync_checkpoints VALUES(?,?,?,?,?,?,?,?,?)
                     ON CONFLICT(provider,scope_key) DO UPDATE SET generation=excluded.generation,
                     window_start=excluded.window_start,window_end=excluded.window_end,cursor_json=excluded.cursor_json,
                     complete=excluded.complete,watermark=excluded.watermark,updated_at_utc=excluded.updated_at_utc''',
                  (provider, key, generation + 1, state['window_start'], state['window_end'],
                   json.dumps(state['cursor'], ensure_ascii=False), int(state['complete']), watermark, now()))
        counts = {name: sum(item['status'] == name for item in saved) for name in ('created', 'updated', 'unchanged', 'reused', 'outdated')}
        status = 'complete' if state['complete'] and not errors else 'partial' if observations or not errors else 'error'
        c.execute('''INSERT INTO sync_runs(provider,scope_key,finished_at_utc,status,window_start,window_end,created,updated,unchanged,errors_json)
                     VALUES(?,?,?,?,?,?,?,?,?,?)''', (provider, key, now(), status, state['window_start'], state['window_end'],
                     counts['created'], counts['updated'], counts['unchanged'] + counts['reused'] + counts['outdated'], json.dumps(safe_errors)))
    return {'provider': provider, 'status': status, **counts, 'errors': safe_errors,
            'window_complete': state['complete'], 'pending_records': len(state['cursor'].get('pending', [])),
            'has_next_page': bool(state['cursor'].get('page_token')), 'watermark': watermark,
            'coverage': 'partial_policy' if state['cursor'].get('policy_omissions') else 'provider_visible',
            'policy_omissions_lower_bound': state['cursor'].get('policy_omissions', {}),
            'coverage_note': 'Provider security filters may exclude items even without omission counts; content projections are partial.'}


SELECT = '''SELECT v.*,r.provider,r.remote_id,r.availability,r.last_verified_at_utc,
 (r.current_version_id=v.id AND r.availability='active') AS is_current
 FROM remote_versions v JOIN remote_records r ON r.id=v.record_id'''


def remote_evidence(row, query=None):
    d = dict(row)
    metadata = json.loads(d.pop('metadata_json'))
    d.pop('record_id', None)
    d['kind'] = 'remote'
    d['version_id'] = d['id']
    d['is_current'] = bool(d['is_current'])
    d['version_basis'] = 'source_revision' if d['revision_tag'] else 'observed_content'
    d['source_path'] = d['source_url'] or d['provider'] + ':' + d['remote_id']
    d['locator'] = d['remote_id']
    d['sha256'] = d.pop('content_hash')
    if query is not None:
        text = d.pop('text')
        match = re.search(re.escape(query.split()[0]), text, re.IGNORECASE)
        start = max(0, match.start() - 80) if match else 0
        d.update(snippet=text[start:start + 320], snippet_start=start, snippet_truncated=len(text) > 320)
    else:
        d['details'] = metadata
    return d


def search_remote(c, query, limit=5):
    if not exists(c, 'remote_records'):
        return []
    expression = ' AND '.join('"' + term.replace('"', '""') + '"' for term in query.split())
    try:
        rows = c.execute(SELECT + ''' JOIN remote_search f ON f.rowid=v.id
              WHERE remote_search MATCH ? AND r.current_version_id=v.id AND r.availability='active'
              ORDER BY bm25(remote_search),v.id LIMIT ?''', (expression, limit)).fetchall()
    except Exception:
        rows = []
    if len(rows) < limit:
        patterns = ['%' + term.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%' for term in query.split()]
        clause = ' AND '.join("(v.title || ' ' || v.text) LIKE ? ESCAPE '\\'" for _ in patterns)
        extra = c.execute(SELECT + " WHERE r.current_version_id=v.id AND r.availability='active' AND " + clause + ' ORDER BY v.id LIMIT ?', (*patterns, limit)).fetchall()
        seen = {r['id'] for r in rows}
        rows.extend(r for r in extra if r['id'] not in seen)
    return [remote_evidence(row, query) for row in rows[:limit]]


def read_remote(c, vid, max_chars=8000, offset=0):
    if not 1 <= max_chars <= 20000 or offset < 0:
        raise IngestError('invalid_read', 'Invalid remote read bounds.')
    row = c.execute(SELECT + ' WHERE v.id=?', (vid,)).fetchone() if exists(c, 'remote_versions') else None
    if not row:
        raise IngestError('missing_evidence', 'No remote version with this id exists.')
    result = remote_evidence(row)
    if offset > len(result['text']):
        raise IngestError('invalid_read', 'Offset exceeds the stored remote text.')
    result['text_truncated'] = offset > 0 or len(result['text']) > offset + max_chars
    result['text'] = result['text'][offset:offset + max_chars]
    result['offset'] = offset
    result['details_omitted'] = len(json.dumps(result['details'], ensure_ascii=False)) > max_chars
    if result['details_omitted']:
        result['details'] = None
    return result


def recheck_candidates(c, provider, limit=1, scope_key=None):
    if not exists(c, 'remote_records'):
        return []
    clause = ' AND EXISTS(SELECT 1 FROM remote_memberships m WHERE m.record_id=r.id AND m.scope_key=?)' if scope_key else ''
    params = (provider, scope_key, limit) if scope_key else (provider, limit)
    rows = c.execute(SELECT + ' WHERE r.provider=? AND r.current_version_id=v.id' + clause +
           ' ORDER BY r.last_verified_at_utc,r.id LIMIT ?', params).fetchall()
    return [{'remote_id': row['remote_id'], 'metadata': json.loads(row['metadata_json']),
             'source_created_at_utc': row['source_created_at_utc'], 'source_url': row['source_url']}
            for row in rows]


def sync_status(c):
    if not exists(c, 'remote_records'):
        return {'state': 'not initialized', 'records': 0, 'versions': 0, 'checkpoints': []}
    checkpoints = [checkpoint(c, row['provider'], row['scope_key'])
                   for row in c.execute('SELECT provider,scope_key FROM sync_checkpoints ORDER BY provider')]
    compact = [{k: cp[k] for k in ('provider', 'generation', 'window_start', 'window_end', 'complete', 'watermark', 'updated_at_utc')}
               | {'pending_records': len(cp['cursor'].get('pending', [])), 'has_next_page': bool(cp['cursor'].get('page_token'))}
               | {'policy_omissions_lower_bound': cp['cursor'].get('policy_omissions', {})}
               for cp in checkpoints]
    return {'state': 'manual MCP sync; no scheduler',
            'records': c.execute('SELECT count(*) FROM remote_records').fetchone()[0],
            'versions': c.execute('SELECT count(*) FROM remote_versions').fetchone()[0],
            'unavailable': c.execute("SELECT count(*) FROM remote_records WHERE availability!='active'").fetchone()[0],
            'checkpoints': compact}
