"""Synthetic read-only provider fixtures and real SQLite/stdio acceptance tests."""
from contextlib import closing
import importlib
import inspect
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))


class RemoteSyncTests(unittest.TestCase):
    def module(self, name):
        try:
            result = importlib.import_module(name)
        except ModuleNotFoundError:
            result = None
        self.assertIsNotNone(result, 'Phase 3 module must exist: ' + name)
        return result

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = self.root / 'test.sqlite3'

    def database(self):
        from kb_store import initialize, connect
        initialize(self.db, self.root)
        c = connect(self.db)
        self.addCleanup(c.close)
        return c

    def observation(self, text='InitialEvidence', revision='v1', state='active'):
        return {'provider': 'jira', 'remote_id': 'cloud/123', 'title': 'Synthetic title',
                'text': text, 'source_url': 'https://example.atlassian.net/browse/EX-1',
                'source_created_at_utc': '2026-01-01T00:00:00Z',
                'source_updated_at_utc': '2026-01-02T00:00:00Z', 'revision_tag': revision,
                'state': state, 'completeness': 'full', 'metadata': {'issue_key': 'EX-1'}}

    def test_remote_deduplication_and_retained_observed_versions(self):
        store = self.module('remote_store'); c = self.database()
        first = store.upsert(c, self.observation())
        second = store.upsert(c, self.observation())
        self.assertEqual(first['status'], 'created')
        self.assertEqual(second['status'], 'unchanged')
        self.assertEqual(c.execute('SELECT count(*) FROM remote_versions').fetchone()[0], 1)
        changed = store.upsert(c, self.observation('UpdatedEvidence', 'v2'))
        self.assertEqual(changed['status'], 'updated')
        self.assertFalse(store.read_remote(c, first['version_id'])['is_current'])
        self.assertEqual(store.search_remote(c, 'InitialEvidence', 5), [])
        self.assertEqual(store.search_remote(c, 'UpdatedEvidence', 5)[0]['source_url'], self.observation()['source_url'])

    def test_unknown_revision_is_observed_hash_not_invented_source_date(self):
        store = self.module('remote_store'); c = self.database()
        item = self.observation(); item.update(revision_tag=None, source_updated_at_utc=None)
        first = store.upsert(c, item)
        hit = store.read_remote(c, first['version_id'])
        self.assertIsNone(hit['source_updated_at_utc'])
        self.assertEqual(hit['version_basis'], 'observed_content')
        item['text'] = 'ChangedWithoutKnownRevision'
        store.upsert(c, item)
        self.assertEqual(c.execute('SELECT count(*) FROM remote_versions').fetchone()[0], 2)

    def test_unavailable_and_deleted_records_keep_cached_history(self):
        store = self.module('remote_store'); c = self.database()
        first = store.upsert(c, self.observation())
        store.mark_unavailable(c, 'jira', 'cloud/123', 'inaccessible')
        self.assertEqual(store.search_remote(c, 'InitialEvidence', 5), [])
        self.assertEqual(store.read_remote(c, first['version_id'])['availability'], 'inaccessible')
        self.assertEqual(store.read_remote(c, first['version_id'])['text'], 'InitialEvidence')
        store.upsert(c, self.observation())
        store.upsert(c, self.observation('', 'deleted-v2', 'deleted'))
        self.assertEqual(store.search_remote(c, 'InitialEvidence', 5), [])
        self.assertEqual(c.execute('SELECT count(*) FROM remote_versions').fetchone()[0], 2)

    def test_partial_drive_evidence_and_bounded_remote_reads(self):
        store = self.module('remote_store'); c = self.database()
        item = self.observation('prefix ' * 1000 + 'LateRemoteEvidence')
        item.update(provider='drive', remote_id='file-1', completeness='partial', metadata={'long': 'x' * 20000})
        saved = store.upsert(c, item)
        hit = store.search_remote(c, 'LateRemoteEvidence', 2)[0]
        self.assertIn('LateRemoteEvidence', hit['snippet'])
        read = store.read_remote(c, saved['version_id'], 320, hit['snippet_start'])
        self.assertEqual(read['completeness'], 'partial')
        self.assertTrue(read['details_omitted'])
        self.assertLess(len(json.dumps(read)), 2200)

    def test_remote_and_local_search_are_both_available(self):
        store = self.module('remote_store'); c = self.database()
        from kb_store import ingest, search, read
        path = self.root / 'local.txt'; path.write_text('LocalEvidence', encoding='utf-8')
        ingest(c, path); saved = store.upsert(c, self.observation('RemoteEvidence'))
        self.assertTrue(search(c, 'LocalEvidence')['hits'])
        hit = search(c, 'RemoteEvidence')['hits'][0]
        self.assertEqual(hit['kind'], 'remote')
        self.assertEqual(read(c, 'remote', saved['version_id'])['text'], 'RemoteEvidence')

    def test_checkpoint_completion_and_stale_updates(self):
        store = self.module('remote_store'); c = self.database()
        state = {'window_start': '2026-01-01T00:00:00Z', 'window_end': '2026-02-01T00:00:00Z',
                 'cursor': {'page_token': 'next', 'pending': []}, 'complete': False, 'watermark': None}
        store.apply_batch(c, 'jira', 'scope', 0, [self.observation()], state, [])
        cp = store.checkpoint(c, 'jira', 'scope')
        self.assertFalse(cp['complete']); self.assertIsNone(cp['watermark'])
        with self.assertRaises(Exception):
            store.apply_batch(c, 'jira', 'scope', 0, [self.observation('BadOverwrite', 'v2')], state, [])
        self.assertEqual(c.execute('SELECT count(*) FROM remote_versions').fetchone()[0], 1)
        state.update(complete=True, cursor={'page_token': None, 'pending': []}, watermark=state['window_end'])
        store.apply_batch(c, 'jira', 'scope', cp['generation'], [], state, [])
        self.assertEqual(store.checkpoint(c, 'jira', 'scope')['watermark'], state['window_end'])

    def test_run_logs_do_not_persist_raw_error_or_secret_text(self):
        store = self.module('remote_store'); c = self.database()
        state = {'window_start': '2026-01-01T00:00:00Z', 'window_end': '2026-02-01T00:00:00Z',
                 'cursor': {'pending': []}, 'complete': False, 'watermark': None}
        error = {'code': 'permission_denied', 'message': 'SECRET_TOKEN=do-not-log', 'remote_id': 'cloud/123'}
        store.apply_batch(c, 'jira', 'scope', 0, [], state, [error])
        dump = '\n'.join(c.iterdump())
        self.assertNotIn('SECRET_TOKEN', dump)
        self.assertIn('permission_denied', dump)

    def test_chat_normalization_keeps_original_id_and_unknown_edit_date(self):
        adapters = self.module('source_adapters')
        item = {'messageId': 'spaces/room/messages/msg.msg', 'createTime': '2026-01-01T00:00:00Z',
                'plaintextBody': 'ChatEvidence', 'threadId': 'spaces/room/threads/msg', 'sender': {'userId': 'users/1'}}
        normalized = adapters.normalize_chat(item)
        self.assertEqual(normalized['remote_id'], item['messageId'])
        self.assertEqual(normalized['text'], 'ChatEvidence')
        self.assertIsNone(normalized['source_updated_at_utc'])

    def test_slack_search_and_read_formats_are_validated(self):
        adapters = self.module('source_adapters')
        result = {'results': '### Result 1 of 1\nChannel: #test (ID: C123)\nMessage_ts: 1234567890.123456\nPermalink: [link](https://example.slack.com/archives/C123/p1234567890123456)\nText: \nSlackEvidence\n\n---\n',
                  'pagination_info': 'For the next page use cursor `next-token`'}
        page = adapters.parse_slack_search(result)
        self.assertEqual(page['items'][0]['ts'], '1234567890.123456')
        self.assertEqual(page['next_token'], 'next-token')
        text = adapters.parse_slack_read({'messages': 'Channel: #test (C123)\n=== Message from Test at now ===\nMessage TS: 1234567890.123456\n\nSlackEvidence', 'pagination_info': 'No more messages'})
        self.assertEqual(text[0]['text'], 'SlackEvidence')
        with self.assertRaises(Exception): adapters.parse_slack_search({'results': 'Unexpected format'})

    def test_source_scopes_and_time_windows_are_in_tool_requests(self):
        adapters = self.module('source_adapters')
        calls = []
        class Client:
            def call(self, name, args):
                calls.append((name,args)); return {'messages': [], 'nextPageToken': 'more'}
        result = adapters.discover(Client(), 'chat', {'conversation_id': 'spaces/room'},
                                   '2026-01-01T00:00:00Z', '2026-02-01T00:00:00Z', 2, None)
        args = calls[0][1]['searchParameters']
        self.assertEqual(args['conversationId'], 'spaces/room')
        self.assertEqual(args['startTime'], '2026-01-01T00:00:00Z')
        self.assertEqual(result['next_token'], 'more')

    def test_configuration_rejects_private_slack_and_unbounded_batches(self):
        sync = self.module('sync_sources')
        with self.assertRaises(Exception): sync.validate_config({'per_source_limit': 1000, 'providers': {}})
        with self.assertRaises(Exception): sync.validate_config({'providers': {'slack': {'channel_ids': ['C123'], 'public_only': False}}})

    def test_failed_candidate_stays_pending_for_later_run(self):
        sync = self.module('sync_sources'); transport = self.module('mcp_stdio')
        cp = {'generation': 0, 'window_start': '2026-01-01T00:00:00Z', 'window_end': '2026-02-01T00:00:00Z',
              'cursor': {'pending': [{'messageId':'spaces/room/messages/1.1','createTime':'2026-01-02T00:00:00Z','plaintextBody':'Evidence'}], 'page_token': None, 'exhausted': True},
              'complete': False, 'watermark': None}
        # A Drive pending candidate requires an exact read and must survive its failure.
        cp['cursor']['pending'] = [{'id':'file-1','title':'Coleco Test','modifiedTime':'2026-01-02T00:00:00Z','etag':'v1','viewUrl':'https://drive.google.com/file/d/file-1/view'}]
        class Client:
            def call(self, name,args): raise transport.McpFailure('permission_denied')
        result = sync.collect_provider(Client(), 'drive', {'title_keyword':'Coleco'}, cp, 2, [])
        self.assertFalse(result['state']['complete'])
        self.assertEqual(result['state']['cursor']['pending'][0]['id'], 'file-1')
        self.assertEqual(result['errors'][0]['code'], 'permission_denied')

    def test_existing_mcp_stdio_transport_and_read_allowlist(self):
        transport = self.module('mcp_stdio')
        script = self.root / 'fake_server.py'
        script.write_text('''import sys,json
for line in sys.stdin:
 r=json.loads(line)
 if 'id' not in r:continue
 method=r['method']
 if method=='initialize':result={'protocolVersion':'2024-11-05','capabilities':{'tools':{}},'serverInfo':{'name':'fixture','version':'1'}}
 elif method=='tools/list':result={'tools':[{'name':'search_files'}]}
 else:result={'content':[{'type':'text','text':json.dumps({'files':[]})}]}
 print(json.dumps({'jsonrpc':'2.0','id':r['id'],'result':result}),flush=True)
''', encoding='utf-8')
        with transport.McpClient('drive', timeout=3, command=[sys.executable,'-B',str(script)]) as client:
            self.assertEqual(client.call('search_files', {'query':'safe'}), {'files':[]})
            with self.assertRaises(transport.McpFailure): client.call('create_file', {'title':'not allowed'})

    def test_legal_empty_search_pages_and_policy_omissions(self):
        sync = self.module('sync_sources')
        cp = {'generation':0,'window_start':'2026-01-01T00:00:00Z','window_end':'2026-02-01T00:00:00Z',
              'cursor':{'pending':[],'page_token':None,'exhausted':False},'complete':False,'watermark':None}
        class Empty:
            def call(self,name,args): return {}
        result = sync.collect_provider(Empty(),'gmail',{'query':'Coleco'},cp,2,[])
        self.assertTrue(result['state']['complete']); self.assertEqual(result['errors'],[])
        class Filtered:
            def call(self,name,args): return {'omittedContent':{'omittedReasonCounts':[{'reason':'CONFIDENTIAL','omittedCount':2}]}}
        result = sync.collect_provider(Filtered(),'gmail',{'query':'Coleco'},cp,2,[])
        self.assertIn('policy_omissions',result['state']['cursor'])
        self.assertEqual(result['state']['cursor']['policy_omissions']['CONFIDENTIAL'],2)

    def test_empty_page_with_token_is_resumable(self):
        adapters = self.module('source_adapters')
        class Client:
            def call(self,name,args): return {'nextPageToken':'next'}
        try:
            page = adapters.discover(Client(),'gmail',{'query':'Coleco'},'2026-01-01T00:00:00Z','2026-02-01T00:00:00Z',2,None)
        except Exception as exc:
            self.fail('Legal empty page must be accepted: ' + type(exc).__name__)
        self.assertEqual(page['items'],[]); self.assertEqual(page['next_token'],'next')

    def test_missing_required_discovery_timestamp_blocks_completion(self):
        sync = self.module('sync_sources')
        cp = {'generation':0,'window_start':'2026-01-01T00:00:00Z','window_end':'2026-02-01T00:00:00Z',
              'cursor':{'pending':[],'page_token':None,'exhausted':False},'complete':False,'watermark':None}
        class Client:
            def call(self,name,args): return {'files':[{'id':'file','title':'Coleco'}]}
        result=sync.collect_provider(Client(),'drive',{'title_keyword':'Coleco'},cp,2,[])
        self.assertFalse(result['state']['complete']); self.assertTrue(result['errors'])

    def test_scope_membership_prevents_rechecking_other_spaces(self):
        store = self.module('remote_store'); c=self.database()
        self.assertIn('scope_key',inspect.signature(store.recheck_candidates).parameters)
        item=self.observation(); item.update(provider='chat',remote_id='spaces/old/messages/1.1')
        state={'window_start':'2026-01-01T00:00:00Z','window_end':'2026-02-01T00:00:00Z',
               'cursor':{'pending':[]},'complete':True,'watermark':None}
        store.apply_batch(c,'chat','old-scope',0,[item],state,[])
        self.assertEqual(store.recheck_candidates(c,'chat',1,'new-scope'),[])
        store.apply_batch(c,'chat','new-scope',0,[],state,[{'code':'out_of_scope','remote_id':item['remote_id']}])
        self.assertTrue(store.search_remote(c,'InitialEvidence',5))

    def test_slack_reply_reads_parent_thread_and_keeps_reply_id(self):
        adapters = self.module('source_adapters'); calls=[]
        class Client:
            def call(self,name,args):
                calls.append((name,args))
                return {'messages':'=== THREAD REPLIES (1 total) ===\n--- Reply 1 of 1 ---\nFrom: User\nMessage TS: 1234567891.123456\nReplyEvidence\n', 'pagination_info':'No more messages'}
        item={'channel_id':'C123','ts':'1234567891.123456','thread_ts':'1234567890.123456','source_url':'https://example.slack.com/link'}
        try:
            result=adapters.hydrate(Client(),'slack',{'channel_ids':['C123']},item)
        except Exception as exc:
            self.fail('Reply read must succeed: ' + type(exc).__name__)
        self.assertEqual(calls[0][0],'slack_read_thread')
        self.assertEqual(calls[0][1]['message_ts'],item['thread_ts'])
        self.assertEqual(result['remote_id'],'C123/1234567891.123456')
        self.assertEqual(result['text'],'ReplyEvidence')

    def test_discovery_queues_ids_instead_of_chat_content(self):
        adapters = self.module('source_adapters')
        class Client:
            def call(self,name,args):return {'messages':[{'messageId':'spaces/room/messages/1.1','createTime':'2026-01-02T00:00:00Z','plaintextBody':'Do not duplicate this text'}]}
        page=adapters.discover(Client(),'chat',{'conversation_id':'spaces/room'},'2026-01-01T00:00:00Z','2026-02-01T00:00:00Z',2,None)
        self.assertNotIn('plaintextBody',page['items'][0])

    def test_older_source_revision_cannot_replace_newer_current_evidence(self):
        store=self.module('remote_store');c=self.database()
        newer=self.observation('NewerEvidence','v2');newer['source_updated_at_utc']='2026-01-03T00:00:00Z'
        store.upsert(c,newer)
        store.upsert(c,self.observation('OlderEvidence','v1'))
        self.assertTrue(store.search_remote(c,'NewerEvidence',5))
        self.assertEqual(store.search_remote(c,'OlderEvidence',5),[])

    def test_jira_date_literals_cover_user_timezone_before_exact_filtering(self):
        adapters=self.module('source_adapters');calls=[]
        class Client:
            def call(self,name,args):calls.append(args);return {'issues':[],'isLast':True}
        adapters.discover(Client(),'jira',{'cloud_id':'cloud','project_keys':['COL']},'2026-01-01T00:00:00Z','2026-01-02T00:00:00Z',2,None)
        self.assertIn('2025-12-31',calls[0]['jql'])
        self.assertIn('2026-01-04',calls[0]['jql'])

    def test_mcp_timeout_is_classified_without_raw_stderr(self):
        transport=self.module('mcp_stdio')
        script=self.root/'silent_server.py';script.write_text('import sys,time\nprint("SECRET",file=sys.stderr,flush=True)\ntime.sleep(10)',encoding='utf-8')
        with self.assertRaises(transport.McpFailure) as failure:
            with transport.McpClient('drive',timeout=0.1,command=[sys.executable,str(script)]):pass
        self.assertEqual(str(failure.exception),'tool_timeout')

    def test_jira_detail_id_mismatch_keeps_requested_candidate_pending(self):
        sync=self.module('sync_sources')
        class Client:
            def call(self,name,args):return {'id':'124','key':'COL-2','fields':{'summary':'Wrong issue','project':{'key':'COL'}}}
        cp={'generation':0,'window_start':'2026-01-01T00:00:00Z','window_end':'2026-02-01T00:00:00Z',
            'cursor':{'pending':[{'id':'123'}],'page_token':None,'exhausted':True},'complete':False,'watermark':None}
        result=sync.collect_provider(Client(),'jira',{'cloud_id':'cloud','site_url':'https://example.atlassian.net','project_keys':['COL']},cp,2,[])
        self.assertFalse(result['state']['complete'])
        self.assertEqual(result['state']['cursor']['pending'][0]['id'],'123')
        self.assertEqual(result['errors'][0]['code'],'source_id_mismatch')

    def test_slack_body_separator_lines_are_preserved(self):
        adapters=self.module('source_adapters')
        body='Initial data\n=== Thermal test ===\nMeasured 62 C\n--- Reply quoted from report ---\nFinal data'
        response={'messages':'Channel: #test (C123)\n=== Message from Test at now ===\nMessage TS: 1234567890.123456\n'+body+'\n'}
        self.assertEqual(adapters.parse_slack_read(response)[0]['text'],body)

    def test_page_size_does_not_change_when_rechecks_reserve_budget(self):
        sync=self.module('sync_sources');calls=[]
        class Client:
            def call(self,name,args):calls.append(args);return {'messages':[],'nextPageToken':'next2'}
        cp={'generation':1,'window_start':'2026-01-01T00:00:00Z','window_end':'2026-02-01T00:00:00Z',
            'cursor':{'pending':[],'page_token':'next1','exhausted':False,'page_size':2},'complete':False,'watermark':None}
        old=[{'remote_id':'spaces/room/messages/1.1','metadata':{},'source_created_at_utc':'2026-01-02T00:00:00Z'}]
        sync.collect_provider(Client(),'chat',{'conversation_id':'spaces/room'},cp,2,old)
        self.assertEqual(calls[0]['pageSize'],2)


if __name__ == '__main__':
    unittest.main()
