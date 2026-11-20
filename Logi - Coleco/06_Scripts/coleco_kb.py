"""Coleco JSON CLI: bounded evidence retrieval and read-only MCP collection."""
import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import sys

from kb_store import connect, ingest, initialize, read, search, status
from local_extract import IngestError

ROOT = Path(__file__).resolve().parents[1]


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db', type=Path, default=ROOT / '04_Database' / 'coleco.sqlite3')
    commands = p.add_subparsers(dest='command', required=True)
    commands.add_parser('init', help='Add local ingestion tables; back up an existing database first.')
    commands.add_parser('status', help='Read local counts and integrity without modifying the database.')
    imp = commands.add_parser('ingest', help='Import files/directories, or the default manual reports inbox.')
    imp.add_argument('paths', nargs='*', type=Path)
    find = commands.add_parser('search', help='Search current local evidence only.')
    find.add_argument('query')
    find.add_argument('--limit', type=int, default=5)
    show = commands.add_parser('read', help='Read evidence by kind/id returned by search, including archived versions.')
    show.add_argument('kind', choices=['chunk', 'legacy_cell', 'fan_measurement', 'remote'])
    show.add_argument('id', type=int)
    show.add_argument('--max-chars', type=int, default=8000)
    show.add_argument('--offset', type=int, default=0)
    sync = commands.add_parser('sync', help='Resume bounded five-source collection through existing LogiQ MCP connections.')
    sync.add_argument('--config', type=Path, default=ROOT / '00_Config' / 'source_scopes.local.json')
    sync.add_argument('--source', action='append', choices=['jira', 'gmail', 'drive', 'chat', 'slack'])
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == 'init':
            result = initialize(args.db, ROOT)
        elif args.command == 'sync':
            from sync_sources import run_sync
            result = run_sync(args.db, ROOT, args.config, args.source)
        elif args.command == 'ingest':
            initialized = initialize(args.db, ROOT)
            paths = args.paths or [ROOT / '01_Inbox' / 'Manual_Reports']
            files = []
            for path in paths:
                files.extend(sorted(p for p in path.rglob('*') if p.is_file() and not p.name.startswith('~$')) if path.is_dir() else [path])
            with closing(connect(args.db)) as c:
                results = [ingest(c, path) for path in files]
            result = {'files': len(files), 'results': results, 'backup_path': initialized['backup_path']}
        else:
            with closing(connect(args.db, readonly=True)) as c:
                if args.command == 'status':
                    result = status(c)
                elif args.command == 'search':
                    result = search(c, args.query, args.limit)
                else:
                    result = read(c, args.kind, args.id, args.max_chars, args.offset)
    except IngestError as exc:
        result = {'status': 'error', 'error_code': exc.code, 'message': str(exc)}
    except sqlite3.Error:
        result = {'status': 'error', 'error_code': 'database_error', 'message': 'SQLite operation failed; check database integrity and access. No source text is logged.'}
    except OSError:
        result = {'status': 'error', 'error_code': 'filesystem_error', 'message': 'Local file or directory access failed.'}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sync_failed = args.command == 'sync' and any(r.get('errors') for r in result.get('sources', []))
    return 1 if result.get('status') == 'error' or any(r['status'] == 'error' for r in result.get('results', [])) or sync_failed else 0


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    raise SystemExit(main())
