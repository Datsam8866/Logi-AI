# Coleco AI Project

Query-first, source-cited thermal engineering knowledge base powered by Codex and authorized MCP connectors.

## Current Status

- Imported the initial Excel test report into the local SQLite index at `04_Database/coleco.sqlite3`.
- The index includes worksheet and cell references, saved formula values, full-text search, and asset metadata. Embedded media and objects remain available in the source workbook.
- The `fan_noise_measurements` table holds user-supplied fan speed (RPM), noise (dBA), and airflow (CFM), with source information for comparison with the workbook.
- Checked the SQLite import, its integrity, and the supplied fan measurements. Built an interactive comparison of the ambient-temperature and SoM-power tradeoffs at a shared acoustic target. The chart and engineering values are in the working session.
- `98_Reference/` and `04_Database/` are excluded from Git.

## Next Action

- Validate both estimated operating points in Free Standing Burn Out. Record steady-state peak CPU DTS, whole-system noise, fan speed, ambient temperature, and measured SoM input power.

## Open Issues

- The chart uses linear interpolation. The two target operating points still need matched measurements, and the report does not provide a comparable SoM power sweep.

## Last Updated

- 2026-11-19 (Asia/Taipei)

## Folders
- `00_Config/` — connector mapping, project identifiers, safe settings (no credentials)
- `01_Inbox/Manual_Reports/` — user-added reports, unchanged originals
- `02_Sources/{Jira,Gmail,Google_Drive,Google_Chat}/` — source metadata, sync manifests; avoid uncontrolled duplication
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
5. Ask `/ingest`, then `/ask <question>` once the implementation is ready.

## Security
Do not put OAuth tokens, API keys, passwords or unrestricted private email exports in this folder. Follow employer security policies for storage and AI processing.
