# Phase 3 — Five-source incremental MCP collection

Scope: Jira, Gmail, Google Drive, Google Chat and Slack. Local SQLite writes and read-only source calls are authorized; no remote writes, new credentials, scheduling, dashboard or Git publication.

## Design

- Reuse the installed LogiQ CLI's stdio MCP connections. A standard-library client performs initialize/tools-list/read-only tool calls with timeouts. No source text, auth tokens or raw stderr enter logs.
- Default first window is the past 30 days; each run processes at most two detailed records per provider (ten across five providers). A user-selected lookback overrides this before the first real scan.
- Jira is scoped to the verified Coleco project; Gmail to Coleco searches; Drive to Coleco-named native Docs/Sheets/Slides; Chat to the verified team space; Slack to verified public Coleco channels. Private Slack content requires separate scope authorization.
- Provider adapters preserve stable IDs, source URLs/IDs, created/updated timestamps, source revision tags when known, and normalized source text. Drive connector projections are explicitly marked partial; missing dates are never synthesized.
- Add `remote_records`, `remote_versions`, FTS5, per-scope checkpoints and run logs to the existing database. Same ID/revision/hash deduplicates; observed changes retain earlier versions. No local report/fan records are changed.
- Freeze each query window until all pages and pending candidates are consumed. Persist page tokens and pending IDs; only a finished window advances its watermark. Failures retain pending work and do not silently complete a scan. Reject stale concurrent checkpoint updates.
- Message APIs filter primarily by creation time. Reserve part of later batches for rotating known-record rechecks to observe older edits/access changes. This is bounded verification, not a guarantee of immediate detection of every historical edit/deletion.
- Explicit trash/deletion observations become tombstones; permission/not-found results become inaccessible; timeouts remain unverified. Preserve cached versions and exclude unavailable records from current search.
- Search/read/status include remote evidence and scan coverage. Historical records remain readable by version ID. A missing result in a search never proves deletion.

## Files and execution

1. `06_Scripts/mcp_stdio.py`: existing LogiQ transport, JSON-RPC and bounded timeouts; only provider allowlisted read tools are callable.
2. `06_Scripts/source_adapters.py`: five provider queries, discovery/pagination, exact readback, normalization and strict response-shape validation.
3. `06_Scripts/remote_store.py`: additive schema, version deduplication, availability, checkpoint/run persistence and bounded retrieval.
4. `06_Scripts/sync_sources.py`: config validation, bounded provider collection and atomic per-provider application. Existing local CLI gains `sync`; search/read/status retain Phase 2 behavior.
5. `06_Scripts/tests/test_remote_sync.py`: synthetic provider responses, real local SQLite and a disposable stdio server. Prove deduplication, update history, failed pagination recovery, older-edit rechecks, partial projections, query scope, redacted errors, concurrent checkpoint rejection and local regression compatibility.
6. `00_Config/source_scopes.example.json`: safe example; real identifiers in Git-excluded `source_scopes.local.json`. All data, checkpoints and run logs stay in Git-excluded paths.
7. Run tests, independent review and first bounded real five-source scan. Repeat a pinned window to demonstrate deduplication; verify original local data/hash and database/FTS integrity. Update README with exact outcomes and remaining coverage.

## Limits

- No complete historical backfill is implied by the initial bounded scan. Empty/partial provider pages with a token still require continuation.
- Gmail and chat/Slack updates lack a reliable global modification-time feed; source revision timestamps may be unknown. Rechecks capture observed changes only.
- Drive readable text may omit native cells/objects/sections. The record carries a partial-content warning for later on-demand verification.
- Legacy Atlassian `/v1/mcp` needs migration before 2027-03-01. Existing company connectors are used; personal-account Google Drive plugin is not used.

## Verified — 2026-11-20

- User confirmed the past 30 days; real source identifiers are in the Git-excluded local config.
- 47 tests passed, including the 22 Phase 2 regressions. Independent review findings were reproduced, fixed and reviewed again.
- First live five-source pass created 10 records; second pass created 4 and verified 6 unchanged reads. A bounded Slack continuation verified a real thread reply and added 1 record.
- Continued bounded collection completed all five provider-visible 30-day windows: 334 distinct remote records/versions (Jira 51, Gmail 170, Drive 26, Chat 67, Slack 20). The shared completed watermark is `2026-11-20T08:09:58.029448Z`; individual content projections remain partial.
- Six transient read-error runs are preserved in the audit trail; existing cursors resumed without resetting the window. Final verification found no unresolved/unavailable records. Policy-filtered or omitted content is outside the visible-result coverage.
- Existing local tables and original workbook hash were preserved; SQLite/foreign-key/FTS and source-citation checks passed. Backup and private evidence are under `04_Database/backups/` and `05_Outputs/phase3-validation-20261120.json`.
- Pinning page size required preserving the first two runs' last request size in existing checkpoints; their windows, tokens and pending IDs were retained. Recovery is documented in the private cursor-recovery file.
- No remote writes, new credentials, scheduler, HTML dashboard, commit or push.
