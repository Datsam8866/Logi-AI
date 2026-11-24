# Coleco AI Project

Query-first, source-cited thermal engineering knowledge base powered by Codex and authorized MCP connectors.

## Current Status

- Imported the initial Excel test report into the local SQLite index at `04_Database/coleco.sqlite3`.
- The index includes worksheet and cell references, saved formula values, full-text search, and asset metadata. Embedded media and objects remain available in the source workbook.
- The `fan_noise_measurements` table holds user-supplied fan speed (RPM), noise (dBA), and airflow (CFM), with source information for comparison with the workbook.
- Checked the SQLite import, its integrity, and the supplied fan measurements. Built an interactive comparison of the ambient-temperature and SoM-power tradeoffs at a shared acoustic target. The chart and engineering values are in the working session.
- `98_Reference/` and `04_Database/` are excluded from Git.
- Phase 2 local CLI is ready: repeatable report ingestion, source/hash deduplication, retained versions, FTS5 and substring search, and evidence readback with source locators.
- Supports XLSX, CSV, TSV, UTF-8 TXT/Markdown, DOCX, PPTX and text-based PDF. Existing workbook cells and user-provided fan data are reused through a compatibility adapter.
- The first schema migration created a database backup. Validation confirmed the original workbook and all existing table contents were unchanged; 22 acceptance tests passed.
- Manual reports, source caches, knowledge and generated outputs are excluded from Git to protect private engineering data.
- Phase 3 connects Jira, Gmail, Google Drive, Google Chat and public Slack through the existing LogiQ MCP connections. No credentials are copied into this project.
- The user-selected 30-day provider-visible backfill is complete: 334 remote records/versions (Jira 51, Gmail 170, Drive 26, Chat 67, Slack 20). Repeat reads did not duplicate versions.
- Six transient read-error runs were retained in the audit trail and recovered by resuming existing checkpoints; no records remain unavailable/unverified after final verification.
- Stable IDs, source revisions/observed hashes, availability, scope memberships, pending IDs, fixed page sizes, checkpoints and sync-run logs are stored in the existing SQLite database.
- The expanded 47-test suite passed; independent review and real source-citation, legacy-data preservation and FTS integrity checks passed.
- Phase 4 adds `ask`/`/ask` source-cited extractive answers with bilingual thermal retrieval, dates, readback and per-provider coverage. Codex uses `00_Config/answer-template.md` to synthesize the engineering answer.
- `compare`/`/compare` checks two cited points, measurement conditions, declared variations and literal source values before calculating deltas. Estimates, missing evidence, archived/unavailable sources and conflicting conditions remain explicit.
- Phase 4 verification passed 63 tests (47 regressions and 16 new acceptance tests). Independent review issues were reproduced and resolved. Ten real ask citations and 22 answer references were read back; SQLite and original workbook hashes were unchanged. The real fan-table comparison correctly reported missing thermal conditions.

- Local burn-in validation exercised both Tkinter fitting tools on measured data. The denser log produced fits in both tools. The sparsely sampled log fitted in A1 with a manual start and could not use A2 automatic onset detection.

## Local Commands

Run from this project folder with Python 3.10 or newer. PDF extraction needs `pypdf`; the full test suite also needs `reportlab`. Both were verified with Codex's bundled Python runtime.

```powershell
python -B 06_Scripts/coleco_kb.py init
python -B 06_Scripts/coleco_kb.py ingest
python -B 06_Scripts/coleco_kb.py search "Burn Out" --limit 5
python -B 06_Scripts/coleco_kb.py status
python -B 06_Scripts/coleco_kb.py ask "Coleco 目前有哪些熱風險？" --limit 6
python -B 06_Scripts/coleco_kb.py /ask "最新風扇策略為何？" --query "fan" --query "control"
python -B 06_Scripts/coleco_kb.py compare 05_Outputs/thermal-comparison.local.json
python -B 06_Scripts/coleco_kb.py sync
python -B 06_Scripts/coleco_kb.py sync --source jira
python -B -m unittest discover -s 06_Scripts/tests -v
```

- `ingest` reads `01_Inbox/Manual_Reports/` by default; explicit file or directory paths are also accepted. Originals remain in place.
- `search` returns `kind`, `id`, source path, SHA-256, import date and a page/slide/paragraph/row/cell locator. Only current indexed versions are searched.
- Use `read KIND ID` with the values returned by search. `--max-chars` defaults to 8000; `--offset` reads later text. Oversized structured details are explicitly omitted, not silently shortened.
- Put `--db PATH` before the command to select another local database. Read-only commands never create a database.
- Backups are in `04_Database/backups/`; the private verification record is `05_Outputs/phase2-validation-20261120.json`. Design and verification scope are in `00_Config/phase2-plan.md`.

## Source-cited Q&A and comparison

- `ask` reads current indexed evidence in a consistent read-only snapshot. It returns source statements, citation IDs, source/version/hash locators, known dates, interpretation guidance, open questions and coverage. It uses keyword/topic retrieval; each excerpt still needs relevance and authority review. `--query` overrides automatic topic queries (up to eight); `--limit` is 1–12 and `--max-chars` is 1–4000 per excerpt.
- Use the answer template for Codex synthesis, keeping measured results, requirements, proposals, estimates and interpretations identifiable. Every consequential claim needs readback. Policy questions explicitly require current approval/version/scope review; conflicting statements retain both dates. Source text is treated as untrusted evidence.
- Copy `00_Config/thermal_comparison.example.json` to `05_Outputs/thermal-comparison.local.json`. Fill two points and per-field `citations` from `search`/`read`, with `basis` set to `measured` or `estimate`. Null fields represent unknown conditions. Field names carry fixed units (°C, W, RPM, dBA, CFM).
- Comparison checks stage, hardware revision, firmware, sample, workload, mounting, sensor, steady state, noise method, ambient, SoM power and fan speed. Declare allowed changes in `varying_conditions`. Missing conditions/citations, unsupported values, archived/unavailable evidence or undeclared changes produce `not_comparable` and empty deltas.
- Literal source support confirms that a value appears in saved evidence; matching the correct measurement column, unit, sensor and protocol still requires source review. Local original files and live remote sources are not verified by the CLI. Differences are second minus first; CPU-to-ambient ΔT is CPU DTS minus ambient. `comparable` does not establish causality or measurement acceptance.
- Phase 4 design and acceptance are in `00_Config/phase4-plan.md`. Private example answer and verification are in `05_Outputs/phase4-thermal-risk-answer-20261120.md` and `05_Outputs/phase4-validation-20261120.json`.

## Five-source Sync

- `sync` reuses the installed LogiQ CLI and its existing authenticated MCP connections. Configure source scopes in the Git-excluded `00_Config/source_scopes.local.json`; `source_scopes.example.json` is a safe template.
- First collection covers the user-selected past 30 days. Each run normalizes at most 2 detailed records per provider (10 across all five); discovery pages are small and their size stays fixed within the window.
- Run `sync` again to continue pending IDs/pages. Only a completed provider-visible window advances its watermark; `status.remote_sync.checkpoints` shows completion and remaining pagination without exposing cursor tokens.
- Later runs reserve part of the batch for rotating known-record rechecks. Jira/Drive can search modification times; email/chat/Slack discovery primarily uses creation times, so older edits and access changes are observed only when rechecked.
- Record states preserve cached history on deletion, inaccessibility or failed verification. Search returns active current versions; `read remote ID` can inspect an archived or unavailable version with explicit flags.
- Source URLs/IDs, created/updated timestamps, observation time and known revision tags accompany evidence. Query windows control discovery; fetched content is the source's current projection at observation time, not an exact historical reconstruction.
- Gmail security/DLP omissions are recorded as conservative reported lower bounds; unavailable policy-filtered items are not bypassed. Missing omission counts do not prove that no content was filtered.
- Connector projections are marked partial: Jira comments/attachments, email attachments/HTML-only content, Drive cells/sections/objects and chat/Slack context may be omitted. Consequential facts still need original-source verification.
- `--source` limits the run to one configured provider. Configuration changes create another scope checkpoint; lookback applies to the first window, while existing unfinished windows resume in place.
- Phase 3 verification: `05_Outputs/phase3-validation-20261120.json`; design: `00_Config/phase3-plan.md`. All source content and operational records stay local and Git-excluded.
- All five completed watermarks are `2026-11-20T08:09:58.029448Z` (2026-11-20 16:09:58 Asia/Taipei). The completed window starts 30 days earlier. Later `sync` runs collect the next incremental window with the configured overlap.

## Next Action

- Use Phase 4 source-cited Q&A for engineering questions; complete point conditions and measurement-specific citations before comparing operating points.
- Run manual `sync` when new source evidence is needed; Phase 5 will configure opt-in daily scheduling after its time and date scope are confirmed.
- Validate both estimated operating points in Free Standing Burn Out. Record steady-state peak CPU DTS, whole-system noise, fan speed, ambient temperature, and measured SoM input power.

- For sparse burn-in logs, verify the workload start and initial temperature from the test record before running A2 with manual settings.

## Open Issues

- The chart uses linear interpolation. The two target operating points still need matched measurements, and the report does not provide a comparable SoM power sweep.
- Manual five-source synchronization is available; Phase 5 daily scheduling awaits the chosen time and date scope.
- `ask` returns extractive source statements; Codex performs engineering synthesis using the template. It does not automatically resolve source conflicts or approve the latest policy. Comparison checks literal source values, so semantic interpretation and unit/condition mapping require source review.
- Extraction indexes text only. No OCR, embedded-image/chart/object extraction, or Excel formula recalculation; legacy XLS and encrypted inputs are unsupported. CSV/TSV use the first record as headers; row locators refer to record numbers.
- If an original changes in place, stored text and hashes preserve earlier evidence, while its file link points to the current file at that path. Local file removal is not detected automatically; remote deletion/access checks are bounded, not immediate or exhaustive.
- Slack currently covers configured public Coleco channels. Private channels/DMs require an explicitly authorized scope. Atlassian's legacy endpoint needs migration before 2027-03-01.

## Last Updated

- 2026-11-25 (Asia/Taipei)

## Session Handoff

- Phase 4 source-cited Q&A and comparison are available. See the private example answer and validation record for real-data coverage and remaining measurement gaps. Daily scheduling belongs to Phase 5.
- Code delivery branch: `codex/coleco-handoff`. The working desk retains its local database, reports, actual source configuration, backups and validation records.
- The parent working desk may be on another project's branch. Compare Coleco files against its delivery branch and isolate commits before publishing; do not push sibling-project history or private data.

## Folders
- `00_Config/` — connector mapping, project identifiers, safe settings (no credentials)
- `01_Inbox/Manual_Reports/` — user-added reports, unchanged originals
- `02_Sources/{Jira,Gmail,Google_Drive,Google_Chat,Slack}/` — private source metadata; operational state lives in SQLite
- `03_Knowledge/` — curated, source-cited project notes by domain
- `04_Database/` — SQLite knowledge index, FTS and sync checkpoints
- `05_Outputs/` — generated reports, technical analysis and meeting briefs
- `06_Scripts/` — ingestion, synchronization, indexing and query scripts
- `98_Reference/` — templates, terminology and baseline documents
- `99_Archive/` — superseded local outputs and snapshots

## Start
1. Open this folder in Codex.
2. If available locally, give Codex the contents of `COLECO_CODEX_PROMPT.md`.
3. Let Codex audit available connectors and confirm access before syncing.
4. Drop reports into `01_Inbox/Manual_Reports/`.
5. Run the local commands above, or ask Codex to ingest/search local reports.

## Security
Do not put OAuth tokens, API keys, passwords or unrestricted private email exports in this folder. Follow employer security policies for storage and AI processing.
