# Hinoki Workbook Freeze and Space Claim Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update the existing Hinoki workbook with a traceable approved-parameter freeze, architecture-linked assumptions, and a formula-checked internal space claim; no CAD geometry is created.

**Architecture:** Preserve the existing `Master Parameter Table` and `Assumption Log` as source-of-truth sheets. Add `Frozen Baseline` as a controlled selection of direct requirements / source-confirmed Known records, and add `Internal Space Claim` as a bounded-box package register using the approved 760 × 540 × 80 mm head envelope. Put all newly introduced numeric package reservations in the Assumption Log and reference them from the new sheets.

**Tech Stack:** Existing `.xlsx` workbook, Node.js, `@oai/artifact-tool` 2.8.6+, formula inspection, workbook render verification.

---

## File Structure

- Modify: `C:/Users/skuan1/Desktop/Logi AI/Logi-Hinoki/Hinoki_Master_Parameters_and_Assumption_Log.xlsx` — authoritative workbook; preserve its existing two sheets and styles.
- Create: `C:/Users/skuan1/Desktop/Logi AI/Logi-Hinoki/tools/update_hinoki_architecture_workbook.mjs` — repeatable, auditable workbook-edit builder. The script imports the authoritative workbook, appends assumptions, adds/refreshes the two controlled sheets, validates content, renders previews, and exports the revised workbook.
- Create: `C:/Users/skuan1/Desktop/Logi AI/Logi-Hinoki/docs/superpowers/plans/2026-09-01-hinoki-workbook-freeze-and-space-claim-plan.md` — this approved execution plan.

### Task 1: Establish source snapshot and architecture-linked assumptions

**Files:**
- Modify: `C:/Users/skuan1/Desktop/Logi AI/Logi-Hinoki/Hinoki_Master_Parameters_and_Assumption_Log.xlsx` — `Assumption Log` rows after A-012 only.
- Create: `C:/Users/skuan1/Desktop/Logi AI/Logi-Hinoki/tools/update_hinoki_architecture_workbook.mjs`
- Test: `C:/Users/skuan1/AppData/Local/Temp/hinoki-space-claim-plan/verify_hinoki_workbook.mjs`

- [ ] **Step 1: Record the exact new assumptions before writing a space-claim number.**

Append rows A-013 through A-021 with Status `Open` and CAD-release authority explicitly denied:

```text
A-013  Architecture  Head concept envelope: 760 W × 540 H × 80 D  mm
A-014  Panel         Display/touch stack: 730 W × 420 H × 18 D      mm
A-015  AV / Acoustic Upper AV/acoustic-bar height: 85               mm
A-016  Camera        Camera + captive-shutter package: 120×55×42   mm
A-017  Audio         Each upper speaker enclosure: 170×55×40       mm
A-018  Lighting      Each front-light module: 55×12×15             mm
A-019  Compute       QC7790 compute + heat-spreader: 200×120×32    mm
A-020  Interface     Head USB-C interface/protection board: 120×75×24 mm
A-021  Interface     Rear I/O board: 220×60×24                     mm
```

For every row, cite the mechanical-architecture specification, state why its reservation is needed, affected MP IDs, failure impact, closure evidence, owner, and low/medium confidence. Link VESA reinforcement to existing A-010 rather than duplicating a 100 × 100 mm VESA assumption.

- [ ] **Step 2: Verify the new assumptions are complete but do not supersede Known values.**

Run the workbook builder in inspection mode and assert the following in its JSON output:

```js
const requiredAssumptions = ["A-013", "A-014", "A-015", "A-016", "A-017", "A-018", "A-019", "A-020", "A-021"];
const allOpen = assumptionRows.every((row) => row.status === "Open");
const noFrozenAssumptions = assumptionRows.every((row) => row.status !== "Frozen");
assert.deepEqual(newAssumptionIds, requiredAssumptions);
assert.ok(allOpen && noFrozenAssumptions);
```

Run:

```powershell
& '<bundled-node>\node.exe' 'C:\Users\skuan1\Desktop\Logi AI\Logi-Hinoki\tools\update_hinoki_architecture_workbook.mjs' --inspect
```

Expected: 21 assumptions total, A-013 through A-021 present, all new rows `Open`, and no formula-error strings.

- [ ] **Step 3: Commit the incremental source-of-truth update.**

```powershell
git -C 'C:\Users\skuan1\Desktop\Logi AI' add -- 'Logi-Hinoki/Hinoki_Master_Parameters_and_Assumption_Log.xlsx' 'Logi-Hinoki/tools/update_hinoki_architecture_workbook.mjs'
git -C 'C:\Users\skuan1\Desktop\Logi AI' commit -m 'docs: add Hinoki architecture assumptions'
```

### Task 2: Build the controlled Frozen Baseline sheet

**Files:**
- Modify: `C:/Users/skuan1/Desktop/Logi AI/Logi-Hinoki/Hinoki_Master_Parameters_and_Assumption_Log.xlsx` — new `Frozen Baseline` sheet.
- Modify: `C:/Users/skuan1/Desktop/Logi AI/Logi-Hinoki/tools/update_hinoki_architecture_workbook.mjs`
- Test: `C:/Users/skuan1/AppData/Local/Temp/hinoki-space-claim-plan/verify_hinoki_workbook.mjs`

- [ ] **Step 1: Define the controlled table schema and freeze selection.**

Create `Frozen Baseline` with columns:

```text
Freeze ID | Master Parameter ID | Category | Approved Parameter | Frozen Value | Units |
Basis | Source / Trace | Status | CAD-driving? | Change-Control Note
```

Select only direct product requirements from Known MP records: MP-001, MP-002, MP-008, MP-011, MP-020, MP-022, MP-024, MP-025, MP-027, MP-033 through MP-038, MP-040 through MP-042, MP-045, MP-048, and MP-077. Include a separate `Conditional` row for ambient-light-sensor provision, citing A-007 and the requirement qualifier. Exclude all Dixie reference dimensions, Dixie thermal inputs, and every non-Known value.

- [ ] **Step 2: Implement freeze selection from an explicit ID list, not by formatting or a free-text filter.**

Use this selection contract in the builder:

```js
const frozenMpIds = new Set([
  "MP-001", "MP-002", "MP-008", "MP-011", "MP-020", "MP-022", "MP-024", "MP-025",
  "MP-027", "MP-033", "MP-034", "MP-035", "MP-036", "MP-037", "MP-038", "MP-040",
  "MP-041", "MP-042", "MP-045", "MP-048", "MP-077",
]);
const frozenRows = masterRows.filter((row) => frozenMpIds.has(row.id) && row.classification === "Known");
assert.equal(frozenRows.length, frozenMpIds.size);
```

Style the title and headers to match the existing workbook, freeze the header row, wrap explanatory text, and use a distinct fill for `Frozen` and `Conditional` status. Do not change the existing Master Parameter Table’s classifications.

- [ ] **Step 3: Verify freeze integrity and traceability.**

Run:

```powershell
& '<bundled-node>\node.exe' 'C:\Users\skuan1\Desktop\Logi AI\Logi-Hinoki\tools\update_hinoki_architecture_workbook.mjs' --verify-freeze
```

Expected checks:

```text
Frozen Baseline contains exactly 21 Frozen MP rows plus one Conditional ambient-light row.
Every Frozen row has a Known source classification and a Master Parameter ID.
No non-Known classification or Dixie-only reference dimension appears as Frozen.
```

- [ ] **Step 4: Commit the controlled baseline.**

```powershell
git -C 'C:\Users\skuan1\Desktop\Logi AI' add -- 'Logi-Hinoki/Hinoki_Master_Parameters_and_Assumption_Log.xlsx' 'Logi-Hinoki/tools/update_hinoki_architecture_workbook.mjs'
git -C 'C:\Users\skuan1\Desktop\Logi AI' commit -m 'docs: add controlled Hinoki frozen baseline'
```

### Task 3: Build and validate the Internal Space Claim sheet

**Files:**
- Modify: `C:/Users/skuan1/Desktop/Logi AI/Logi-Hinoki/Hinoki_Master_Parameters_and_Assumption_Log.xlsx` — new `Internal Space Claim` sheet.
- Modify: `C:/Users/skuan1/Desktop/Logi AI/Logi-Hinoki/tools/update_hinoki_architecture_workbook.mjs`
- Test: `C:/Users/skuan1/AppData/Local/Temp/hinoki-space-claim-plan/verify_hinoki_workbook.mjs`

- [ ] **Step 1: Create a datum-controlled package register.**

Create columns:

```text
Claim ID | Zone | Claim Type | Module | Qty | Center X | Center Y | Center Z |
W | H | D | Unit Volume | Total Volume | Containment | Clearance | Source MP IDs |
Assumption IDs | CAD-driving? | Notes
```

State at the top: X is left/right, Y is bottom/top, Z is front/rear, all positions use head center as datum, and positive Z is rearward. Set head envelope dimensions in visible input cells (760, 540, 80 mm) from A-013. Add claims for display/touch stack, upper AV bar, camera/shutter, two speaker enclosures, two front-light modules, compute/heat-spreader, USB-C interface, rear I/O board, VESA reinforcement, radar keep-out, ambient-light-sensor keep-out, antenna keep-outs, upper/lower vent keep-outs, and cable/service keep-out.

- [ ] **Step 2: Use formulas for volume and containment; use explicit geometric checks for hard-package intersections.**

Use formulas in every claim row:

```excel
Unit Volume = W * H * D
Total Volume = Unit Volume * Qty
Containment = IF(AND(ABS(Center X)+W/2<=Envelope W/2, ABS(Center Y)+H/2<=Envelope H/2, Center Z-D/2>=0, Center Z+D/2<=Envelope D), "Pass", "Fail")
```

For hard packages, calculate pairwise three-axis overlap in a visible `Space Claim Checks` block using the strict intersection condition:

```js
const overlap = (a, b) =>
  Math.abs(a.x - b.x) < (a.w + b.w) / 2 &&
  Math.abs(a.y - b.y) < (a.h + b.h) / 2 &&
  Math.abs(a.z - b.z) < (a.d + b.d) / 2;
```

Report total claimed rear-cavity volume, residual rear-cavity reserve volume, and reserve ratio. Flag reserve below 25% as `Review`, not `Fail`. Apply a 5 mm clearance allocation for unrelated hard packages and mark all positions as `Assumed` until a later CAD release.

- [ ] **Step 3: Verify the numerical claim and visually inspect every sheet.**

Run:

```powershell
node 'C:\Users\skuan1\.cache\codex-runtimes\codex-primary-runtime\dependencies\container_tools\mark_artifact_operation_started.mjs' --operation-kind edit --expected-output-count 1 --output-format xlsx
& '<bundled-node>\node.exe' 'C:\Users\skuan1\Desktop\Logi AI\Logi-Hinoki\tools\update_hinoki_architecture_workbook.mjs' --verify --render
```

Expected: all claims contain, hard-package overlap count equals zero, clearance check passes, and all workbook sheets render with legible title, headers, and data without clipping. Scan all populated ranges for `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?`, and `#N/A`.

- [ ] **Step 4: Export and commit the verified workbook.**

```powershell
git -C 'C:\Users\skuan1\Desktop\Logi AI' add -- 'Logi-Hinoki/Hinoki_Master_Parameters_and_Assumption_Log.xlsx' 'Logi-Hinoki/tools/update_hinoki_architecture_workbook.mjs'
git -C 'C:\Users\skuan1\Desktop\Logi AI' commit -m 'docs: add Hinoki internal space claim'
```

## Plan Self-Review

- Spec coverage: Tasks 1–3 cover the approved freeze boundary, top AV/audio arrangement, base-versus-head power partition, serviceable I/O, VESA/stand reservation, thermal boundary, datum definition, space containment, clearance, reserve, and no-CAD restriction.
- Placeholder scan: no execution step defers required content; the only unresolved product facts are intentionally retained as explicit Open assumptions and must not be frozen.
- Consistency: the builder, authoritative workbook, claim datum, A-013 envelope, A-010 VESA candidate, and explicit Frozen MP list use the same names throughout.
