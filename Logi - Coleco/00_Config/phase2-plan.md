# Phase 2 — Local report ingestion and search

Approved scope: the user's “phase 2 go”; local files only, reuse the existing SQLite database, no remote sync, scheduler, dashboard, or Git publication.

## Design

- `06_Scripts/local_extract.py`: extract source text with page/slide/paragraph/row/cell locators from XLSX, CSV, TSV, TXT, Markdown, DOCX, PPTX and text-based PDF. Preserve cached Excel values and formula metadata; no recalculation or OCR.
- `06_Scripts/kb_store.py`: additive local-source/version/chunk tables and FTS5, plus a compatibility adapter for existing report/cell and user-provided fan tables. Leave existing tables and records intact.
- `06_Scripts/coleco_kb.py`: bounded JSON CLI (`init`, `ingest`, `search`, `read`, `status`). Default database: `04_Database/coleco.sqlite3`; default ingestion folder: `01_Inbox/Manual_Reports`.
- Original files stay in place. First schema migration backs up the existing database. Same source path and hash deduplicate; changed contents retain earlier versions. Failed extraction leaves the previous current version intact.
- Search returns current evidence, source file/hash, import timestamp and exact locator. Legacy fan values remain explicitly attributed to the user-provided table.

## Execution and verification

1. Write CLI acceptance tests in `06_Scripts/tests/test_local_kb.py`; run them before implementation and confirm failure because the CLI is absent.
2. Implement extractors, additive database initialization, atomic ingestion, bounded search and evidence readback.
3. Run fixtures for every supported format, duplicate/version/rollback cases, literal queries, missing/unsupported input, empty/scanned PDFs, original preservation and legacy compatibility.
4. Initialize the real database with backup; re-ingest the existing workbook without rebuilding its cells. Verify search citations and unchanged legacy table counts/content, source hash and integrity.
5. Review the implementation, fix substantive findings, update README and ignore private reports/caches/outputs. Do not commit or push.

## Limits

- PDF extraction uses `pypdf` (available in the bundled Python runtime); the other extractors use Python's standard library.
- Images, charts, embedded objects, DOCX headers/footnotes and PPTX speaker notes are not indexed. Missing PDF page text is reported explicitly.
- Legacy XLS and password-protected inputs are unsupported. Search is lexical/substring retrieval, not semantic Q&A.
- MCP synchronization, deletion detection, remote revisions and daily jobs belong to later phases.

## Verification completed — 2026-11-20

- 22 CLI acceptance tests passed after reproducing and fixing five independent review findings, plus write-failure rollback and long-text retrieval cases.
- Independent follow-up review confirmed the fixes and reported no new substantive issues.
- Real database initialization created a backup; re-ingesting the existing workbook returned `unchanged`. Original file hash, all legacy table contents, saved formula values and source citations were verified.
- SQLite quick check, foreign-key check and new FTS integrity check passed. Detailed local evidence is in the Git-excluded `05_Outputs/phase2-validation-20261120.json`.
- README and privacy exclusions updated. No remote integration, schedule, commit or push was performed.
