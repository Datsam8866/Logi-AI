"""Five scoped, read-only source adapters. Connector text is data, never instructions."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import re
from urllib.parse import parse_qs, urlsplit

from mcp_stdio import McpFailure


def date(value):
    if value is None:
        return None
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.tzinfo is None:
            raise ValueError()
        return result.astimezone(timezone.utc)
    except (ValueError, AttributeError) as exc:
        raise McpFailure('invalid_source_timestamp') from exc


def iso(value):
    return date(value).isoformat().replace('+00:00', 'Z') if value else None


def epoch_iso(value):
    return datetime.fromtimestamp(float(Decimal(str(value))), timezone.utc).isoformat().replace('+00:00', 'Z')


def in_window(value, start, end):
    if value is None:
        raise McpFailure('missing_source_timestamp')
    return date(start) <= date(value) < date(end)


def require_list(data, name, empty_page=False):
    if empty_page and isinstance(data, dict) and name not in data and set(data) <= {'nextPageToken', 'omittedContent', 'resultCountEstimate'}:
        return []
    if not isinstance(data, dict) or not isinstance(data.get(name), list):
        raise McpFailure('invalid_source_response')
    return data[name]


def query_string(value):
    return value.replace('\\', '\\\\').replace("'", "\\'")


def _cursor(text):
    found = re.search(r'cursor[^\n`"]*[`"]([^`"]+)[`"]', text, re.IGNORECASE)
    if found:
        return found.group(1)
    if re.search(r'next page|more results available', text, re.IGNORECASE) and not re.search(r'no more|end of results', text, re.IGNORECASE):
        raise McpFailure('invalid_pagination_response')
    return None


def parse_slack_search(data):
    text = data.get('results') if isinstance(data, dict) else None
    if not isinstance(text, str):
        raise McpFailure('invalid_source_response')
    items = []
    for block in re.split(r'^### Result \d+ of \d+\s*$', text, flags=re.MULTILINE)[1:]:
        header, separator, body = block.partition('\nText:')
        channel = re.search(r'^Channel:.*?\(ID: ([A-Z0-9]+)\)', header, re.MULTILINE)
        stamp = re.search(r'^Message_ts: ([0-9]+\.[0-9]+)', header, re.MULTILINE)
        link = re.search(r'^Permalink:.*?\((https://[^\s)]+)\)', header, re.MULTILINE)
        if not channel or not stamp or not separator:
            raise McpFailure('invalid_source_response')
        items.append({'channel_id': channel.group(1), 'ts': stamp.group(1),
                      'source_url': link.group(1) if link else None,
                      'thread_ts': parse_qs(urlsplit(link.group(1)).query).get('thread_ts', [None])[0] if link else None,
                      'text': re.sub(r'\n---\s*$', '', body).strip()})
    if not items and not re.search(r'0 results|no results|no messages', text, re.IGNORECASE):
        raise McpFailure('invalid_source_response')
    return {'items': items, 'next_token': _cursor(data.get('pagination_info', ''))}


def parse_slack_read(data):
    text = data.get('messages') if isinstance(data, dict) else None
    if not isinstance(text, str):
        raise McpFailure('invalid_source_response')
    result = []
    matches = list(re.finditer(r'^Message TS: ([0-9]+\.[0-9]+)[ \t]*\r?\n', text, re.MULTILINE))
    for number, match in enumerate(matches):
        tail = text[match.end():matches[number + 1].start() if number + 1 < len(matches) else len(text)]
        if number + 1 < len(matches):
            # Strip only the connector envelope paired with the next Message TS.
            envelope = re.search(r'(?m)^(?:=== Message from[^\n]*===[^\n]*\n[ \t\r\n]*|'
                                 r'(?:=== THREAD REPLIES \(\d+ total\) ===[ \t]*\n[ \t\r\n]*)?'
                                 r'--- Reply \d+ of \d+ ---[ \t]*\n'
                                 r'(?:From:[^\n]*\n)?(?:Time:[^\n]*\n)?[ \t\r\n]*)\Z', tail)
            if not envelope: raise McpFailure('invalid_source_response')
            tail = tail[:envelope.start()]
        elif text.startswith('=== THREAD PARENT MESSAGE ==='):
            tail = re.sub(r'\n=== THREAD REPLIES \(0 total\) ===\s*\Z', '', tail)
        body = tail.strip()
        result.append({'ts': match.group(1), 'text': body})
    if not result and not re.search(r'no messages|0 messages', text, re.IGNORECASE) and not re.fullmatch(r'\s*Channel:[^\n]*\s*', text):
        raise McpFailure('invalid_source_response')
    return result


def discover(client, provider, scope, start, end, limit, token):
    if provider == 'jira':
        keys = ','.join(scope['project_keys'])
        # Date literals use the Jira user's timezone. Widen dates, then filter exact UTC locally.
        low = date(start) - timedelta(days=1)
        high = date(end) + timedelta(days=2)
        args = {'cloudId': scope['cloud_id'], 'jql': f'project in ({keys}) AND updated >= "{low:%Y-%m-%d}" AND updated < "{high:%Y-%m-%d}" ORDER BY updated ASC',
                'fields': ['summary', 'project', 'updated'], 'maxResults': limit, 'searchResultMode': 'issues'}
        if token: args['nextPageToken'] = token
        data = client.call('searchJiraIssuesUsingJql', args)
        issues = data.get('issues') if isinstance(data, dict) else None
        if isinstance(issues, dict):
            items = require_list(issues, 'nodes'); page = issues.get('pageInfo', {})
            next_token = page.get('endCursor') if page.get('hasNextPage') else None
            if page.get('hasNextPage') and not next_token: raise McpFailure('invalid_pagination_response')
        else:
            items = require_list(data, 'issues'); next_token = data.get('nextPageToken')
            if data.get('isLast') is False and not next_token: raise McpFailure('invalid_pagination_response')
        items = [i for i in items if i['fields']['project']['key'] in scope['project_keys'] and in_window(i['fields'].get('updated'), start, end)]
        return {'items': [{'id': i['id']} for i in items], 'next_token': next_token}
    if provider == 'gmail':
        args = {'query': f"({scope['query']}) after:{int(date(start).timestamp())-1} before:{int(date(end).timestamp())+1}",
                'pageSize': limit, 'view': 'THREAD_VIEW_IDS_ONLY'}
        if token: args['pageToken'] = token
        data = client.call('search_threads', args)
        items = []
        for thread in require_list(data, 'threads', True):
            detail = client.call('get_thread', {'threadId': thread['id'], 'messageFormat': 'METADATA_ONLY'})
            for message in require_list(detail, 'messages'):
                created = epoch_iso(Decimal(message['internalDate']) / 1000) if message.get('internalDate') else iso(message.get('date'))
                if in_window(created, start, end):
                    items.append({'id': message['id'], 'threadId': thread['id'], 'created': created})
        unique = {item['id']: item for item in items}
        omissions = {}
        for entry in data.get('omittedContent', {}).get('omittedReasonCounts', []):
            reason, count = entry.get('reason', 'UNKNOWN'), entry.get('omittedCount', 0)
            if not isinstance(reason, str) or not isinstance(count, int) or count < 0:
                raise McpFailure('invalid_policy_summary')
            omissions[reason] = omissions.get(reason, 0) + count
        return {'items': sorted(unique.values(), key=lambda i: (i['created'], i['id'])),
                'next_token': data.get('nextPageToken'), 'policy_omissions': omissions}
    if provider == 'drive':
        types = ' or '.join("mimeType = '" + query_string(t) + "'" for t in scope.get('mime_types', [
            'application/vnd.google-apps.document', 'application/vnd.google-apps.spreadsheet', 'application/vnd.google-apps.presentation']))
        args = {'query': f"trashed = false and title contains '{query_string(scope['title_keyword'])}' and modifiedTime >= '{start}' and modifiedTime < '{end}' and ({types})",
                'pageSize': limit, 'orderBy': 'modifiedTime asc', 'excludeContentSnippets': True}
        if token: args['pageToken'] = token
        data = client.call('search_files', args)
        items = [i for i in require_list(data, 'files', True) if in_window(i.get('modifiedTime'), start, end)]
        return {'items': [{'id': i['id']} for i in items], 'next_token': data.get('nextPageToken')}
    if provider == 'chat':
        args = {'searchParameters': {'conversationId': scope['conversation_id'], 'startTime': start, 'endTime': end}, 'pageSize': limit}
        if token: args['pageToken'] = token
        data = client.call('search_messages', args)
        items = [i for i in require_list(data, 'messages', True) if in_window(i.get('createTime'), start, end)]
        return {'items': [{'messageId': i['messageId'], 'createTime': i['createTime']} for i in items], 'next_token': data.get('nextPageToken')}
    if provider == 'slack':
        args = {'filters': ' '.join('in:<#' + cid + '>' for cid in scope['channel_ids']), 'keywords': [],
                'after': str(int(date(start).timestamp()) - 1), 'before': str(int(date(end).timestamp()) + 1),
                'natural_language_query': '', 'limit': limit, 'include_context': False,
                'include_bots': True, 'response_format': 'detailed', 'sort': 'timestamp', 'sort_dir': 'asc', 'content_types': 'messages'}
        if token: args['cursor'] = token
        page = parse_slack_search(client.call('slack_search_public', args))
        page['items'] = [i for i in page['items'] if i['channel_id'] in scope['channel_ids'] and in_window(epoch_iso(i['ts']), start, end)]
        return page
    raise McpFailure('unknown_provider')


def adf_text(value):
    if isinstance(value, str):
        return value
    if not isinstance(value, dict):
        return ''
    if value.get('type') == 'text':
        return value.get('text', '')
    if value.get('type') == 'hardBreak':
        return '\n'
    text = ''.join(adf_text(item) for item in value.get('content', []))
    return text + ('\n' if value.get('type') in ('paragraph', 'heading', 'listItem', 'tableRow') else '')


def normalize_chat(item):
    if not item.get('messageId') or not isinstance(item.get('plaintextBody', ''), str):
        raise McpFailure('invalid_source_response')
    return {'provider': 'chat', 'remote_id': item['messageId'], 'title': 'Google Chat message',
            'text': item.get('plaintextBody', ''), 'source_url': item.get('viewUrl'),
            'source_created_at_utc': iso(item.get('createTime')), 'source_updated_at_utc': iso(item.get('updateTime')),
            'revision_tag': item.get('updateTime'), 'state': 'deleted' if item.get('deleteTime') else 'active',
            'completeness': 'partial', 'metadata': {'thread_id': item.get('threadId'),
            'author_id': item.get('sender', {}).get('userId'), 'warning': 'Message text only; attachments and hidden/private-only messages are not mirrored.'}}


def candidate_id(provider, scope, item):
    if provider == 'jira': return scope['cloud_id'] + '/' + item['id']
    if provider == 'chat': return item['messageId']
    if provider == 'slack': return item['channel_id'] + '/' + item['ts']
    return item['id']


def hydrate(client, provider, scope, item):
    if provider == 'chat':
        if not item['messageId'].startswith(scope['conversation_id'] + '/messages/'):
            raise McpFailure('out_of_scope')
        if 'plaintextBody' not in item:
            created = date(item.get('createTime'))
            if created is None: raise McpFailure('missing_source_timestamp')
            response = client.call('search_messages', {'searchParameters': {'conversationId': scope['conversation_id'],
                'startTime': (created - timedelta(seconds=1)).isoformat(), 'endTime': (created + timedelta(seconds=1)).isoformat()}, 'pageSize': 100})
            matches = [m for m in require_list(response, 'messages', True) if m.get('messageId') == item['messageId']]
            if len(matches) != 1: raise McpFailure('source_not_verified')
            item = matches[0]
        return normalize_chat(item)
    if provider == 'jira':
        data = client.call('getJiraIssue', {'cloudId': scope['cloud_id'], 'issueIdOrKey': item['id'],
            'fields': ['summary', 'description', 'project', 'status', 'created', 'updated', 'assignee', 'labels'],
            'responseContentFormat': 'markdown', 'updateHistory': False})
        if isinstance(data.get('issues'), dict):
            nodes = require_list(data['issues'], 'nodes')
            if len(nodes) != 1: raise McpFailure('source_id_mismatch')
            data = nodes[0]
        if data.get('id') != item['id']: raise McpFailure('source_id_mismatch')
        fields = data.get('fields', {})
        if fields.get('project', {}).get('key') not in scope['project_keys']:
            raise McpFailure('out_of_scope')
        summary = fields['summary']
        return {'provider': 'jira', 'remote_id': scope['cloud_id'] + '/' + data['id'],
                'title': summary, 'text': summary + '\n' + adf_text(fields.get('description')),
                'source_url': data.get('webUrl') or scope['site_url'].rstrip('/') + '/browse/' + data['key'],
                'source_created_at_utc': iso(fields.get('created')), 'source_updated_at_utc': iso(fields.get('updated')),
                'revision_tag': fields.get('updated'), 'state': 'active', 'completeness': 'partial',
                'metadata': {'issue_key': data['key'], 'project_key': fields['project']['key'],
                             'status': fields.get('status', {}).get('name'),
                             'assignee_id': (fields.get('assignee') or {}).get('accountId'),
                             'warning': 'Summary and description snapshot; comments and attachments are not mirrored.'}}
    if provider == 'gmail':
        m = client.call('get_message', {'messageId': item['id'], 'messageFormat': 'PLAIN_TEXT'})
        if m.get('id') != item['id']: raise McpFailure('source_id_mismatch')
        created = epoch_iso(Decimal(m['internalDate']) / 1000) if m.get('internalDate') else iso(m.get('date'))
        trashed = 'TRASH' in m.get('labelIds', [])
        return {'provider': 'gmail', 'remote_id': m['id'], 'title': m.get('subject', ''),
                'text': '' if trashed else m.get('plaintextBody', ''), 'source_url': m.get('viewUrl'),
                'source_created_at_utc': created, 'source_updated_at_utc': None, 'revision_tag': m.get('historyId'),
                'state': 'deleted' if trashed else 'active', 'completeness': 'partial',
                'metadata': {'thread_id': m.get('threadId'), 'sender': m.get('sender'),
                             'message_header_date': m.get('date'), 'warning': 'Plain-text email; attachments and HTML-only content are not mirrored.'}}
    if provider == 'drive':
        meta = client.call('get_file_metadata', {'fileId': item['id'], 'excludeContentSnippets': True})
        if meta.get('id') != item['id']: raise McpFailure('source_id_mismatch')
        if scope['title_keyword'].casefold() not in meta.get('title', '').casefold(): raise McpFailure('out_of_scope')
        trashed = bool(meta.get('trashed'))
        text = ''
        if not trashed:
            content = client.call('read_file_content', {'fileId': item['id'], 'includeComments': False})
            text = content.get('fileContent') if isinstance(content, dict) else None
            if not isinstance(text, str) or not text.strip(): raise McpFailure('missing_source_text')
            after = client.call('get_file_metadata', {'fileId': item['id'], 'excludeContentSnippets': True})
            if meta.get('etag') != after.get('etag') or meta.get('modifiedTime') != after.get('modifiedTime'):
                raise McpFailure('source_changed_during_read')
        return {'provider': 'drive', 'remote_id': meta['id'], 'title': meta.get('title', ''), 'text': text,
                'source_url': meta.get('viewUrl'), 'source_created_at_utc': iso(meta.get('createdTime')),
                'source_updated_at_utc': iso(meta.get('modifiedTime')), 'revision_tag': meta.get('etag'),
                'state': 'deleted' if trashed else 'active', 'completeness': 'partial',
                'metadata': {'mime_type': meta.get('mimeType'), 'warning': 'Connector-readable projection may omit cells, sections, comments and embedded objects; verify the original for consequential claims.'}}
    if provider == 'slack':
        if item['channel_id'] not in scope['channel_ids']: raise McpFailure('out_of_scope')
        stamp = Decimal(item['ts'])
        args = {'channel_id': item['channel_id'],
            'oldest': str(stamp - Decimal('0.000001')), 'latest': str(stamp + Decimal('0.000001')),
            'limit': 1, 'response_format': 'detailed'}
        thread = item.get('thread_ts')
        if thread and thread != item['ts']:
            if not re.fullmatch(r'[0-9]+\.[0-9]+', thread): raise McpFailure('invalid_source_response')
            args['message_ts'] = thread
            response = client.call('slack_read_thread', args)
        else:
            response = client.call('slack_read_channel', args)
        matches = [m for m in parse_slack_read(response) if m['ts'] == item['ts']]
        if len(matches) != 1: raise McpFailure('source_not_verified')
        return {'provider': 'slack', 'remote_id': item['channel_id'] + '/' + item['ts'],
                'title': 'Slack message', 'text': matches[0]['text'], 'source_url': item.get('source_url'),
                'source_created_at_utc': epoch_iso(item['ts']), 'source_updated_at_utc': None,
                'revision_tag': None, 'state': 'active', 'completeness': 'partial',
                'metadata': {'channel_id': item['channel_id'], 'message_ts': item['ts'],
                             'thread_ts': item.get('thread_ts'),
                             'warning': 'Public-channel text projection; attachments, replies and source edit timestamps may be incomplete.'}}
    raise McpFailure('unknown_provider')


def recheck(client, provider, scope, known):
    rid, meta = known['remote_id'], known['metadata']
    if provider == 'jira':
        if not rid.startswith(scope['cloud_id'] + '/') or meta.get('project_key') not in scope['project_keys']:
            raise McpFailure('out_of_scope')
        item = {'id': rid.split('/', 1)[1]}
    elif provider in ('gmail', 'drive'):
        item = {'id': rid}
    elif provider == 'slack':
        item = {'channel_id': meta['channel_id'], 'ts': meta['message_ts'],
                'thread_ts': meta.get('thread_ts'), 'source_url': known.get('source_url')}
    elif provider == 'chat':
        if not rid.startswith(scope['conversation_id'] + '/messages/') or not known.get('source_created_at_utc'):
            raise McpFailure('out_of_scope')
        created = date(known['source_created_at_utc'])
        response = client.call('search_messages', {'searchParameters': {'conversationId': scope['conversation_id'],
            'startTime': (created - timedelta(seconds=1)).isoformat(), 'endTime': (created + timedelta(seconds=1)).isoformat()}, 'pageSize': 100})
        matches = [m for m in require_list(response, 'messages') if m.get('messageId') == rid]
        if len(matches) != 1: raise McpFailure('source_not_verified')
        item = matches[0]
    else:
        raise McpFailure('unknown_provider')
    return hydrate(client, provider, scope, item)
