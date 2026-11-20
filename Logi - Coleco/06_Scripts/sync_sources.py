"""Small, resumable five-source collection through existing read-only MCP tools."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import closing
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re

from local_extract import IngestError
from mcp_stdio import McpClient, McpFailure, COMPONENTS
import remote_store
from source_adapters import candidate_id, date, discover, hydrate, recheck


def validate_config(config):
    providers = config.get('providers', {})
    if not providers or not set(providers) <= set(COMPONENTS):
        raise IngestError('invalid_sync_config', 'Configure at least one supported provider.')
    defaults = {'lookback_days': 30, 'per_source_limit': 2, 'overlap_hours': 24, 'timeout_seconds': 40}
    result = defaults | config
    bounds = {'lookback_days': (1, 36500), 'per_source_limit': (1, 2), 'overlap_hours': (1, 168), 'timeout_seconds': (1, 60)}
    for field, (low, high) in bounds.items():
        if not isinstance(result[field], int) or not low <= result[field] <= high:
            raise IngestError('invalid_sync_config', 'Invalid bounded sync setting: ' + field)
    for provider, scope in providers.items():
        if not isinstance(scope, dict): raise IngestError('invalid_sync_config', 'Provider scope must be an object.')
        if provider == 'jira':
            if not scope.get('cloud_id') or not scope.get('site_url', '').startswith('https://') or not scope.get('project_keys'):
                raise IngestError('invalid_sync_config', 'Jira needs a verified cloud, site and project keys.')
            if not all(re.fullmatch(r'[A-Z][A-Z0-9_]*', k) for k in scope['project_keys']):
                raise IngestError('invalid_sync_config', 'Invalid Jira project key.')
        elif provider == 'gmail' and not isinstance(scope.get('query'), str):
            raise IngestError('invalid_sync_config', 'Gmail requires a search query.')
        elif provider == 'drive' and not scope.get('title_keyword'):
            raise IngestError('invalid_sync_config', 'Drive requires a project title keyword.')
        elif provider == 'chat' and not re.fullmatch(r'spaces/[A-Za-z0-9_-]+', scope.get('conversation_id', '')):
            raise IngestError('invalid_sync_config', 'Chat requires a verified space ID.')
        elif provider == 'slack':
            if scope.get('public_only') is not True or not scope.get('channel_ids'):
                raise IngestError('invalid_sync_config', 'Only explicitly configured public Slack channels are supported.')
            if not all(re.fullmatch(r'C[A-Z0-9]+', k) for k in scope['channel_ids']):
                raise IngestError('invalid_sync_config', 'Invalid public Slack channel ID.')
    return result


def scope_key(provider, scope):
    return hashlib.sha256(json.dumps([provider, scope], sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def prepare_checkpoint(cp, config, end=None):
    end = end or datetime.now(timezone.utc)
    if cp and not cp['complete']:
        return deepcopy(cp)
    start = date(cp['watermark']) - timedelta(hours=config['overlap_hours']) if cp and cp.get('watermark') else end - timedelta(days=config['lookback_days'])
    if start >= end:
        raise IngestError('invalid_sync_window', 'Sync window must have increasing UTC times.')
    return {'generation': cp['generation'] if cp else 0,
            'window_start': start.isoformat().replace('+00:00', 'Z'),
            'window_end': end.isoformat().replace('+00:00', 'Z'),
            'cursor': {'page_token': None, 'pending': [], 'exhausted': False},
            'complete': False, 'watermark': cp.get('watermark') if cp else None}


def collect_provider(client, provider, scope, checkpoint, limit, known):
    state = deepcopy(checkpoint)
    cursor = state['cursor']
    cursor.setdefault('pending', [])
    cursor.setdefault('page_token', None)
    cursor.setdefault('exhausted', False)
    cursor.setdefault('policy_omissions', {})
    cursor.setdefault('page_size', limit)
    observations, errors, processed = [], [], set()
    new_budget = max(1, limit - 1) if known and limit > 1 else limit
    try:
        if not cursor['pending'] and not cursor['exhausted']:
            page = discover(client, provider, scope, state['window_start'], state['window_end'], cursor['page_size'], cursor['page_token'])
            if page['next_token'] and page['next_token'] == cursor['page_token']:
                raise McpFailure('repeated_page_token')
            cursor['pending'] = page['items']
            cursor['page_token'] = page['next_token']
            cursor['exhausted'] = not bool(page['next_token'])
            for reason, count in page.get('policy_omissions', {}).items():
                # Page overlap can repeat filtered items; max is a conservative lower bound.
                cursor['policy_omissions'][reason] = max(cursor['policy_omissions'].get(reason, 0), count)
        for _ in range(new_budget):
            if not cursor['pending']: break
            item = cursor['pending'][0]
            rid = candidate_id(provider, scope, item)
            try:
                observations.append(hydrate(client, provider, scope, item))
                processed.add(rid)
                cursor['pending'].pop(0)
            except McpFailure as exc:
                errors.append({'code': exc.code, 'remote_id': rid})
                break
        if not errors and len(observations) < limit:
            for old in known:
                if old['remote_id'] in processed: continue
                try:
                    observations.append(recheck(client, provider, scope, old))
                except McpFailure as exc:
                    errors.append({'code': exc.code, 'remote_id': old['remote_id']})
                break
    except McpFailure as exc:
        errors.append({'code': exc.code})
    except (KeyError, TypeError, ValueError, AttributeError):
        errors.append({'code': 'invalid_source_response'})
    state['complete'] = cursor['exhausted'] and not cursor['pending']
    return {'observations': observations, 'state': state, 'errors': errors}


def run_sync(db, root, config_path, sources=None):
    from kb_store import initialize, connect
    try:
        config = validate_config(json.loads(Path(config_path).read_text(encoding='utf-8-sig')))
    except OSError as exc:
        raise IngestError('missing_sync_config', 'Create the private local source configuration from the example first.') from exc
    except (ValueError, AttributeError) as exc:
        raise IngestError('invalid_sync_config', 'Sync configuration must contain valid JSON.') from exc
    if sources and not set(sources) <= set(config['providers']):
        raise IngestError('invalid_sync_config', 'Requested provider is not configured.')
    initialized = initialize(db, root)
    jobs = {}
    end = datetime.now(timezone.utc)
    with closing(connect(db, readonly=True)) as c:
        for provider, scope in config['providers'].items():
            if sources and provider not in sources: continue
            key = scope_key(provider, scope)
            cp = prepare_checkpoint(remote_store.checkpoint(c, provider, key), config, end)
            old = remote_store.recheck_candidates(c, provider, 3, key)
            jobs[provider] = (scope, key, cp, old)

    def collect(provider):
        scope, _, cp, old = jobs[provider]
        try:
            with McpClient(provider, config['timeout_seconds']) as client:
                return collect_provider(client, provider, scope, cp, config['per_source_limit'], old)
        except McpFailure as exc:
            return {'observations': [], 'state': cp, 'errors': [{'code': exc.code}]}

    results = []
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        futures = {pool.submit(collect, provider): provider for provider in jobs}
        with closing(connect(db)) as c:
            for future in as_completed(futures):
                provider = futures[future]
                batch = future.result()
                _, key, cp, _ = jobs[provider]
                results.append(remote_store.apply_batch(c, provider, key, cp['generation'],
                               batch['observations'], batch['state'], batch['errors']))
    return {'status': 'partial' if any(r['status'] != 'complete' for r in results) else 'complete',
            'sources': sorted(results, key=lambda r: r['provider']), 'backup_path': initialized['backup_path'],
            'max_detailed_records': config['per_source_limit'] * len(jobs), 'scheduler': 'not configured'}
