# Hinoki LOD 3 Task 7 Overlap Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove all 28 confirmed unauthorised head collisions and make Task 7 validate every physical semantic-part pair without weakening the 0.01 mm3 hard gate.

**Architecture:** Preserve the head envelope, board placements, VESA interface, and passive thermal chain. Housing geometry owns VESA and rib reliefs; electronics geometry owns shield, connector, heat-proxy, and thermal keep-outs; the validator independently checks every unique physical pair and exempts only the three approved heat contacts.

**Tech Stack:** Python 3 `unittest`, FreeCAD 1.1 Python API (`App`, `Part`), OCC boolean geometry, JSON, Git.

---

## Execution rules

- Work in `C:\Users\skuan1\.codex\visualizations\2026\09\03\01a06579-1496-7d10-af7e-8cca66c0f3a9\Logi-AI-hinoki-task7\Logi-Hinoki` on branch `codex/hinoki-lod3-task7`.
- Use `C:\Users\skuan1\AppData\Local\Programs\FreeCAD 1.1\bin\freecadcmd.exe` unless `FREECAD_CMD` overrides it.
- Use the official Codex `--codex-run-as-apply-patch` entrypoint for every file edit.
- Start every behavior with an observed failing test.
- Write all generated FCStd and JSON files below the system temporary directory.
- Do not update formal FCStd/JSON artifacts until every Task 7 gate passes.
- Keep the exact 0.01 mm3 threshold and the exact three-pair authorised-contact matrix.
- Do not add stand/base, cable routes, full-product STEP, review images, or FLOEFD derivatives.
- Do not modify Iteration 01, Iteration 02, or thermal preview artifacts.

## File responsibilities

- `hinoki_lod3_parameters.py`: controlled VESA mount points and clearance dimensions.
- `hinoki_lod3_display_housing.py`: VESA plate holes, rear boss geometry, and rib relief application.
- `hinoki_lod3_electronics_thermal.py`: electronics placement source of truth, housing keep-out shapes, open shield proxies, heat-proxy and spreader reliefs.
- `review_hinoki_lod3.py`: complete physical-pair validation and machine-readable evidence.
- `build_hinoki_lod3_master.py`: already-correct non-zero failure propagation and publication gate.
- `tests/test_hinoki_lod3_inferred.py`: independent collision oracle, category assertions, validator-scope proof, and regression coverage.
- `README.md`: current Task 7 status and limitations after all tests pass.

## Task 1: Remove all confirmed geometry overlaps

**Files:**

- Modify: `cad/lod3-inferred-prototype-01/hinoki_lod3_parameters.py`
- Modify: `cad/lod3-inferred-prototype-01/hinoki_lod3_display_housing.py`
- Modify: `cad/lod3-inferred-prototype-01/hinoki_lod3_electronics_thermal.py`
- Modify: `tests/test_hinoki_lod3_inferred.py`

- [ ] **Step 1: Preserve and run the independent all-pair RED test**

Keep the existing test probe that opens the temporary FCStd, collects every
physical semantic part outside `08_Reference_Datums_Keepouts`, checks every
unique unordered pair, skips only these pairs, and exits 1 when any remaining
overlap exceeds 0.01 mm3:

```python
authorized = {
    tuple(sorted(pair))
    for pair in (
        ("Camera_Module", "Heat_Camera"),
        ("Front_Light_Left", "Heat_Front_Lighting"),
        ("Front_Light_Right", "Heat_Front_Lighting"),
    )
}
```

Run:

```powershell
python -B -m unittest tests.test_hinoki_lod3_inferred.TestMasterValidation.test_head_only_review_reports_all_active_hard_gates -v
```

Expected: FAIL with `physical_count: 79` and exactly the 28 documented forbidden pairs.

Parse the probe output for the category checks below instead of relying on
substring matching:

```python
sentinel = "HINOKI_LOD3_ALL_PHYSICAL_OVERLAPS "
payload = next(
    line.split(sentinel, 1)[1]
    for line in overlap_output.splitlines()
    if sentinel in line
)
overlap_report = json.loads(payload)
actual_forbidden_pairs = {
    tuple(sorted(entry["parts"]))
    for entry in overlap_report["forbidden"]
}
```

- [ ] **Step 2: Add failing controlled-clearance contract tests**

Add assertions to `TestFrozenEngineeringContract`:

```python
def test_collision_clearance_contract(self):
    p = load_module(PARAMETERS_FILE, "hinoki_lod3_parameters_clearance")
    self.assertEqual(
        ((321.0, 196.0), (421.0, 196.0), (321.0, 296.0), (421.0, 296.0)),
        p.VESA_MOUNT_POINTS,
    )
    self.assertEqual(0.5, p.COLLISION_CLEARANCE["linear"])
    self.assertEqual(0.5, p.COLLISION_CLEARANCE["radial"])
    self.assertEqual(0.8, p.COLLISION_CLEARANCE["shield_wall"])
    self.assertEqual(44.0, p.COLLISION_CLEARANCE["rear_boss_z"])
    self.assertEqual(15.2, p.COLLISION_CLEARANCE["rear_boss_height"])
```

Run:

```powershell
python -B -m unittest tests.test_hinoki_lod3_inferred.TestFrozenEngineeringContract.test_collision_clearance_contract -v
```

Expected: FAIL because `VESA_MOUNT_POINTS` and `COLLISION_CLEARANCE` do not exist.

- [ ] **Step 3: Add the controlled clearance values**

Add to `hinoki_lod3_parameters.py`:

```python
VESA_MOUNT_POINTS = (
    (321.0, 196.0),
    (421.0, 196.0),
    (321.0, 296.0),
    (421.0, 296.0),
)
COLLISION_CLEARANCE = frozen(
    linear=0.5,
    radial=0.5,
    shield_wall=0.8,
    rear_boss_z=44.0,
    rear_boss_height=15.2,
)
```

Re-run the contract test. Expected: PASS.

- [ ] **Step 4: Add VESA clearance holes and rear-only boss geometry**

In `hinoki_lod3_display_housing.py`, build the VESA plate from an outer box
and cut one cylinder at every controlled mount point:

```python
def vesa_reinforcement_shape():
    shape = Part.makeBox(140.0, 140.0, 3.0, vector(301.0, 176.0, 56.2))
    radius = p.HOUSING["primary_boss_od"] / 2.0 + p.COLLISION_CLEARANCE["radial"]
    cutters = [
        Part.makeCylinder(radius, 3.2, vector(x, y, 56.1))
        for x, y in p.VESA_MOUNT_POINTS
    ]
    return shape.cut(Part.makeCompound(cutters))
```

Use `vesa_reinforcement_shape()` for `VESA_Reinforcement`. Replace the four
hard-coded VESA boss coordinates with `p.VESA_MOUNT_POINTS`. For bosses 05-08,
use:

```python
boss_z = p.COLLISION_CLEARANCE["rear_boss_z"]
boss_height = p.COLLISION_CLEARANCE["rear_boss_height"]
boss_shape = Part.makeCylinder(
    p.HOUSING["primary_boss_od"] / 2.0,
    boss_height,
    vector(x, y, boss_z),
).cut(
    Part.makeCylinder(1.6, boss_height + 0.2, vector(x, y, boss_z - 0.1))
)
```

Keep bosses 01-04 unchanged. Do not move the VESA mount points or fasteners.

- [ ] **Step 5: Run the VESA/boss collision probe**

Add a category assertion that none of these 16 pairs occurs in the independent
forbidden list:

```python
expected_removed = {
    tuple(sorted((left, right)))
    for left, right in (
        ("VESA_Reinforcement", "Primary_Boss_05"),
        ("VESA_Reinforcement", "M3_Fastener_05"),
        ("VESA_Reinforcement", "Primary_Boss_06"),
        ("VESA_Reinforcement", "M3_Fastener_06"),
        ("VESA_Reinforcement", "Primary_Boss_07"),
        ("VESA_Reinforcement", "M3_Fastener_07"),
        ("VESA_Reinforcement", "Primary_Boss_08"),
        ("VESA_Reinforcement", "M3_Fastener_08"),
        ("Primary_Boss_05", "Carrier_PCB"),
        ("Primary_Boss_05", "Aluminum_Interface"),
        ("Primary_Boss_06", "Carrier_PCB"),
        ("Primary_Boss_06", "Aluminum_Interface"),
        ("Primary_Boss_07", "Carrier_PCB"),
        ("Primary_Boss_07", "Aluminum_Interface"),
        ("Primary_Boss_08", "Carrier_PCB"),
        ("Primary_Boss_08", "Aluminum_Interface"),
    )
}
self.assertTrue(expected_removed.isdisjoint(actual_forbidden_pairs))
```

Run the targeted test. Expected: the VESA/boss assertion passes and the global
zero-overlap assertion still fails with 12 remaining pairs.

- [ ] **Step 6: Expose electronics-owned housing keep-outs**

In `hinoki_lod3_electronics_thermal.py`, define the existing geometry once:

```python
BOARD_POSITIONS = {
    "Carrier_PCB": (246.0, 176.0, 27.0),
    "Compute_SOM_PCB": (326.0, 211.0, 28.6),
    "Power_PCB": (55.0, 176.0, 27.0),
    "IO_PCB": (281.0, 106.0, 27.0),
    "WiFi_BLE_Module": (652.0, 215.0, 27.0),
}

CONNECTOR_SPECS = {
    "Carrier_BoardToBoard_Connector": ((30.0, 8.0, 5.0), (356.0, 200.0, 28.6)),
    "Power_Input_Connector": ((24.0, 12.0, 8.0), (68.0, 210.0, 28.6)),
    "Display_FFC_Connector": ((42.0, 6.0, 4.0), (350.0, 306.0, 28.6)),
    "IO_Harness_Connector": ((38.0, 8.0, 5.0), (352.0, 126.0, 28.6)),
}

HEAT_BOX_SPECS = {
    "Heat_Memory": ((22.0, 16.0, 2.0), (294.0, 228.0, 30.2)),
    "Heat_IO": ((35.0, 20.0, 3.0), (353.5, 111.0, 28.6)),
}

THERMAL_BOX_SPECS = {
    "Copper_Spreader": ((100.0, 80.0, 2.0), (321.0, 206.0, 33.2)),
    "Aluminum_Interface": ((220.0, 120.0, 2.5), (261.0, 186.0, 41.2)),
}

HEAT_PIPE_SPECS = {
    "Heat_Pipe_Left": (3.0, 160.0, (291.0, 224.0, 38.2)),
    "Heat_Pipe_Right": (3.0, 160.0, (291.0, 268.0, 38.2)),
}
```

Use these mappings in the existing builder. Add reusable expansion helpers and
a focused keep-out interface:

```python
def expanded_box(dimensions, position, clearance):
    width, height, depth = dimensions
    x, y, z = position
    return Part.makeBox(
        width + 2.0 * clearance,
        height + 2.0 * clearance,
        depth + 2.0 * clearance,
        vector(x - clearance, y - clearance, z - clearance),
    )


def expanded_connector_shape(name):
    dimensions, position = CONNECTOR_SPECS[name]
    return expanded_box(
        dimensions,
        position,
        p.COLLISION_CLEARANCE["linear"],
    )


def housing_keepout_shapes(clearance):
    boxes = [
        expanded_box(*CONNECTOR_SPECS["Power_Input_Connector"], clearance),
        expanded_box(*HEAT_BOX_SPECS["Heat_Memory"], clearance),
        expanded_box(
            *THERMAL_BOX_SPECS["Aluminum_Interface"],
            clearance
        ),
    ]
    pipes = [
        Part.makeCylinder(
            radius + clearance,
            length + 2.0 * clearance,
            vector(position[0] - clearance, position[1], position[2]),
            vector(1.0, 0.0, 0.0),
        )
        for radius, length, position in HEAT_PIPE_SPECS.values()
    ]
    return boxes + pipes
```

The connector, memory, aluminium-interface, and heat-pipe keep-outs include
0.5 mm clearance around the same mapping used to build the actual proxies. Do
not move those components or duplicate their coordinates elsewhere.

- [ ] **Step 7: Cut electronics keep-outs from ribs**

Import `housing_keepout_shapes` into `hinoki_lod3_display_housing.py`.
After creating each rib box, subtract the compound of those keep-outs:

```python
rib_shape = Part.makeBox(
    p.HOUSING["structural_rib"],
    360.0,
    22.0,
    vector(x, 66.0, 32.0),
)
rib_shape = rib_shape.cut(
    Part.makeCompound(
        housing_keepout_shapes(p.COLLISION_CLEARANCE["linear"])
    )
)
```

Apply the same operation consistently to all ribs; unaffected ribs retain their
original volume because the keep-outs do not intersect them.

- [ ] **Step 8: Run the rib collision probe**

Add a category assertion for these eight pairs:

```python
rib_pairs = {
    tuple(sorted(pair))
    for pair in (
        ("Structural_Rib_01", "Power_Input_Connector"),
        ("Structural_Rib_03", "Heat_Memory"),
        ("Structural_Rib_03", "Heat_Pipe_Left"),
        ("Structural_Rib_03", "Heat_Pipe_Right"),
        ("Structural_Rib_03", "Aluminum_Interface"),
        ("Structural_Rib_04", "Heat_Pipe_Left"),
        ("Structural_Rib_04", "Heat_Pipe_Right"),
        ("Structural_Rib_04", "Aluminum_Interface"),
    )
}
self.assertTrue(rib_pairs.isdisjoint(actual_forbidden_pairs))
```

Run the targeted test. Expected: the rib assertion passes and the global
zero-overlap assertion still fails with four remaining pairs.

- [ ] **Step 9: Replace solid shields with relieved thin-wall proxies**

Add to `hinoki_lod3_electronics_thermal.py`:

```python
def open_shield_shape(dimensions, position, connector_clearance=None):
    width, height, depth = dimensions
    x, y, z = position
    wall = p.COLLISION_CLEARANCE["shield_wall"]
    outer = Part.makeBox(width, height, depth, vector(x, y, z))
    inner = Part.makeBox(
        width - 2.0 * wall,
        height - 2.0 * wall,
        depth - wall + 0.1,
        vector(x + wall, y + wall, z - 0.1),
    )
    shape = outer.cut(inner)
    if connector_clearance is not None:
        shape = shape.cut(connector_clearance)
    return shape
```

Build expanded connector-clearance boxes from `CONNECTOR_SPECS` and pass them
to `Power_Shield_Can` and `IO_Shield_Can`. Keep `SOM_Shield_Can` thin-wall
but without a connector opening because no confirmed overlap crosses it.

- [ ] **Step 10: Relieve Heat_IO and Copper_Spreader**

Create the original shapes, then subtract the matching connector clearance:

```python
heat_io_shape = Part.makeBox(35.0, 20.0, 3.0, vector(353.5, 111.0, 28.6))
heat_io_shape = heat_io_shape.cut(
    expanded_connector_shape("IO_Harness_Connector")
)

copper_spreader_shape = Part.makeBox(
    100.0, 80.0, 2.0, vector(321.0, 206.0, 33.2)
)
copper_spreader_shape = copper_spreader_shape.cut(
    expanded_connector_shape("Carrier_BoardToBoard_Connector")
)
```

Use the relieved shapes in `heat_shapes` and `thermal_shapes`. Preserve
`Heat_IO.HeatLoadW == 5.0`, copper material intent, and every existing thermal
contact pair.

- [ ] **Step 11: Run the all-pair GREEN test**

Run:

```powershell
python -B -m unittest tests.test_hinoki_lod3_inferred.TestMasterValidation.test_head_only_review_reports_all_active_hard_gates -v
```

Expected: PASS with `physical_count: 79` and `forbidden: []`.

Run subsystem regressions:

```powershell
python -B -m unittest tests.test_hinoki_lod3_inferred.TestFrozenEngineeringContract tests.test_hinoki_lod3_inferred.TestDisplayHousingGeometry tests.test_hinoki_lod3_inferred.TestElectronicsThermalGeometry tests.test_hinoki_lod3_inferred.TestAvIoGeometry -v
```

Expected: all selected tests pass; geometry stays valid and positive, VESA and
rear-hatch TIM checks remain unchanged, and heat loads still total 57 W.

- [ ] **Step 12: Commit the geometry remediation**

```powershell
git add -- cad/lod3-inferred-prototype-01/hinoki_lod3_parameters.py cad/lod3-inferred-prototype-01/hinoki_lod3_display_housing.py cad/lod3-inferred-prototype-01/hinoki_lod3_electronics_thermal.py tests/test_hinoki_lod3_inferred.py
git commit -m "fix: remove LOD 3 head geometry overlaps"
```

## Task 2: Expand the validator to the complete head collision domain

**Files:**

- Modify: `cad/lod3-inferred-prototype-01/review_hinoki_lod3.py`
- Modify: `tests/test_hinoki_lod3_inferred.py`

- [ ] **Step 1: Write a failing pair-count and cross-subsystem detection test**

After building a temporary document, calculate:

```python
physical_count = 79
expected_authorized_count = 3
expected_checked_pairs = (
    physical_count * (physical_count - 1) // 2
    - expected_authorized_count
)
self.assertEqual(
    expected_checked_pairs,
    report["authorized_contact_matrix"]["checked_forbidden_pair_count"],
)
```

Then replace `Structural_Rib_01.Shape` with
`Structural_Rib_02.Shape.copy()`, call `validate_master(doc)`, and assert:

```python
injected = validate_master(doc)
self.assertEqual("Fail", injected["status"])
self.assertFalse(injected["hard_gates"]["no_forbidden_overlaps"])
self.assertIn(
    ["Structural_Rib_01", "Structural_Rib_02"],
    [entry["parts"] for entry in injected["forbidden_overlaps"]],
)
```

Run:

```powershell
python -B -m unittest tests.test_hinoki_lod3_inferred.TestMasterValidation -v
```

Expected: FAIL because the initial validator checks only the Task 5 integration
domain and does not report the complete pair count or injected rib collision.

- [ ] **Step 2: Validate every unique physical pair**

In `review_hinoki_lod3.py`, replace the Task 5 assembly-domain pair
construction with:

```python
from itertools import combinations

checked_forbidden_pairs = 0
forbidden = []
for left, right in combinations(physical_parts, 2):
    pair = tuple(sorted((left.Name, right.Name)))
    if pair in expected:
        continue
    checked_forbidden_pairs += 1
    overlap = float(left.Shape.common(right.Shape).Volume)
    if overlap > OVERLAP_THRESHOLD_MM3:
        forbidden.append(
            {
                "parts": [left.Name, right.Name],
                "overlap_mm3": overlap,
            }
        )
```

Store `checked_forbidden_pairs` in the machine-readable
`authorized_contact_matrix` evidence. Do not change
`EXPECTED_AUTHORIZED_CONTACTS` or `OVERLAP_THRESHOLD_MM3`.

- [ ] **Step 3: Run targeted GREEN**

```powershell
python -B -m unittest tests.test_hinoki_lod3_inferred.TestMasterValidation -v
```

Expected: all tests pass. The normal model reports zero forbidden overlaps; the
injected rib collision reports Fail and prevents publication.

- [ ] **Step 4: Commit the complete validator**

```powershell
git add -- cad/lod3-inferred-prototype-01/review_hinoki_lod3.py tests/test_hinoki_lod3_inferred.py
git commit -m "fix: validate every LOD 3 head collision pair"
```

## Task 3: Verify Task 7 and update the handoff

**Files:**

- Modify: `README.md`

- [ ] **Step 1: Run the complete LOD 3 suite**

```powershell
python -B -m unittest tests.test_hinoki_lod3_inferred -v
```

Expected: all tests pass, including the full-pair collision oracle, exact
authorised-contact matrix, sentinel/exit-code tests, and existing AV/I/O tests.

- [ ] **Step 2: Compile the changed Python files**

```powershell
python -m py_compile cad/lod3-inferred-prototype-01/hinoki_lod3_parameters.py cad/lod3-inferred-prototype-01/hinoki_lod3_display_housing.py cad/lod3-inferred-prototype-01/hinoki_lod3_electronics_thermal.py cad/lod3-inferred-prototype-01/review_hinoki_lod3.py cad/lod3-inferred-prototype-01/build_hinoki_lod3_master.py tests/test_hinoki_lod3_inferred.py
```

Expected: exit code 0 and no output.

- [ ] **Step 3: Update README without publishing formal artifacts**

In `README.md`, replace the Task 5 checkpoint wording with a concise Task 7
status block:

```markdown
## Task 7 head-only validation

The temporary head-only build contains 97 semantic parts and 79 physical
collision parts. Task 7 checks every unique physical pair at the 0.01 mm3
threshold and authorises only the three camera/front-light heat contacts.
Temporary validation reports Pass.

The formal FCStd remains the earlier 62-part checkpoint until Task 8 performs
atomic publication. Task 6 stand/base, cable routes, full-product STEP, review
images, and the FLOEFD derivative remain deferred.
```

Keep `README.md` below 250 lines.

- [ ] **Step 4: Verify scope and whitespace**

```powershell
rg -n "Task 7|97 semantic|79 physical|0.01 mm3|62-part|Task 6" README.md
git diff --check
git status --short
```

Expected: README contains all six handoff facts; `git diff --check` is silent;
only Task 7 remediation files and README are changed relative to the Task 7
base. No formal FCStd or JSON file is modified.

- [ ] **Step 5: Commit the handoff update**

```powershell
git add -- README.md
git commit -m "docs: record Task 7 head validation"
```

## Final review gate

- [ ] Compare the complete diff against
  `docs/superpowers/specs/2026-09-03-hinoki-lod3-task7-overlap-remediation-design.md`.
- [ ] Confirm the independent all-pair oracle and validator agree on zero
  forbidden overlaps.
- [ ] Confirm the validator checks 3,078 non-authorised pairs for 79 physical
  parts and retains exactly three authorised contacts.
- [ ] Confirm all physical semantic parts have valid non-null positive geometry,
  complete metadata, eight-group ownership, and ManufacturingAuthority=false.
- [ ] Confirm the 742 x 492 x 62 mm head envelope and 57 W heat total are
  unchanged.
- [ ] Confirm build failure returns non-zero, emits one failure sentinel, and
  leaves no temporary or formal artifact.
- [ ] Confirm Task 6, cable routes, full-product STEP, review images, FLOEFD
  derivatives, Iteration 01, Iteration 02, and formal outputs remain untouched.
