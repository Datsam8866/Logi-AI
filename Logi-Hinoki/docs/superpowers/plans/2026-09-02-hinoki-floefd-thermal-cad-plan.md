# Hinoki FLOEFD Thermal CAD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify a simplified named multi-body Hinoki CAD package for 35 °C, 57 W, fanless Simcenter FLOEFD conjugate heat-transfer analysis.

**Architecture:** Create a new `cad/thermal-simulation-01/` model independent of the product-review CAD. One immutable parameter module drives FreeCAD construction, review evidence, FLOEFD setup metadata, and controlled STEP export; tests always build into temporary paths before the formal artifacts are regenerated.

**Tech Stack:** FreeCAD 1.1 Python (`Part`, `Import`), Python `unittest`, JSON, STEP, Git.

---

## File Map

Create:

- `cad/thermal-simulation-01/hinoki_thermal_parameters.py` — geometry, body manifests, heat loads, materials, ambient, gravity, and filenames.
- `cad/thermal-simulation-01/build_hinoki_thermal_cht.py` — deterministic native FreeCAD construction.
- `cad/thermal-simulation-01/review_hinoki_thermal_cht.py` — geometry, airflow-path, overlap, and thermal-input checks.
- `cad/thermal-simulation-01/export_hinoki_thermal_cht.py` — controlled solid and air STEP export.
- `cad/thermal-simulation-01/Hinoki_Thermal_CHT_Model.FCStd` — retained native model.
- `cad/thermal-simulation-01/Hinoki_Thermal_CHT_Solids.step` — retained FLOEFD solid-body import.
- `cad/thermal-simulation-01/Hinoki_Thermal_Internal_Air.step` — retained fluid-region import.
- `cad/thermal-simulation-01/Hinoki_Thermal_FLOEFD_Setup.json` — retained setup map.
- `cad/thermal-simulation-01/Hinoki_Thermal_CHT_Review.json` — retained review evidence.
- `tests/test_hinoki_thermal_cht.py` — isolated acceptance and regression tests.

Modify:

- `README.md` — replace the active Next Action with the thermal CAD deliverable and exact commands; keep the file below 250 lines.

## Task 1: Freeze the FLOEFD thermal input contract

**Files:**

- Create: `cad/thermal-simulation-01/hinoki_thermal_parameters.py`
- Create: `tests/test_hinoki_thermal_cht.py`

- [ ] **Step 1: Write the failing parameter-contract test**

Create the test module with an import helper and this first test:

```python
from pathlib import Path
import importlib.util
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CAD_ROOT = PROJECT_ROOT / "cad" / "thermal-simulation-01"
PARAMETERS_FILE = CAD_ROOT / "hinoki_thermal_parameters.py"


def load_parameters():
    spec = importlib.util.spec_from_file_location("hinoki_thermal_parameters", PARAMETERS_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HinokiThermalCHTTests(unittest.TestCase):
    def test_parameter_contract_matches_approved_floefd_case(self):
        self.assertTrue(PARAMETERS_FILE.exists())
        p = load_parameters()
        self.assertEqual(p.HEAD, {"width": 742.0, "height": 492.0, "depth": 62.0})
        self.assertEqual(p.AMBIENT_C, 35.0)
        self.assertEqual(p.COOLING_MODE, "NaturalConvection")
        self.assertEqual(p.GRAVITY_MM_S2, (0.0, -9810.0, 0.0))
        self.assertEqual(p.VENT, {"width": 400.0, "height": 15.0, "area": 6000.0})
        self.assertAlmostEqual(sum(p.HEAT_LOADS_W.values()), 57.0)
        self.assertEqual(len(p.HEAT_LOADS_W), 10)
        self.assertEqual(p.HEAT_LOADS_W["Heat_QC7790"], 12.0)
        self.assertEqual(p.HEAT_LOADS_W["Heat_Panel_Backlight"], 20.0)
        self.assertEqual(p.MATERIAL_INTENT["Rear_Enclosure"], "PC/ABS")
        self.assertEqual(p.MATERIAL_INTENT["Internal_Air_Volume"], "Air")
```

- [ ] **Step 2: Run the test and confirm RED**

Run:

```powershell
python -B -m unittest tests.test_hinoki_thermal_cht.HinokiThermalCHTTests.test_parameter_contract_matches_approved_floefd_case -v
```

Expected: `FAIL` because `hinoki_thermal_parameters.py` does not exist.

- [ ] **Step 3: Implement the immutable contract**

Create the parameter module with these exact public values:

```python
HEAD = {"width": 742.0, "height": 492.0, "depth": 62.0}
GLASS_THICKNESS = 3.0
REAR_WALL = 2.5
MIDFRAME_THICKNESS = 2.0
ACTIVE_AREA = {"width": 708.4, "height": 398.5}
AMBIENT_C = 35.0
COOLING_MODE = "NaturalConvection"
GRAVITY_MM_S2 = (0.0, -9810.0, 0.0)
VENT = {"width": 400.0, "height": 15.0, "area": 6000.0}

HEAT_LOADS_W = {
    "Heat_Panel_Backlight": 20.0,
    "Heat_QC7790": 12.0,
    "Heat_Memory": 2.0,
    "Heat_Carrier_PMIC": 5.0,
    "Heat_IO": 5.0,
    "Heat_WiFi_BLE": 1.5,
    "Heat_Camera": 3.0,
    "Heat_Audio": 4.0,
    "Heat_Radar_ALS": 0.5,
    "Heat_Front_Lighting": 4.0,
}

SOLID_BODIES = (
    "Cover_Glass", "Mid_Frame", "Rear_Enclosure", "Heat_Panel_Backlight",
    "Carrier_PCB", "Heat_Spreader", "TIM_QC7790", "Heat_QC7790",
    "Heat_Memory", "Heat_Carrier_PMIC", "Heat_IO", "Heat_WiFi_BLE",
    "Heat_Camera", "Heat_Audio", "Heat_Radar_ALS", "Heat_Front_Lighting",
)
FLUID_BODIES = ("Internal_Air_Volume",)
BOUNDARY_FACES = ("Inlet_Opening_Lower_Rear", "Outlet_Opening_Upper_Rear")

MATERIAL_INTENT = {
    "Cover_Glass": "Generic glass",
    "Heat_Panel_Backlight": "FLOEFD equivalent display stack",
    "Mid_Frame": "Aluminum 6061",
    "Rear_Enclosure": "PC/ABS",
    "Carrier_PCB": "FLOEFD equivalent PCB",
    "Heat_Spreader": "Aluminum 6061",
    "TIM_QC7790": "Isotropic TIM; k=3 W/m-K",
    "Internal_Air_Volume": "Air",
}

MODEL_FILE = "Hinoki_Thermal_CHT_Model.FCStd"
SOLIDS_STEP = "Hinoki_Thermal_CHT_Solids.step"
AIR_STEP = "Hinoki_Thermal_Internal_Air.step"
SETUP_JSON = "Hinoki_Thermal_FLOEFD_Setup.json"
REVIEW_JSON = "Hinoki_Thermal_CHT_Review.json"
```

- [ ] **Step 4: Run the contract test and confirm GREEN**

Run the single test again. Expected: one test passes and the heat-load sum is exactly 57.0 W.

- [ ] **Step 5: Commit the contract**

```powershell
git add -- cad/thermal-simulation-01/hinoki_thermal_parameters.py tests/test_hinoki_thermal_cht.py
git commit -m "test: define Hinoki FLOEFD thermal contract"
```

## Task 2: Build the simplified conduction and airflow geometry

**Files:**

- Create: `cad/thermal-simulation-01/build_hinoki_thermal_cht.py`
- Create: `cad/thermal-simulation-01/Hinoki_Thermal_CHT_Model.FCStd`
- Modify: `tests/test_hinoki_thermal_cht.py`

- [ ] **Step 1: Add a failing native-model test**

Add a helper that passes source through FreeCAD with an absolute compile filename and explicit temporary output:

```python
import os
import subprocess
import tempfile

BUILD_SCRIPT = CAD_ROOT / "build_hinoki_thermal_cht.py"
FREECAD_CMD = Path(os.environ.get(
    "FREECAD_CMD",
    r"C:\Users\skuan1\AppData\Local\Programs\FreeCAD 1.1\bin\freecadcmd.exe",
))


def run_freecad_script(script, env):
    source = script.read_text(encoding="utf-8")
    launcher = f"exec(compile({source!r}, {str(script)!r}, 'exec'))\n"
    return subprocess.run(
        [str(FREECAD_CMD), "-c"],
        input=launcher,
        text=True,
        capture_output=True,
        env=env,
        cwd=Path(tempfile.gettempdir()),
        timeout=120,
        check=False,
    )
```

The test shall build to a temporary FCStd, require the five top-level groups `Thermal_Solids`, `Heat_Sources`, `Fluid_Regions`, `Boundary_References`, and `Thermal_Metadata`, require every manifest object, and probe:

```python
assert all(doc.getObject(name) is not None for name in required)
assert all(doc.getObject(name).Shape.isValid() for name in p.SOLID_BODIES)
assert all(doc.getObject(name).Shape.Volume > 0 for name in p.SOLID_BODIES)
assert doc.getObject("Internal_Air_Volume").Shape.isValid()
assert len(doc.getObject("Internal_Air_Volume").Shape.Solids) == 1
assert abs(doc.getObject("Inlet_Opening_Lower_Rear").Shape.Area - 6000.0) < 0.1
assert abs(doc.getObject("Outlet_Opening_Upper_Rear").Shape.Area - 6000.0) < 0.1
```

- [ ] **Step 2: Run the native-model test and confirm RED**

Expected: `FAIL` because the builder is absent.

- [ ] **Step 3: Implement deterministic builder interfaces**

The builder shall resolve its sibling parameter module from `__file__`, accept `HINOKI_THERMAL_MODEL_PATH`, and expose helpers with these signatures:

```python
def add_feature(doc, group, name, shape, classification, material, heat_w=0.0):
    """Create one Part::Feature with MaterialIntent, HeatLoadW, Classification, and Units."""


def make_box(size, origin):
    """Return Part.makeBox(size_x, size_y, size_z, App.Vector(*origin))."""


def build_model(output_path):
    """Build, recompute, validate, and atomically publish the FCStd."""
```

Use a temporary output next to the destination, call `doc.saveAs(temp_path)`, reopen it with `App.openDocument`, validate every required object, close it, then publish with `os.replace`.

- [ ] **Step 4: Build the enclosure, thermal stack, sources, and vents**

Use X left/right, Y bottom/top, Z front/rear with the finished head spanning:

```text
X = -371 .. +371 mm
Y = 0 .. 492 mm
Z = 0 .. 62 mm
```

Construct:

```python
cover_glass = make_box((742.0, 492.0, 3.0), (-371.0, 0.0, 0.0))
panel = make_box((708.4, 398.5, 12.0), (-354.2, 28.0, 3.0))
mid_frame = make_box((737.0, 487.0, 2.0), (-368.5, 2.5, 15.0))

rear_outer = make_box((742.0, 492.0, 45.0), (-371.0, 0.0, 17.0))
rear_cavity = make_box((737.0, 487.0, 42.5), (-368.5, 2.5, 17.0))
lower_vent = make_box((400.0, 15.0, 2.5), (-200.0, 20.0, 59.5))
upper_vent = make_box((400.0, 15.0, 2.5), (-200.0, 457.0, 59.5))
rear_enclosure = rear_outer.cut(rear_cavity).cut(lower_vent).cut(upper_vent)
```

Place the compute stack on the mid-frame with face contact and no volumetric overlap:

```text
Mid_Frame       Z 15.0–17.0
Heat_Spreader   Z 17.0–20.0, 160 × 100 mm
TIM_QC7790      Z 20.0–21.0, 40 × 40 mm
Heat_QC7790     Z 21.0–23.0, 40 × 40 mm
Carrier_PCB     Z 23.0–25.0, 200 × 120 mm
```

Place memory and PMIC beside QC7790 on the front side of `Carrier_PCB`. Place I/O near the lower rear, Wi-Fi/BLE at an upper side zone, camera/radar/front-light sources at the upper centre, and two audio source blocks at upper left/right. Every source must stay inside the 742 × 492 × 62 mm envelope and outside both vent channels.

- [ ] **Step 5: Construct the connected internal air body and boundary faces**

Form the fluid volume from the cavity plus both vent channels, subtracting all solids that occupy the rear cavity:

```python
air = rear_cavity.fuse(lower_vent).fuse(upper_vent)
for solid_name in REAR_CAVITY_SOLIDS:
    air = air.cut(doc.getObject(solid_name).Shape)
air = air.removeSplitter()
```

Create the two 400 × 15 mm boundary faces at Z=62 with outward normal +Z. Require one connected air solid and non-zero face intersection with both boundaries.

- [ ] **Step 6: Run the native-model test and confirm GREEN**

Expected: builder prints `HINOKI_THERMAL_BUILD_OK`, the temporary FCStd reopens, all manifests are present, all solids are valid, the air body is connected, and both boundary areas are 6,000 mm².

- [ ] **Step 7: Regenerate and commit the formal FCStd**

Run the builder once with `HINOKI_THERMAL_MODEL_PATH` set to the formal path, then:

```powershell
git add -- cad/thermal-simulation-01/build_hinoki_thermal_cht.py cad/thermal-simulation-01/Hinoki_Thermal_CHT_Model.FCStd tests/test_hinoki_thermal_cht.py
git commit -m "feat: build Hinoki FLOEFD thermal geometry"
```

## Task 3: Generate FLOEFD setup metadata and machine review

**Files:**

- Create: `cad/thermal-simulation-01/review_hinoki_thermal_cht.py`
- Create: `cad/thermal-simulation-01/Hinoki_Thermal_FLOEFD_Setup.json`
- Create: `cad/thermal-simulation-01/Hinoki_Thermal_CHT_Review.json`
- Modify: `tests/test_hinoki_thermal_cht.py`

- [ ] **Step 1: Add a failing review/setup test**

Require both JSON files and assert:

```python
self.assertEqual(setup["solver"], "Simcenter FLOEFD")
self.assertEqual(setup["analysis_type"], "ConjugateHeatTransfer")
self.assertEqual(setup["ambient_c"], 35.0)
self.assertEqual(setup["cooling_mode"], "NaturalConvection")
self.assertFalse(setup["fan_present"])
self.assertEqual(setup["gravity_mm_s2"], [0.0, -9810.0, 0.0])
self.assertAlmostEqual(sum(setup["heat_loads_w"].values()), 57.0)
self.assertEqual(review["status"], "Pass")
self.assertTrue(all(review["hard_gates"].values()))
self.assertEqual(review["unauthorized_overlaps"], [])
```

- [ ] **Step 2: Run the test and confirm RED**

Expected: `FAIL` because the review script and JSON outputs are absent.

- [ ] **Step 3: Implement the setup map**

Write `Hinoki_Thermal_FLOEFD_Setup.json` from the parameter module, never from duplicated literals. Include:

```json
{
  "solver": "Simcenter FLOEFD",
  "analysis_type": "ConjugateHeatTransfer",
  "units": "mm, W, degC",
  "ambient_c": 35.0,
  "cooling_mode": "NaturalConvection",
  "fan_present": false,
  "gravity_mm_s2": [0.0, -9810.0, 0.0],
  "heat_loads_w": {},
  "material_intent": {},
  "vent_openings": {},
  "external_domain": "Create in FLOEFD",
  "assumption_status": "Preliminary concept inputs"
}
```

- [ ] **Step 4: Implement evidence-derived geometry checks**

The review shall calculate and record:

- required-object presence;
- valid/closed/positive solid geometry;
- overall envelope within 0.1 mm of 742 × 492 × 62 mm;
- inlet/outlet area within 1% of 6,000 mm²;
- one connected internal-air solid;
- air intersection area with each boundary face greater than 5,900 mm²;
- every heat-source bound inside the head envelope;
- zero heat-source common volume with either vent channel;
- exact 57.0 W total;
- pairwise overlap volume for all solid bodies.

Permit only zero-volume face contact. Any common volume above 0.01 mm³ is unauthorized and sets `status` to `Fail`.

- [ ] **Step 5: Run review tests and confirm GREEN**

Use temporary environment overrides `HINOKI_THERMAL_MODEL_PATH`, `HINOKI_THERMAL_SETUP_PATH`, and `HINOKI_THERMAL_REVIEW_PATH`. Expected: setup and review are generated under the temporary directory, all hard gates are true, and status is `Pass`.

- [ ] **Step 6: Regenerate and commit formal review evidence**

```powershell
git add -- cad/thermal-simulation-01/review_hinoki_thermal_cht.py cad/thermal-simulation-01/Hinoki_Thermal_FLOEFD_Setup.json cad/thermal-simulation-01/Hinoki_Thermal_CHT_Review.json tests/test_hinoki_thermal_cht.py
git commit -m "test: add Hinoki thermal review gates"
```

## Task 4: Export, re-import, document, and verify the FLOEFD package

**Files:**

- Create: `cad/thermal-simulation-01/export_hinoki_thermal_cht.py`
- Create: `cad/thermal-simulation-01/Hinoki_Thermal_CHT_Solids.step`
- Create: `cad/thermal-simulation-01/Hinoki_Thermal_Internal_Air.step`
- Modify: `tests/test_hinoki_thermal_cht.py`
- Modify: `README.md`

- [ ] **Step 1: Add failing STEP export/re-import tests**

The test shall run the exporter with temporary output paths and assert:

```python
self.assertTrue(solids_step.exists())
self.assertTrue(air_step.exists())
self.assertGreater(solids_step.stat().st_size, 10_000)
self.assertGreater(air_step.stat().st_size, 1_000)
```

Probe each imported STEP with FreeCAD. Require exactly `len(SOLID_BODIES)` positive-volume solids in the solids STEP, exactly one positive-volume solid in the air STEP, millimetre-scale overall dimensions, and no boundary-reference faces in either file.

- [ ] **Step 2: Run the test and confirm RED**

Expected: `FAIL` because the exporter and STEP files are absent.

- [ ] **Step 3: Implement controlled export**

The exporter shall:

1. Open the FCStd from `HINOKI_THERMAL_MODEL_PATH` or the formal default.
2. Resolve exactly `SOLID_BODIES`; reject missing, invalid, non-solid, or zero-volume objects.
3. Export solids with `Import.export(objects, solids_temp_path)`.
4. Export only `Internal_Air_Volume` to `air_temp_path`.
5. Reopen both temporary STEP files with FreeCAD and verify expected positive-volume solid counts and scale.
6. Atomically replace `HINOKI_THERMAL_SOLIDS_STEP_PATH` and `HINOKI_THERMAL_AIR_STEP_PATH` only after verification.
7. Print `HINOKI_THERMAL_EXPORT_OK`.

- [ ] **Step 4: Update README with the thermal deliverable**

Document:

- the purpose and concept-only maturity;
- the five files a FLOEFD user needs;
- the 35 °C / 57 W / natural-convection case;
- exact build, review, export, and test commands;
- FLOEFD import steps from the approved design;
- the fact that surface radiation, emissivity, external domain, pressure boundaries, and result limits are configured in FLOEFD;
- current assumptions and absence of production temperature limits.

Keep README below 250 lines and remove the obsolete active Next Action that asks for publication renders or stand/motion completion.

- [ ] **Step 5: Run full verification**

Run from `Logi-Hinoki`:

```powershell
python -B -m unittest tests.test_hinoki_thermal_cht -v
git diff --check
git status --short
```

Expected:

- all thermal tests pass with no skipped tests;
- formal FCStd and both STEP files reopen successfully;
- setup heat loads sum to 57.0 W;
- review status is `Pass`;
- only the pre-existing `.superpowers/` directory remains untracked.

- [ ] **Step 6: Commit the complete FLOEFD package**

```powershell
git add -- README.md cad/thermal-simulation-01 tests/test_hinoki_thermal_cht.py
git commit -m "feat: deliver Hinoki FLOEFD thermal CAD"
```

## Final Review Boundary

Before presenting the deliverable, independently verify the frozen thermal inputs, body/material/load mapping, geometry validity, vent connectivity, STEP body counts, and scope truthfulness. Do not apply the superseded Calm Crown product-appearance scorecard to this thermal-only model.
