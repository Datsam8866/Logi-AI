"""Read-only stdio MCP client for the user's existing LogiQ connections."""
import json
import os
from pathlib import Path
import queue
import subprocess
import threading
import time

COMPONENTS = {'jira': 'codex_atlassian_jira', 'gmail': 'codex_gmail',
              'drive': 'codex_gdrive', 'chat': 'codex_gchat', 'slack': 'codex_slack'}
READ_TOOLS = {
    'jira': {'searchJiraIssuesUsingJql', 'getJiraIssue'},
    'gmail': {'search_threads', 'get_thread', 'get_message'},
    'drive': {'search_files', 'get_file_metadata', 'read_file_content'},
    'chat': {'search_messages'},
    'slack': {'slack_search_public', 'slack_read_channel', 'slack_read_thread'},
}


class McpFailure(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def error_code(value):
    text = str(value).lower()
    if 'permission' in text or '403' in text or 'forbidden' in text:
        return 'permission_denied'
    if '401' in text or 'unauthorized' in text or 'authenticate' in text or 'sign in' in text:
        return 'authentication_required'
    if '404' in text or 'not found' in text:
        return 'not_found'
    return 'tool_error'


def unwrap(result):
    if result.get('isError'):
        raise McpFailure(error_code(result.get('content', [])))
    if result.get('structuredContent') is not None:
        value = result['structuredContent']
    else:
        parts = []
        for item in result.get('content', []):
            if item.get('type') == 'text':
                parts.append(item.get('text', ''))
            elif item.get('type') == 'resource':
                parts.append(item.get('resource', {}).get('text', ''))
        text = '\n'.join(parts)
        try:
            value = json.loads(text)
        except ValueError:
            value = {'fileContent': text} if text else {}
    if isinstance(value, dict) and value.get('error'):
        raise McpFailure(error_code(value))
    return value


class McpClient:
    def __init__(self, provider, timeout=40, command=None):
        self.provider, self.timeout, self.command = provider, timeout, command
        self.process = None
        self.messages = queue.Queue()
        self.sequence = 0
        self.tool_names = set()

    def __enter__(self):
        executable = Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'logiq' / 'logiq.EXE'
        command = self.command or [str(executable), 'mcp', 'connect', 'codex/' + COMPONENTS[self.provider]]
        try:
            self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace',
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            threading.Thread(target=self._stdout, daemon=True).start()
            threading.Thread(target=self._stderr, daemon=True).start()
            self.request('initialize', {'protocolVersion': '2024-11-05', 'capabilities': {},
                                      'clientInfo': {'name': 'codex', 'version': '1.0'}})
            self._send({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
            listing = self.request('tools/list', {})
            self.tool_names = {item['name'] for item in listing.get('tools', [])}
            if not self.tool_names:
                raise McpFailure('authentication_required')
            return self
        except (OSError, ValueError) as exc:
            self.close()
            raise McpFailure('connection_failed') from exc
        except McpFailure:
            self.close()
            raise

    def _stdout(self):
        try:
            for line in self.process.stdout:
                try:
                    self.messages.put(json.loads(line))
                except ValueError:
                    self.messages.put({'transport_error': 'invalid_protocol_response'})
        except (OSError, ValueError):
            pass
        finally:
            self.messages.put({'transport_error': 'connection_closed'})

    def _stderr(self):
        # Authentication URLs, tokens and remote source text must not enter logs.
        try:
            for _ in self.process.stderr:
                pass
        except (OSError, ValueError):
            pass

    def _send(self, message):
        try:
            self.process.stdin.write(json.dumps(message, ensure_ascii=False) + '\n')
            self.process.stdin.flush()
        except (OSError, ValueError) as exc:
            raise McpFailure('connection_closed') from exc

    def request(self, method, params):
        self.sequence += 1
        rid = self.sequence
        self._send({'jsonrpc': '2.0', 'id': rid, 'method': method, 'params': params})
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                message = self.messages.get(timeout=max(0.01, deadline - time.monotonic()))
            except queue.Empty as exc:
                raise McpFailure('tool_timeout') from exc
            if message.get('transport_error'):
                raise McpFailure(message['transport_error'])
            if message.get('method') == 'ping' and 'id' in message:
                self._send({'jsonrpc': '2.0', 'id': message['id'], 'result': {}})
            if message.get('id') != rid:
                if time.monotonic() >= deadline:
                    raise McpFailure('tool_timeout')
                continue
            if message.get('error'):
                raise McpFailure(error_code(message['error']))
            if 'result' not in message:
                raise McpFailure('invalid_protocol_response')
            return message['result']

    def call(self, name, arguments):
        if name not in READ_TOOLS[self.provider]:
            raise McpFailure('write_tool_forbidden')
        if name not in self.tool_names:
            raise McpFailure('missing_tool')
        return unwrap(self.request('tools/call', {'name': name, 'arguments': arguments}))

    def close(self):
        if not self.process:
            return
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)
        for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
            if stream:
                try:
                    stream.close()
                except OSError:
                    pass

    def __exit__(self, *args):
        self.close()
