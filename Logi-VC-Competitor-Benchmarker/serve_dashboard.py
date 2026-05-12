# -*- coding: utf-8-sig -*-
"""
Local server for VC Competitor Benchmarker dashboard.

Usage:
    python serve_dashboard.py

Endpoints:
    GET /              → serves reports/dashboard.html
    GET /api/refresh   → re-reads SQLite, regenerates HTML, returns JSON
"""
import http.server, json, os, sys, threading, webbrowser
from urllib.parse import urlparse

BASE = os.path.dirname(os.path.abspath(__file__))
DASHBOARD = os.path.join(BASE, 'reports', 'dashboard.html')
PORT = 8765

sys.path.insert(0, BASE)
from generate_dashboard import load_devices, build_html


def regenerate():
    devices = load_devices()
    html = build_html(devices)
    os.makedirs(os.path.dirname(DASHBOARD), exist_ok=True)
    with open(DASHBOARD, 'w', encoding='utf-8-sig') as f:
        f.write(html)
    return len(devices)


class Handler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        path = urlparse(self.path).path

        if path in ('/', '/dashboard', '/dashboard.html'):
            try:
                with open(DASHBOARD, 'rb') as f:
                    body = f.read()
                self._respond(200, 'text/html; charset=utf-8', body)
            except FileNotFoundError:
                self._respond(404, 'text/plain', b'Run python generate_dashboard.py first.')

        elif path == '/api/refresh':
            try:
                count = regenerate()
                body = json.dumps({'status': 'ok', 'count': count}, ensure_ascii=False).encode()
                self._respond(200, 'application/json', body)
                print(f'  Refreshed: {count} devices loaded.')
            except Exception as exc:
                body = json.dumps({'status': 'error', 'message': str(exc)}).encode()
                self._respond(500, 'application/json', body)

        else:
            self._respond(404, 'text/plain', b'Not found')

    def _respond(self, code, ctype, body):
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f'  [{self.log_date_time_string()}] {fmt % args}')


def main():
    print('=== VC Competitor Benchmarker ===')
    print('Generating dashboard from SQLite...')
    count = regenerate()
    print(f'Ready: {count} devices loaded.')

    url = f'http://localhost:{PORT}/'
    print(f'Server: {url}')
    print('Press Ctrl+C to stop.\n')

    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    http.server.HTTPServer(('localhost', PORT), Handler).serve_forever()


if __name__ == '__main__':
    main()
