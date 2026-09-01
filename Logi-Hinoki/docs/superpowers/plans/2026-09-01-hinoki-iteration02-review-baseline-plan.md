# Hinoki Iteration 02 Review Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a source-traceable Wave 1 candidate workbook and a rebuildable preliminary Iteration 02 FreeCAD file for panel/touch, camera/shutter, and stand/VESA review.

**Architecture:** Keep researched facts in a small JSON source-of-truth, generate the review workbook from those facts with formula-driven scoring, and build the CAD from an explicit review-baseline parameter table. Verified market geometry is labeled `Verified`; unresolved shutter, integrated-product decomposition, and custom stand geometry remain visible assumptions or blockers.

**Tech Stack:** Python `unittest`, FreeCAD 1.1 Python/Part, JSON, Node.js with `@oai/artifact-tool`, Markdown.

---

## File Structure

- Create `data/iteration-02/component_candidates.json`: reviewed candidate facts, scores, source URLs, and access dates.
- Create `scripts/build_iteration02_candidates.mjs`: deterministic workbook generator.
- Create `outputs/hinoki-iteration02-review/Hinoki_Iteration02_Component_Candidates.xlsx`: review workbook.
- Create `tests/test_hinoki_iteration02.py`: acceptance checks for CAD objects, verified dimensions, traceability, and review report.
- Create `cad/iteration-02/build_hinoki_iteration02.py`: preliminary review-baseline FreeCAD builder.
- Create `cad/iteration-02/review_iteration02.py`: geometry, source-status, and mass-headroom checks.
- Create `cad/iteration-02/Hinoki_Concept_CAD_Iteration02_Review.FCStd`: generated review CAD.
- Create `cad/iteration-02/Hinoki_Iteration02_CAD_Review.json`: generated machine-readable review.
- Create `docs/reviews/2026-09-01-hinoki-iteration02-preliminary-review.md`: decision summary and blockers.
- Modify `README.md`: add Iteration 02 review artifact paths and current limitations.

### Task 1: Freeze source-backed candidate data

**Files:**
- Create: `data/iteration-02/component_candidates.json`

- [ ] **Step 1: Record exact candidate facts and source status**

Use these CAD-driving candidates and facts; do not infer missing values:

```json
{
  "access_date": "2026-09-01",
  "candidates": [
    {"subsystem":"Panel / Touch","manufacturer":"One World Touch","part_number":"LM-3237-26B-4K","width_mm":750.4,"height_mm":452.7,"depth_mm":56.5,"mass_kg":14.0,"resolution":"3840 x 2160","touch":"10-point PCAP","vesa":"200 x 200 mm, M4","status":"Preferred","verification":"Verified review proxy","source_url":"https://oneworldtouch.com/wp-content/mediafiles/2025/02/LM-3237-26B-4K-Data-Sheet.pdf"},
    {"subsystem":"Panel / Touch","manufacturer":"AccuView","part_number":"OFU320UPUA","width_mm":824.0,"height_mm":524.0,"depth_mm":77.0,"resolution":"3840 x 2160","touch":"PCAP","vesa":"200 x 200 mm","status":"Reject","verification":"Verified external envelope","source_url":"https://accuview.com/product/ofu320upua-32-inch-4k-ultra-hd-open-frame-projected-capacitive-pcap-touch-monitor/"},
    {"subsystem":"Panel / Touch","manufacturer":"Elo","part_number":"E103164 / 3204L","width_mm":763.7,"height_mm":458.1,"depth_mm":49.6,"mass_kg":10.9,"resolution":"1920 x 1080","touch":"40-touch PCAP","vesa":"400 x 400 mm, M6","status":"Reject","verification":"Verified hard mismatches","source_url":"https://www.elotouch.com/touchscreen-signage-3204l.html"},
    {"subsystem":"Camera / Shutter","manufacturer":"Leopard Imaging","part_number":"LI-IMX477-MIPI-140H","width_mm":38.0,"height_mm":38.0,"depth_mm":25.78,"mass_kg":0.016,"resolution":"4056 x 3040","horizontal_fov_deg":140.0,"status":"Preferred","verification":"Verified module; shutter excluded","source_url":"https://leopardimaging.com/wp-content/uploads/2024/04/LI-IMX477-MIPI-140H_Datasheet.pdf"},
    {"subsystem":"Camera / Shutter","manufacturer":"Leopard Imaging","part_number":"LI-IMX779-MIPI-140H","resolution":"3856 x 2176","horizontal_fov_deg":140.0,"mass_kg":0.018,"status":"Alternate","verification":"Mechanical drawing requires final datum check; shutter excluded","source_url":"https://leopardimaging.com/wp-content/uploads/2025/08/LI-IMX779-MIPI-140H_Datasheet.pdf"},
    {"subsystem":"Camera / Shutter","manufacturer":"Arducam","part_number":"B0670 + LK006 140H lens","width_mm":24.0,"height_mm":25.0,"depth_mm":16.5,"horizontal_fov_deg":140.0,"status":"Hold","verification":"Board verified; full-resolution frame rate below 4K30; lens depth separate","source_url":"https://www.arducam.com/arducam-imx500-ai-mipi-camera-module-for-raspberry-pi.html"},
    {"subsystem":"Stand / VESA","manufacturer":"Ergotron","part_number":"45-475-224 HX Desk Monitor Arm","mass_capacity_min_kg":9.1,"mass_capacity_max_kg":19.1,"lift_mm":292.0,"tilt_forward_deg":-5.0,"tilt_rearward_deg":70.0,"vesa":"75x75, 100x100, 200x100, 200x200","status":"Preferred","verification":"Verified mechanism benchmark, not Hinoki industrial design","source_url":"https://www.ergotron.com/en-ca/products/product-details/45-475"},
    {"subsystem":"Stand / VESA","manufacturer":"Humanscale","part_number":"M8 Pro / M81BBTBC","mass_capacity_min_kg":4.1,"mass_capacity_max_kg":22.7,"tilt_forward_deg":-15.0,"tilt_rearward_deg":80.0,"vesa":"100 x 100 mm","status":"Alternate","verification":"Verified capacity; 200 mm adapter and CAD envelope unresolved","source_url":"https://shop.humanscale.com/products/m8-pro-single-monitor-arm"},
    {"subsystem":"Stand / VESA","manufacturer":"CBS","part_number":"Flo X","mass_capacity_min_kg":3.0,"mass_capacity_max_kg":18.0,"vesa":"75 x 75 / 100 x 100 mm","status":"Hold","verification":"Verified capacity; 200 mm adapter and CAD envelope unresolved","source_url":"https://www.colebrookbossonsaunders.com/en-au/products/flo-x"},
    {"subsystem":"Stand / VESA","manufacturer":"Ergotron","part_number":"45-682-292 LX Pro Desk Arm","mass_capacity_min_kg":1.8,"mass_capacity_max_kg":10.0,"lift_mm":330.0,"vesa":"75 x 75 / 100 x 100 mm","status":"Reject","verification":"Verified capacity below 14 kg display proxy mass","source_url":"https://media.ergotron.com/reserved/resources/specs-lx-pro-series-ea-orig.pdf"}
  ]
}
```

- [ ] **Step 2: Validate JSON syntax**

Run: `python -m json.tool data/iteration-02/component_candidates.json > $null`

Expected: exit code 0.

- [ ] **Step 3: Commit candidate source data**

```powershell
git add data/iteration-02/component_candidates.json
git commit -m "data: add Hinoki iteration 02 CAD-driving candidates"
```

### Task 2: Build and verify the candidate workbook

**Files:**
- Create: `scripts/build_iteration02_candidates.mjs`
- Create: `outputs/hinoki-iteration02-review/Hinoki_Iteration02_Component_Candidates.xlsx`

- [ ] **Step 1: Implement the deterministic workbook builder**

Create six sheets: `Summary`, `Candidates`, `Requirements`, `CAD Envelopes`, `Sources`, and `Scoring Guide`. `Candidates` must expose 0–5 inputs for specification, CAD, interface, thermal/power, documentation, and availability, then calculate weighted score with:

```excel
=SUMPRODUCT(Q2:V2,'Scoring Guide'!$B$2:$B$7)/5*100
```

Use bounded ranges, data validation for recommendation/status fields, explicit source URL columns, frozen headers, and conditional formatting for status and score. The `Summary` sheet must show the preferred panel proxy, camera module, stand benchmark, and the three blockers: integrated-product decomposition, shutter mechanism, and custom stand/stability.

- [ ] **Step 2: Run the required artifact operation marker once**

Run with the bundled Node executable:

```powershell
& $node container_tools/mark_artifact_operation_started.mjs --operation-kind create --expected-output-count 1 --output-format xlsx
```

Expected: exit code 0.

- [ ] **Step 3: Generate, inspect, and render every sheet**

Run: `& $node scripts/build_iteration02_candidates.mjs`

Expected: workbook saved under `outputs/hinoki-iteration02-review/`; key-range inspection contains formulas and no formula-error scan matches; six PNG verification renders are created in a temporary verification directory.

- [ ] **Step 4: Commit workbook source and output**

```powershell
git add scripts/build_iteration02_candidates.mjs outputs/hinoki-iteration02-review/Hinoki_Iteration02_Component_Candidates.xlsx
git commit -m "feat: add Hinoki iteration 02 candidate workbook"
```

### Task 3: Create Iteration 02 CAD acceptance test first

**Files:**
- Create: `tests/test_hinoki_iteration02.py`
- Test: `tests/test_hinoki_iteration02.py`

- [ ] **Step 1: Write the failing acceptance test**

The test must require `Iteration02_Metadata`, `Review_Parameters`, `Head_Envelope`, `OWT_LM3237_Display_Proxy`, `LI_IMX477_140H_Camera`, `Privacy_Shutter_Assumption`, `VESA_200x200_Interface`, `Ergotron_HX_Mechanism_Benchmark`, `Low_Forward_Envelope`, and `High_Rearward_Envelope`. Assert display dimensions `750.4 × 56.5 × 452.7 mm`, camera dimensions `38 × 25.78 × 38 mm`, horizontal FOV `140°`, VESA pattern `200 mm`, verified/assumed classifications, and generated review status `PassWithOpenRisks`.

- [ ] **Step 2: Run the test and verify RED**

Run: `python -m unittest tests.test_hinoki_iteration02 -v`

Expected: FAIL because `cad/iteration-02/build_hinoki_iteration02.py` does not exist.

- [ ] **Step 3: Commit the failing test**

```powershell
git add tests/test_hinoki_iteration02.py
git commit -m "test: define Hinoki iteration 02 review CAD acceptance"
```

### Task 4: Implement the minimum review CAD and geometry report

**Files:**
- Create: `cad/iteration-02/build_hinoki_iteration02.py`
- Create: `cad/iteration-02/review_iteration02.py`
- Generate: `cad/iteration-02/Hinoki_Concept_CAD_Iteration02_Review.FCStd`
- Generate: `cad/iteration-02/Hinoki_Iteration02_CAD_Review.json`

- [ ] **Step 1: Build only the review-baseline geometry**

Use the Iteration 01 coordinate system. Keep the `760 × 80 × 540 mm` head envelope classified `Assumed`. Place the verified `750.4 × 56.5 × 452.7 mm` LM-3237 proxy at the head front/bottom, leaving `4.8 mm` side margin and `87.3 mm` top zone. Place the verified `38 × 25.78 × 38 mm` LI-IMX477 module at the top centre with `140°` HFOV. Keep a separate `52 × 4 × 30 mm` privacy-shutter package classified `Assumed`. Model a `200 × 200 mm` VESA interface and label the Ergotron HX as a mechanism benchmark; do not reproduce vendor industrial design from incomplete web geometry.

- [ ] **Step 2: Implement review checks**

The report must calculate containment, side/top margin, display depth reserve, camera FOV, preferred stand capacity headroom (`19.1 - 14.0 = 5.1 kg` before Hinoki AV/compute additions), and open-risk flags. Return `PassWithOpenRisks` only when verified geometry is contained and FOV is 134–140°, while all three open-risk flags remain visible.

- [ ] **Step 3: Run the test and verify GREEN**

Run: `python -m unittest tests.test_hinoki_iteration02 -v`

Expected: `1 test`, `OK`.

- [ ] **Step 4: Run Iteration 01 regression**

Run: `python -m unittest tests.test_hinoki_iteration01 tests.test_hinoki_iteration02 -v`

Expected: `2 tests`, `OK`.

- [ ] **Step 5: Commit CAD implementation and generated review artifacts**

```powershell
git add cad/iteration-02 tests/test_hinoki_iteration02.py
git commit -m "feat: add Hinoki iteration 02 preliminary review CAD"
```

### Task 5: Document the review decision and handoff

**Files:**
- Create: `docs/reviews/2026-09-01-hinoki-iteration02-preliminary-review.md`
- Modify: `README.md`

- [ ] **Step 1: Write the decision summary**

Document that LM-3237 is a full-display review proxy rather than a bare panel/touch stack; LI-IMX477 is the preferred camera module baseline but has no integrated shutter; Ergotron HX proves a viable capacity/motion class and VESA 200 support but is not the intended Hinoki industrial design. Record the `4.8 mm` side margin, `23.5 mm` depth reserve, `87.3 mm` upper zone, and `5.1 kg` pre-AV/compute mass headroom.

- [ ] **Step 2: Update README current status and artifact links**

Add the workbook, CAD, review JSON, and review Markdown paths. Preserve the statement that the model is not release geometry and no STEP has been exported.

- [ ] **Step 3: Run fresh final verification**

```powershell
python -m json.tool data/iteration-02/component_candidates.json > $null
python -m unittest tests.test_hinoki_iteration01 tests.test_hinoki_iteration02 -v
git status --short
git diff --check
```

Expected: JSON valid, two tests pass, no whitespace errors, and only intended generated/verification files remain visible.

- [ ] **Step 4: Commit documentation**

```powershell
git add README.md docs/reviews/2026-09-01-hinoki-iteration02-preliminary-review.md
git commit -m "docs: record Hinoki iteration 02 preliminary review"
```

