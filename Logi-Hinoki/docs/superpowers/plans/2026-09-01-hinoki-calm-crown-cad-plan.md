# Hinoki Calm Crown CAD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete Calm Crown external concept CAD, publication-ready render set, product-only STP, machine-readable scorecard, and independent agent approval package.

**Architecture:** Create Iteration 03 as a separate FreeCAD document driven by a small immutable parameter module. Separate visible product parts, internal claims, structure, motion references, review/export logic, and rendering so product review never confuses packaging proxies with finished geometry. Export only named physical product leaves and verify them through FreeCAD and CadQuery before agent scoring.

**Tech Stack:** FreeCAD 1.1 Python (`Part`, `Import`, `FreeCADGui`), Python `unittest`, CadQuery 2.8.0 for independent STEP import, JSON review evidence, PNG renders, Git.

---

## File Map

Create:

- `cad/iteration-03/hinoki_calm_crown_parameters.py` — controlled dimensions, object manifests, source/assumption metadata, and score weights.
- `cad/iteration-03/build_hinoki_calm_crown.py` — native FreeCAD construction and saved FCStd.
- `cad/iteration-03/review_hinoki_calm_crown.py` — geometry, requirement, motion, collision, and score evidence.
- `cad/iteration-03/render_hinoki_calm_crown.py` — deterministic product and engineering views.
- `cad/iteration-03/export_hinoki_calm_crown_step.py` — product-only STP export and manifest creation.
- `cad/iteration-03/verify_hinoki_calm_crown_step.py` — FreeCAD re-import parity and finite geometry checks.
- `cad/iteration-03/verify_hinoki_calm_crown_cadquery.py` — independent CadQuery STEP import.
- `tests/test_hinoki_iteration03.py` — acceptance and regression tests.
- `docs/reviews/2026-09-01-hinoki-calm-crown-agent-review.md` — signed reviewer outcomes and score aggregation.

Modify:

- `README.md` — Iteration 03 status, deliverables, commands, score, and risks.

Generated and retained:

- `cad/iteration-03/Hinoki_CalmCrown_Concept.FCStd`
- `cad/iteration-03/Hinoki_CalmCrown_Concept_Review.stp`
- `cad/iteration-03/Hinoki_CalmCrown_Review.json`
- `cad/iteration-03/Hinoki_CalmCrown_Artifact_Manifest.json`
- `cad/iteration-03/Hinoki_CalmCrown_Hero.png`
- `cad/iteration-03/Hinoki_CalmCrown_Rear.png`
- `cad/iteration-03/Hinoki_CalmCrown_Front.png`
- `cad/iteration-03/Hinoki_CalmCrown_Side_Motion.png`
- `cad/iteration-03/Hinoki_CalmCrown_Internal_Overlay.png`

## Task 1: Freeze the Iteration 03 parameter and object contract

**Files:**

- Create: `cad/iteration-03/hinoki_calm_crown_parameters.py`
- Create: `tests/test_hinoki_iteration03.py`

- [ ] **Step 1: Write the failing parameter-contract test**

```python
from pathlib import Path
import importlib.util
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CAD_ROOT = PROJECT_ROOT / "cad" / "iteration-03"
PARAMETERS_FILE = CAD_ROOT / "hinoki_calm_crown_parameters.py"


def load_parameters():
    spec = importlib.util.spec_from_file_location("hinoki_calm_crown_parameters", PARAMETERS_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HinokiIteration03Tests(unittest.TestCase):
    def test_parameter_contract_matches_approved_design(self):
        self.assertTrue(PARAMETERS_FILE.exists())
        p = load_parameters()
        self.assertEqual(p.HEAD, {"width": 742.0, "height": 492.0, "depth": 62.0, "corner_radius": 18.0})
        self.assertEqual(p.CROWN_HEIGHT, 72.0)
        self.assertEqual(p.VESA_PATTERN, 100.0)
        self.assertEqual(p.STAND_MOTION, {"travel": 120.0, "tilt_forward": -5.0, "tilt_rear": 20.0})
        self.assertEqual(p.BASE, {"width": 420.0, "depth": 285.0, "height": 68.0})
        self.assertIn("Front_Glass", p.PRODUCT_EXPORT_OBJECTS)
        self.assertIn("Rear_Service_Cover", p.PRODUCT_EXPORT_OBJECTS)
        self.assertNotIn("Camera_FOV_KeepOut", p.PRODUCT_EXPORT_OBJECTS)
        self.assertAlmostEqual(sum(p.SCORE_WEIGHTS.values()), 1.0)
```

- [ ] **Step 2: Run the test and confirm the expected failure**

Run:

```powershell
python -m unittest tests.test_hinoki_iteration03.HinokiIteration03Tests.test_parameter_contract_matches_approved_design -v
```

Expected: `FAIL` because `hinoki_calm_crown_parameters.py` does not exist.

- [ ] **Step 3: Implement the controlled parameter module**

```python
HEAD = {"width": 742.0, "height": 492.0, "depth": 62.0, "corner_radius": 18.0}
CROWN_HEIGHT = 72.0
ACTIVE_AREA = {"width": 708.4, "height": 398.5}
VESA_PATTERN = 100.0
STAND_MOTION = {"travel": 120.0, "tilt_forward": -5.0, "tilt_rear": 20.0}
BASE = {"width": 420.0, "depth": 285.0, "height": 68.0}
BASE_POWER = {"width": 360.0, "depth": 240.0, "height": 45.0}
BALLAST = {"width": 380.0, "depth": 250.0, "height": 8.0}

PRODUCT_EXPORT_OBJECTS = (
    "Front_Glass", "Display_Mask", "Crown_Shell", "Speaker_Insert_Left",
    "Speaker_Insert_Right", "Camera_Pill", "Camera_Lens_Window", "Shutter_Rail",
    "Shutter_Tab_Open", "Fill_Light_Left", "Fill_Light_Right", "Radar_Window",
    "ALS_Window", "Rear_Shell", "Rear_Service_Cover", "Vent_Insert_Lower",
    "IO_Recess", "Stand_Fixed_Spine", "Stand_Moving_Spine", "Pivot_Pod",
    "VESA_Interface_Cover", "Base_Upper", "Base_Lower", "Foot_Left", "Foot_Right",
)

REQUIRED_VISIBLE_OBJECTS = PRODUCT_EXPORT_OBJECTS + (
    "Mic_Aperture_Left_Outer", "Mic_Aperture_Left_Inner",
    "Mic_Aperture_Right_Inner", "Mic_Aperture_Right_Outer",
)

REQUIRED_INTERNAL_CLAIMS = (
    "Panel_Touch_Claim", "Speaker_Claim_Left", "Speaker_Claim_Right",
    "Camera_ISP_Claim", "QC7790_Claim", "Heat_Spreader_Claim",
    "USB_C_Interface_Claim", "Rear_IO_Board_Claim", "VESA_Reinforcement_Claim",
    "Base_Power_PD_Claim", "Ballast_Claim", "Cable_Loop_Claim",
)

SCORE_WEIGHTS = {
    "external_design_completeness": 0.15,
    "architecture_consistency": 0.20,
    "visual_communication": 0.10,
    "geometry_health": 0.20,
    "step_portability": 0.10,
    "requirement_traceability": 0.15,
    "risk_integrity": 0.10,
}

CONCEPT_SCORE_THRESHOLD = 80.0
MINIMUM_CATEGORY_SCORES = {
    "external_design_completeness": 3,
    "architecture_consistency": 4,
    "visual_communication": 3,
    "geometry_health": 4,
    "step_portability": 4,
    "requirement_traceability": 4,
    "risk_integrity": 3,
}
```

- [ ] **Step 4: Run the contract test and confirm it passes**

Expected: one test passes.

- [ ] **Step 5: Commit the contract**

```powershell
git add -- cad/iteration-03/hinoki_calm_crown_parameters.py tests/test_hinoki_iteration03.py
git commit -m "test: define Hinoki Calm Crown CAD contract"
```

## Task 2: Build the finished head and visible front architecture

**Files:**

- Create: `cad/iteration-03/build_hinoki_calm_crown.py`
- Modify: `tests/test_hinoki_iteration03.py`

- [ ] **Step 1: Add a failing native-CAD structure test**

Add constants for `BUILD_SCRIPT`, `CAD_FILE`, and `FREECAD_CMD`, plus a `run_freecad_script()` helper matching the Iteration 02 test. The test must run the builder and probe these objects:

```python
required = [
    'Visible_ID_Surfaces', 'Structure', 'Internal_Space_Claims', 'Datums_and_Motion',
    'Front_Glass', 'Display_Mask', 'Crown_Shell', 'Speaker_Insert_Left',
    'Speaker_Insert_Right', 'Camera_Pill', 'Camera_Lens_Window', 'Shutter_Rail',
    'Shutter_Tab_Open', 'Fill_Light_Left', 'Fill_Light_Right', 'Radar_Window',
    'ALS_Window'
]
missing = [name for name in required if doc.getObject(name) is None]
assert not missing, 'Missing objects: ' + ', '.join(missing)
assert doc.getObject('Front_Glass').Shape.isValid()
assert doc.getObject('Crown_Shell').Shape.isValid()
assert doc.getObject('Front_Glass').Shape.BoundBox.XLength == 742.0
assert doc.getObject('Front_Glass').Shape.BoundBox.YLength == 492.0
```

- [ ] **Step 2: Run the native-CAD test and observe the missing-builder failure**

Run the single Iteration 03 test. Expected: `FAIL` because the builder is missing.

- [ ] **Step 3: Implement reusable shape and metadata helpers**

Implement:

```python
def rounded_prism_xy(width, height, depth, radius, origin):
    x, y, z = origin
    core_h = Part.makeBox(width - 2 * radius, height, depth, App.Vector(x + radius, y, z))
    core_v = Part.makeBox(width, height - 2 * radius, depth, App.Vector(x, y + radius, z))
    shape = core_h.fuse(core_v)
    for cx in (x + radius, x + width - radius):
        for cy in (y + radius, y + height - radius):
            shape = shape.fuse(Part.makeCylinder(radius, depth, App.Vector(cx, cy, z)))
    return shape.removeSplitter()


def add_feature(doc, group, name, label, shape, color, classification, requirement_ids, assumption_ids=""):
    obj = doc.addObject("Part::Feature", name)
    obj.Label = label
    obj.Shape = shape
    obj.ViewObject.ShapeColor = color
    obj.addProperty("App::PropertyString", "Classification", "Traceability")
    obj.Classification = classification
    obj.addProperty("App::PropertyString", "RequirementIDs", "Traceability")
    obj.RequirementIDs = requirement_ids
    obj.addProperty("App::PropertyString", "AssumptionIDs", "Traceability")
    obj.AssumptionIDs = assumption_ids
    group.addObject(obj)
    return obj
```

- [ ] **Step 4: Implement head, glass, display mask, and Balanced Crown parts**

Create a new document with the five specified top-level groups. Build the head at a neutral head-bottom height of 115 mm. Use rounded prisms for the front glass, display mask, crown shell, speaker inserts, camera pill, lens window, shutter rail/tab, fill-light windows, radar window, and ALS window. Use separate physical parts, controlled reveals, and non-coplanar Z positions to avoid duplicate/coincident faces.

- [ ] **Step 5: Run the native-CAD test and confirm all front objects pass**

Expected: build completes, FCStd exists, all required front objects are valid, and the outer glass bounds are 742 × 492 mm.

- [ ] **Step 6: Commit the front architecture**

```powershell
git add -- cad/iteration-03/build_hinoki_calm_crown.py cad/iteration-03/Hinoki_CalmCrown_Concept.FCStd tests/test_hinoki_iteration03.py
git commit -m "feat: build Hinoki Calm Crown front architecture"
```

## Task 3: Add the rear shell, internal claims, I/O, and traceability

**Files:**

- Modify: `cad/iteration-03/build_hinoki_calm_crown.py`
- Modify: `tests/test_hinoki_iteration03.py`

- [ ] **Step 1: Add failing assertions for rear and internal coverage**

The test must require `Rear_Shell`, `Rear_Service_Cover`, `Vent_Insert_Lower`, `IO_Recess`, all `REQUIRED_INTERNAL_CLAIMS`, and traceability properties on every required object. It must assert the rear service cover is 260 × 220 mm and the VESA reinforcement declares 100 mm.

- [ ] **Step 2: Run the test and observe missing rear/internal objects**

Expected: `FAIL` listing the missing objects.

- [ ] **Step 3: Build the rear pillow architecture**

Create a rounded rear shell behind the display, a 260 × 220 mm central service cover, lower vent insert, recessed I/O bay, and cable-exit feature. Use stepped/filleted solids so the rear is visibly shallower at the perimeter and fuller only at the central service island.

- [ ] **Step 4: Restore all internal space claims**

Create the listed internal claims as transparent `Part::Feature` objects. Add `Classification`, `RequirementIDs`, `AssumptionIDs`, and `ExportPolicy="ReferenceOnly"`. Keep them hidden by default.

- [ ] **Step 5: Run the coverage test**

Expected: every hard subsystem has an object and traceability; all product solids remain valid.

- [ ] **Step 6: Commit the rear and packaging architecture**

```powershell
git add -- cad/iteration-03/build_hinoki_calm_crown.py cad/iteration-03/Hinoki_CalmCrown_Concept.FCStd tests/test_hinoki_iteration03.py
git commit -m "feat: add Hinoki rear and internal architecture"
```

## Task 4: Build the stand, base, and true kinematic review states

**Files:**

- Modify: `cad/iteration-03/build_hinoki_calm_crown.py`
- Modify: `tests/test_hinoki_iteration03.py`

- [ ] **Step 1: Add failing motion and stand tests**

Require `Stand_Fixed_Spine`, `Stand_Moving_Spine`, `Pivot_Pod`, `VESA_Interface_Cover`, `Base_Upper`, `Base_Lower`, both feet, `Cable_Loop_Claim`, and six named motion-state compounds. Assert 120 mm travel, −5/0/+20-degree states, base bounds 420 × 285 × 68 mm, and no head/base intersection in each state.

- [ ] **Step 2: Run and observe missing stand/motion failures**

- [ ] **Step 3: Implement the D-profile spine, pivot, and VESA cover**

Use nested rounded prisms for fixed/moving members, a separate pivot pod and axis marker, and a 100 × 100 mm VESA interface cover. Preserve physical gaps between moving cosmetic covers.

- [ ] **Step 4: Implement the soft-plinth base**

Create separate upper/lower rounded shells, a thinner front edge, left/right feet, rear cable exit, and hidden power/ballast claims. The base bounding box must remain 420 × 285 × 68 mm.

- [ ] **Step 5: Implement true state compounds**

Create low, neutral, high, forward, and rearward state compounds from transformed copies of the complete head plus moving spine and cable-loop references. Store `HeightOffset` and `TiltAngle` properties on each state. Hide non-neutral states by default.

- [ ] **Step 6: Run stand/motion tests and commit**

```powershell
git add -- cad/iteration-03/build_hinoki_calm_crown.py cad/iteration-03/Hinoki_CalmCrown_Concept.FCStd tests/test_hinoki_iteration03.py
git commit -m "feat: add Hinoki Calm Crown stand and motion"
```

## Task 5: Add machine review, collision evidence, and scoring

**Files:**

- Create: `cad/iteration-03/review_hinoki_calm_crown.py`
- Modify: `tests/test_hinoki_iteration03.py`

- [ ] **Step 1: Add a failing review-report test**

Require a JSON report containing `hard_gates`, `category_scores`, `weighted_score`, `unauthorized_collisions`, `product_validity`, `requirement_coverage`, `motion_results`, `open_risks`, and `status`. Assert:

```python
self.assertEqual(report["unauthorized_collisions"], [])
self.assertTrue(all(report["hard_gates"].values()))
self.assertGreaterEqual(report["weighted_score"], 80.0)
self.assertEqual(report["status"], "Pass")
```

- [ ] **Step 2: Run and observe the missing review script/report failure**

- [ ] **Step 3: Implement geometry and collision checks**

For each export object, verify finite bounds, positive volume, `Shape.isValid()`, and closed solids. Compute pairwise common volume. Permit only named interfaces in an explicit whitelist and fail any other common volume above `0.01 mm³`.

- [ ] **Step 4: Implement requirement and motion gates**

Verify every required visible/internal object, camera centreline, 134° and 140° keep-out intersections, shutter open/closed states, base/head/stand clearances, I/O/service presence, and three-height/three-tilt state availability. Hard gaps produce `Fail`, never `PassWithOpenRisks`.

- [ ] **Step 5: Implement evidence-derived scoring**

Calculate the seven category scores from measured booleans/counts. Do not accept hand-entered totals. Enforce per-category minimums and `CONCEPT_SCORE_THRESHOLD`.

- [ ] **Step 6: Run review tests and commit**

```powershell
git add -- cad/iteration-03/review_hinoki_calm_crown.py cad/iteration-03/Hinoki_CalmCrown_Review.json tests/test_hinoki_iteration03.py
git commit -m "test: add Hinoki Calm Crown review gates"
```

## Task 6: Generate the publication-ready render package

**Files:**

- Create: `cad/iteration-03/render_hinoki_calm_crown.py`
- Modify: `tests/test_hinoki_iteration03.py`

- [ ] **Step 1: Add failing render-manifest assertions**

Require all five PNGs, minimum 1600 × 1000 resolution, non-empty image variance, and modification times later than the FCStd being rendered.

- [ ] **Step 2: Run and observe missing render outputs**

- [ ] **Step 3: Implement deterministic product visibility and camera helpers**

The render script must hide all reference groups for product views, apply Graphite CMF, set perspective/orthographic cameras, use a neutral light background, enable anti-aliasing, fit the product with controlled margins, and save 2400 × 1600 PNGs.

- [ ] **Step 4: Implement five required views**

Generate hero, rear, front, side-motion, and internal-overlay views. The side-motion and internal-overlay images must include only the relevant transparent references, never every keep-out at once.

- [ ] **Step 5: Visually inspect all images**

Open every PNG and verify silhouette, material separation, camera/shutter readability, stand/base proportion, no clipped geometry, and consistent background/scale. Correct the model or camera setup rather than accepting a misleading view.

- [ ] **Step 6: Run render tests and commit**

```powershell
git add -- cad/iteration-03/render_hinoki_calm_crown.py cad/iteration-03/*.png tests/test_hinoki_iteration03.py
git commit -m "feat: render Hinoki Calm Crown review package"
```

## Task 7: Export and independently verify the product-only STP

**Files:**

- Create: `cad/iteration-03/export_hinoki_calm_crown_step.py`
- Create: `cad/iteration-03/verify_hinoki_calm_crown_step.py`
- Create: `cad/iteration-03/verify_hinoki_calm_crown_cadquery.py`
- Modify: `tests/test_hinoki_iteration03.py`

- [ ] **Step 1: Add failing export and parity tests**

Require the STP and artifact manifest. Assert exact intended product leaf names/count, finite dimensions, millimetre scale, native/re-import part mapping, no reference objects, and a passing CadQuery verification record.

- [ ] **Step 2: Run and observe missing exporter/verifier failures**

- [ ] **Step 3: Implement product-only export**

Resolve exactly `PRODUCT_EXPORT_OBJECTS`, reject missing/invalid/duplicate shapes, export with `Import.export`, then write SHA-256 values and source revision metadata to `Hinoki_CalmCrown_Artifact_Manifest.json`.

- [ ] **Step 4: Implement FreeCAD neutral re-import parity**

Ignore origin/axis/plane/root-assembly objects. Map only finite positive-volume leaf solids. Verify exact intended count, overall bounding box, per-part bounding box/centroid tolerance ≤0.1 mm, and volume difference ≤0.1%.

- [ ] **Step 5: Create and use an isolated CadQuery 2.8.0 verifier environment**

Run:

```powershell
python -m venv 'C:\Users\skuan1\.cache\hinoki-cadquery-venv'
& 'C:\Users\skuan1\.cache\hinoki-cadquery-venv\Scripts\python.exe' -m pip install cadquery==2.8.0
```

The verifier imports the STP with `cadquery.importers.importStep`, checks finite positive volume and the expected overall size range, and writes its result into the artifact manifest.

- [ ] **Step 6: Run both verifiers and the full Iteration 03 test**

Expected: both importers pass, exact product leaf parity passes, and no reference objects are present.

- [ ] **Step 7: Commit STP and verification evidence**

```powershell
git add -- cad/iteration-03/Hinoki_CalmCrown_Concept_Review.stp cad/iteration-03/Hinoki_CalmCrown_Artifact_Manifest.json cad/iteration-03/export_hinoki_calm_crown_step.py cad/iteration-03/verify_hinoki_calm_crown_step.py cad/iteration-03/verify_hinoki_calm_crown_cadquery.py tests/test_hinoki_iteration03.py
git commit -m "feat: export and verify Hinoki Calm Crown STEP"
```

## Task 8: Independent agent review, remediation, and handoff documentation

**Files:**

- Create: `docs/reviews/2026-09-01-hinoki-calm-crown-agent-review.md`
- Modify: `README.md`
- Modify as required by veto remediation: `cad/iteration-03/*`, `tests/test_hinoki_iteration03.py`

- [ ] **Step 1: Freeze the candidate artifact revision**

Run all tests, regenerate all derived artifacts, calculate hashes, and record the candidate commit. Do not ask reviewers to score mixed revisions.

- [ ] **Step 2: Dispatch five independent review domains**

Assign Requirements/Architecture, ID/Product, Geometry/Mechanism, STEP Portability, and Traceability/Risk reviewers. Each receives the spec, FCStd, STP, renders, JSON evidence, and manifest. Reviewers return category scores, evidence, and explicit veto/no-veto.

- [ ] **Step 3: Remediate every veto and repeat affected reviews**

Only the reviewer who raised a veto may clear it after new evidence. A category-score spread greater than one point requires written adjudication.

- [ ] **Step 4: Aggregate the signed scorecard**

The QA integrator records hard-gate outcomes and computes the weighted score. Delivery requires zero vetoes, every hard gate true, total score ≥80, and all category minimums met.

- [ ] **Step 5: Update README and review record**

Document deliverable paths, exact verification commands/results, score, known concept limitations, branch/commit, and the fact that this is not manufacturing geometry. Keep README under 250 lines.

- [ ] **Step 6: Run final verification**

```powershell
python -m unittest tests.test_hinoki_iteration01 tests.test_hinoki_iteration02 tests.test_hinoki_iteration03 -v
git diff --check
git status --short
```

Expected: all tests pass; no diff errors; only the active Visual Companion `.superpowers/` directory may remain untracked.

- [ ] **Step 7: Commit the reviewed handoff**

```powershell
git add -- README.md docs/reviews/2026-09-01-hinoki-calm-crown-agent-review.md cad/iteration-03 tests/test_hinoki_iteration03.py
git commit -m "docs: approve Hinoki Calm Crown concept handoff"
```
