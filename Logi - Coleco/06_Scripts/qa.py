"""Bounded extractive answers with exact citations and indexed-source coverage."""
from datetime import datetime
import re

from kb_store import read, search, utc_now
from local_extract import IngestError
import remote_store

TOPICS = (
    (('thermal', 'temperature', '熱', '溫度', '環溫'), ('thermal', 'temperature', 'DTS')),
    (('fan', '風扇', '轉速', 'rpm'), ('fan', 'RPM')),
    (('noise', 'acoustic', '噪音', '聲學'), ('noise', 'dBA')),
    (('policy', '策略', '政策'), ('policy', 'fan')),
    (('burn', 'burn-in', '燒機', '老化'), ('Burn Out', 'burn-in')),
    (('power', '功耗', '功率', '電力'), ('power', 'SoM')),
    (('throttl', '降頻'), ('throttling',)),
    (('cpu', 'dts', '感測器'), ('CPU', 'DTS')),
)
STOP_WORDS = {'what', 'which', 'is', 'are', 'the', 'a', 'an', 'of', 'for', 'and',
              'with', 'in', 'to', 'about', 'latest', 'current', 'coleco', 'does', 'how'}


def citation(evidence, citation_id):
    """Preserve source and version identity without attributing unknown dates."""
    return {'citation_id': citation_id, 'kind': evidence['kind'], 'id': evidence['id'],
            'version_id': evidence.get('version_id'), 'sha256': evidence.get('sha256'),
            'title': evidence.get('title'), 'provider': evidence.get('provider'),
            'remote_id': evidence.get('remote_id'), 'source_path': evidence.get('source_path'),
            'source_url': evidence.get('source_url'), 'file_uri': evidence.get('file_uri'),
            'locator': evidence.get('locator'), 'is_current': evidence.get('is_current'),
            'availability': evidence.get('availability', 'indexed_local'),
            'source_created_at_utc': evidence.get('source_created_at_utc'),
            'source_updated_at_utc': evidence.get('source_updated_at_utc', evidence.get('source_modified_at_utc')),
            'observed_at_utc': evidence.get('observed_at_utc', evidence.get('imported_at_utc')),
            'last_verified_at_utc': evidence.get('last_verified_at_utc'),
            'revision_tag': evidence.get('revision_tag'),
            'completeness': evidence.get('completeness', 'indexed_text'),
            'warnings': evidence.get('warnings', []),
            'original_file_verified': False if evidence['kind'] in ('chunk', 'legacy_cell') else None}


def coverage(c):
    state = remote_store.sync_status(c)
    present = {cp['provider'] for cp in state['checkpoints']}
    return {'live_checked': False, 'checkpoints': state['checkpoints'],
            'unavailable_records': state.get('unavailable', 0),
            'providers_without_checkpoint': sorted(remote_store.PROVIDERS - present),
            'scope': 'Current indexed versions within configured scopes at the recorded observation times.',
            'limitations': [
                'Provider-visible completion excludes policy-filtered results and omitted attachments/objects.',
                'Email/chat/Slack discovery primarily uses creation time; older changes rely on bounded rechecks.',
                'A current index version does not verify a local original or a live remote source.',
            ]}


def retrieval_queries(question, explicit):
    if explicit:
        if len(explicit) > 8 or any(not q.strip() or len(q) > 256 for q in explicit):
            raise IngestError('invalid_ask', 'Use at most eight nonempty search queries up to 256 characters each.')
        return list(dict.fromkeys(q.strip() for q in explicit))
    candidates = [question.strip()] if len(question.strip()) <= 256 else []
    lower = question.casefold()
    for triggers, queries in TOPICS:
        if any(term in lower for term in triggers):
            candidates.extend(queries)
    words = [word for word in re.findall(r'[a-zA-Z0-9][a-zA-Z0-9_-]*', lower)
             if word not in STOP_WORDS and len(word) > 1]
    candidates.extend(words)
    return list(dict.fromkeys(candidates))[:8]


def source_time(hit):
    stamp = hit.get('source_updated_at_utc') or hit.get('source_modified_at_utc') or hit.get('source_created_at_utc')
    try:
        parsed = datetime.fromisoformat(stamp.replace('Z', '+00:00')) if stamp else None
        return parsed.timestamp() if parsed and parsed.tzinfo else 0
    except (ValueError, OverflowError):
        return 0


def ask(c, question, limit=6, max_chars=1500, queries=None):
    if not question.strip() or len(question) > 512 or not 1 <= limit <= 12 or not 1 <= max_chars <= 4000:
        raise IngestError('invalid_ask', 'Use a question up to 512 characters, limit 1–12 and max-chars 1–4000.')
    plan = retrieval_queries(question, queries)
    candidates = {}
    for query in plan:
        # Independent remote retrieval keeps many workbook cells from hiding remote evidence.
        hits = search(c, query, 20)['hits'] + remote_store.search_remote(c, query, 20)
        for position, hit in enumerate(hits):
            key = (hit['kind'], hit['id'])
            entry = candidates.setdefault(key, {'hit': hit, 'queries': set(), 'position': position})
            entry['queries'].add(query)
    ranked = sorted(candidates.values(), key=lambda entry: (
        -sum(len(q.split()) for q in entry['queries']), -source_time(entry['hit']),
        entry['position'], entry['hit']['kind'], entry['hit']['id']))
    selected = ranked[:limit]
    if limit > 1 and selected:
        selected_remote = {item['hit']['kind'] == 'remote' for item in selected}
        if len(selected_remote) == 1:
            alternate = next((item for item in ranked if
                              (item['hit']['kind'] == 'remote') not in selected_remote), None)
            if alternate:
                selected = selected[:limit - 1] + [alternate]
    statements, citations = [], []
    for item in selected:
        hit = item['hit']
        evidence = read(c, hit['kind'], hit['id'], max_chars, hit.get('snippet_start', 0))
        if not evidence['is_current'] or evidence.get('availability', 'active') != 'active':
            continue
        cid = 'E' + str(len(citations) + 1)
        citations.append(citation(evidence, cid))
        statements.append({'text': evidence['text'], 'citation_id': cid,
                           'classification': 'source_statement', 'untrusted_source_text': True,
                           'offset': evidence['offset'], 'text_truncated': evidence['text_truncated']})
    lower = question.casefold()
    policy_question = any(term in lower for term in ('policy', '策略', '政策'))
    policy_topic = '風扇' if any(term in lower for term in ('fan', '風扇')) else '此問題涉及的'
    questions = ['引用的負載、樣品、硬體／韌體、環溫及感測器位置是否足以支持這個問題的結論？',
                 '不同來源的陳述是否互相衝突，或需要讀取截斷處與原始附件？']
    if policy_question:
        questions.insert(0, '最新正式' + policy_topic + '政策的核准版本、發布日期與適用硬體／韌體為何？')
    if not citations:
        questions.insert(0, '目前查詢未找到可引用證據；需要哪些來源或更精確的搜尋詞？')
    return {'question': question, 'status': 'evidence_found' if citations else 'insufficient_evidence',
            'answer_mode': 'extractive', 'generated_at_utc': utc_now(), 'queries': plan,
            'source_statements': statements, 'citations': citations,
            'interpretation': ['回答列出來源原文與引用；工程判讀需要核對量測條件、來源權威性與日期。'],
            'open_questions': questions,
            'recommended_actions': ['使用 read KIND ID 讀取引用上下文，依問答模板完成逐項工程判讀。'],
            'policy_confirmation': 'requires_authoritative_source_review' if policy_question else 'not_assessed',
            'conflict_review': 'required', 'coverage': coverage(c)}
