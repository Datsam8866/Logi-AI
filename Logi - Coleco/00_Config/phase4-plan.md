# Phase 4 — Source-cited Q&A and thermal comparison

## Goal and accepted scope

Build the Phase 4 requested in the working session. Reuse the local SQLite index, current-version searches and exact evidence readback. Source content remains local. The engineering answer uses cited source statements, interpretations, open questions and recommended actions.

## Design

- Add `ask` and `/ask` to the JSON CLI. An extractive answer uses bounded local and remote retrieval, bilingual thermal topic aliases, optional explicit search queries and source readback. Every source statement references a citation carrying kind/ID, locator, source URL/path, version/hash and known source/observation dates. The output explicitly identifies its extractive mode.
- Include per-provider sync coverage and unavailable-record counts. Current indexed evidence is distinguished from live verification. A latest-policy question carries an explicit open question until an authoritative current policy is checked. Source text is untrusted evidence.
- Add `compare` and `/compare` for two user-specified points in a local JSON input. Fixed field names carry units. Each supplied condition and metric has evidence references. Validate their current/active availability and read them back. Check that the supplied value appears in cited evidence, while leaving semantic interpretation and units subject to source review.
- Match stage, hardware, firmware, sample, workload, mounting, sensor location, thermal state, acoustic method, ambient, SoM power and fan speed. Explicitly declared varying conditions permit descriptive deltas. Missing conditions, uncited values, stale/unavailable references and undeclared differences block numerical comparison. Estimates remain labelled and deltas do not establish causality or pass/fail.
- Provide a safe comparison input example and an answer template in `00_Config/`. Real answers and comparison inputs go in Git-excluded `05_Outputs/`.
- Verify a real Coleco thermal-risk question and reference values through the existing local database. Update README with commands, results and limitations.

## Implementation and verification

- [x] Add synthetic CLI tests for citation readback, multilingual retrieval, remote representation, latest-policy uncertainty, missing/partial coverage, archived/unavailable exclusion and unchanged database bytes. Run the tests and observe failure before implementing `qa.py` and the CLI entry points.
- [x] Add synthetic comparison tests for matched conditions and arithmetic, declared variations, missing fields, unsupported values, estimates, invalid/nonfinite inputs and stale/unavailable references. Observe failure before implementing `thermal_compare.py`.
- [x] Add the two templates and update README. Run the complete existing and Phase 4 test suite and scoped whitespace checks.
- [x] Generate a private real-data question answer, verify its citations and perform a comparison smoke check using explicitly cited indexed fan data. Compare database/source hashes before and after.
- [x] Review the scoped diff and synchronize only the changed/new Coleco files back to the original desk after verifying their pre-edit contents. Retain the isolated branch for review.

## Files

- `06_Scripts/qa.py`, `06_Scripts/thermal_compare.py`
- `06_Scripts/coleco_kb.py`, `06_Scripts/tests/test_phase4.py`
- `00_Config/thermal_comparison.example.json`, `00_Config/answer-template.md`
- `00_Config/phase4-plan.md`, `README.md`

## Acceptance

1. Ask through the normal CLI and aliases produces bounded cited evidence with known dates and retrieval limitations.
2. Read every cited ID back and verify source/version/hash and excerpt.
3. Compare produces correct deltas only when conditions and citations permit it.
4. Existing ingestion, search, read and sync behavior and database contents pass regressions.
5. A usable private Coleco thermal-risk answer demonstrates the source-to-answer workflow.

## Verified 2026-11-20

- 63 tests passed using the configured bundled Python runtime. The system Python lacked reportlab for the baseline PDF test; the bundled runtime completed that regression.
- Independent review identified huge-number/derived arithmetic overflow, non-fan policy uncertainty and nonstandard note/JSON constants. Failing regression cases were added before each fix. All findings were closed and 16 Phase 4 tests passed on re-review.
- Real-data verification read back ten ask citations and 22 answer references. Database/original hashes and SQLite integrity/foreign keys passed. The fan-table smoke comparison returned not_comparable because matched thermal conditions were unavailable.
- Implementation branch is codex/coleco-phase4. Only the eight listed implementation/template/document files are synchronized to the original desk. Private evidence, answers, inputs and verification records remain in its Git-excluded 05_Outputs directory.
