# Hinoki LOD 3 Inferred Engineering Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a traceable 80–120-part Hinoki LOD 3 inferred engineering prototype and a controlled Simcenter FLOEFD derivative for the approved 35 °C, 57 W, fanless natural-convection case.

**Architecture:** A frozen Python parameter/source contract drives independent FreeCAD subsystem builders. A master assembler creates semantic parts and metadata; validators gate atomic FCStd/STEP/JSON/PNG publication. A separate deterministic suppression map derives the FLOEFD solids and one connected internal-air body without altering the master.

**Tech Stack:** Python 3 `unittest`, FreeCAD 1.1 Python API (`App`, `Part`, `Import`, `TechDraw`/view APIs), JSON, STEP AP214/AP242 exchange, Git.

---

## Execution rules

- Run in `C:\Users\skuan1\.config\superpowers\worktrees\Logi-AI\hinoki-iteration02-review\Logi-Hinoki` on branch `codex/hinoki-iteration02-review`.
- Use `C:\Users\skuan1\AppData\Local\Programs\FreeCAD 1.1\bin\freecadcmd.exe` unless `FREECAD_CMD` overrides it.
- Every behavior starts with a failing test and an observed expected failure.
- Tests write only below the system temporary directory. Formal artifacts are published only after all gates pass.
- Do not add `.superpowers/`, `cad/thermal-simulation-01/Hinoki_Thermal_CHT_Review.png`, or `cad/thermal-simulation-01/preview_hinoki_thermal_cht.py` to any LOD 3 commit.
- Do not modify or regenerate `cad/iteration-01/`, `cad/iteration-02/`, or their formal artifacts.
- Every inferred semantic part sets `ManufacturingAuthority = false` and the package states `LOD 3 inferred engineering prototype; not manufacturing release`.

## Task 1: Freeze the parameter, source, and manifest contract

**Files:**

- Create: `cad/lod3-inferred-prototype-01/hinoki_lod3_parameters.py`
- Create: `cad/lod3-inferred-prototype-01/hinoki_lod3_sources.py`
- Create: `tests/test_hinoki_lod3_inferred.py`

- [ ] Write tests `test_frozen_product_envelope_and_display_stack`, `test_source_precedence_rejects_uniform_dixie_scale`, `test_thermal_case_is_exactly_57_w`, and `test_manifest_schema_denies_manufacturing_authority`.

```python
def test_frozen_product_envelope_and_display_stack(self):
    p = load_module(PARAMETERS_FILE, "hinoki_lod3_parameters")
    self.assertEqual((742.0, 492.0, 62.0), tuple(p.HEAD.values()))
    self.assertEqual((726.0, 446.0, 3.2), tuple(p.DISPLAY_STACK["Cover_Glass"].values()))
    self.assertEqual(6000.0, p.VENTS["Inlet_Lower_Rear"]["minimum_open_area"])

def test_thermal_case_is_exactly_57_w(self):
    p = load_module(PARAMETERS_FILE, "hinoki_lod3_parameters")
    self.assertEqual(10, len(p.HEAT_LOADS_W))
    self.assertAlmostEqual(57.0, sum(p.HEAT_LOADS_W.values()), places=9)
```

- [ ] Run RED and confirm import/file-not-found failures:

```powershell
python -B -m unittest tests.test_hinoki_lod3_inferred -v
```

Expected: four tests fail because the parameter/source modules do not exist.

- [ ] Implement immutable mappings for the approved head, display, housing, vents, boards, camera, sensors, audio, thermal stack, stand, material intents, ten heat loads, eight group names, metadata keys, source precedence, `MP-077`, and output filenames. Implement `source_record()` so conflicts reject lower-authority values and never average them.
- [ ] Run GREEN with the same command. Expected: four tests pass.
- [ ] Commit only the three task files:

```powershell
git add -- cad/lod3-inferred-prototype-01/hinoki_lod3_parameters.py cad/lod3-inferred-prototype-01/hinoki_lod3_sources.py tests/test_hinoki_lod3_inferred.py
git commit -m "feat: freeze Hinoki LOD 3 engineering contract"
```

## Task 2: Index Dixie references without copying the source assembly

**Files:**

- Create: `cad/lod3-inferred-prototype-01/index_hinoki_lod3_sources.py`
- Modify: `tests/test_hinoki_lod3_inferred.py`

- [ ] Add tests that run the indexer against fixture paths and assert SHA-256, byte size, authority class, rejected `14498.4 mm` literal, absence of copied Dixie STEP bytes, and failure for a missing required source.
- [ ] Run the targeted RED test:

```powershell
python -B -m unittest tests.test_hinoki_lod3_inferred.TestSourceInventory -v
```

Expected: failure because `index_hinoki_lod3_sources.py` does not exist.

- [ ] Implement `build_source_index(source_root, output_path)` using streamed SHA-256 reads. Record the Dixie 3D/BOM/2D/panel/thermal references and Hinoki spreadsheets as external references; do not copy the approximately 456 MB Dixie STEP into the repository.
- [ ] Run the targeted test. Expected: source inventory tests pass and temporary files are cleaned.
- [ ] Commit:

```powershell
git add -- cad/lod3-inferred-prototype-01/index_hinoki_lod3_sources.py tests/test_hinoki_lod3_inferred.py
git commit -m "feat: index LOD 3 reference authority"
```

## Task 3: Build the head, housing, and display stack

**Files:**

- Create: `cad/lod3-inferred-prototype-01/hinoki_lod3_common.py`
- Create: `cad/lod3-inferred-prototype-01/hinoki_lod3_display_housing.py`
- Create: `cad/lod3-inferred-prototype-01/build_hinoki_lod3_master.py`
- Modify: `tests/test_hinoki_lod3_inferred.py`

- [ ] Add a FreeCAD probe test that builds to a temporary FCStd and asserts eight ordered top groups, 742 × 492 × 62 mm head envelope, display layer dimensions, 2.8 mm rear wall, 1.7 mm ribs, 7 mm boss OD, explicit upper/lower vent fields, positive closed solids, and complete metadata.
- [ ] Run RED:

```powershell
python -B -m unittest tests.test_hinoki_lod3_inferred.TestDisplayHousingGeometry -v
```

Expected: builder/module missing failure.

- [ ] Implement helpers `semantic_part()`, `add_metadata()`, `rounded_box_proxy()`, `perforated_field()`, and `publish_fcstd_atomically()`. Build cover glass, PCAP, optical bond, LCD, BLU, T-con, carrier, front frame, rear shell, mid-frame, retainers, hatches, grille fields, I/O cover, VESA reinforcement, ribs, bosses, and fasteners from recorded parameters only.
- [ ] Model each vent as explicit repeated slots whose summed open area is at least 6000 mm² inside the 400 × 25 mm gross field. Keep front surfaces unobstructed except approved camera/light/sensor/audio features.
- [ ] Run GREEN. Expected: display/housing tests pass; builder emits `HINOKI_LOD3_BUILD_OK` and closes all documents.
- [ ] Commit:

```powershell
git add -- cad/lod3-inferred-prototype-01/hinoki_lod3_common.py cad/lod3-inferred-prototype-01/hinoki_lod3_display_housing.py cad/lod3-inferred-prototype-01/build_hinoki_lod3_master.py tests/test_hinoki_lod3_inferred.py
git commit -m "feat: build LOD 3 head and display stack"
```

## Task 4: Add electronics and the passive thermal path

**Files:**

- Create: `cad/lod3-inferred-prototype-01/hinoki_lod3_electronics_thermal.py`
- Modify: `cad/lod3-inferred-prototype-01/build_hinoki_lod3_master.py`
- Modify: `tests/test_hinoki_lod3_inferred.py`

- [ ] Test named board envelopes, mounting holes, shields, connectors, package solids, TIM/spreader/heat-pipe/chassis/hatch contacts, material coverage, and ten heat loads summing exactly 57 W.
- [ ] Run RED:

```powershell
python -B -m unittest tests.test_hinoki_lod3_inferred.TestElectronicsThermalGeometry -v
```

Expected: electronics subsystem group membership and geometry assertions fail.

- [ ] Implement carrier 250 × 140 × 1.6, SOM 90 × 70 × 1.6, power 160 × 100 × 1.6, I/O 180 × 30 × 1.6, Wi-Fi 30 × 20 × 3, major ICs/shields/connectors, QC7790 35 × 35 × 2, TIM 35 × 35 × 1, copper spreader 100 × 80 × 2, two 6 mm heat pipes, aluminium interface 220 × 120 × 2.5, and rear-hatch TIM 80 × 40 × 1.5.
- [ ] Run GREEN. Expected: electronics/thermal tests pass with no solid missing metadata.
- [ ] Commit:

```powershell
git add -- cad/lod3-inferred-prototype-01/hinoki_lod3_electronics_thermal.py cad/lod3-inferred-prototype-01/build_hinoki_lod3_master.py tests/test_hinoki_lod3_inferred.py
git commit -m "feat: add LOD 3 electronics and thermal path"
```

## Task 5: Add camera, lights, sensors, audio, and I/O (head-only)

The current approved checkpoint closes Task 5 only. Physical cable-route solids and bend validation are excluded; connector cutouts/service clearances remain validated. Task 6 stand/base is deferred.

**Files:**

- Create: `cad/lod3-inferred-prototype-01/hinoki_lod3_av_io.py`
- Modify: `cad/lod3-inferred-prototype-01/build_hinoki_lod3_master.py`
- Modify: `tests/test_hinoki_lod3_inferred.py`

- [x] Test the 38 × 38 × 25.78 camera module, 104 × 46 × 32 barrel, captive shutter travel, two 120 × 8 × 8 light bars, 59.8 × 18 × 16.3 radar holder, ALS path, two 40 mm speakers, two 50 × 25 radiators, two microphones, and the six approved port types.
- [ ] Run RED:

```powershell
python -B -m unittest tests.test_hinoki_lod3_inferred.TestAvIoGeometry -v
```

Expected: named AV/I/O parts are absent.

- [x] Implement the subsystem with optical and acoustic keep-outs. Represent ports and clearance holes explicitly. Physical cable routes and bend validation are outside this approved checkpoint scope.
- [x] Run GREEN. AV/I/O tests pass and all geometry stays within the head envelope.
- [x] Current checkpoint commit:

```powershell
git add -- cad/lod3-inferred-prototype-01/hinoki_lod3_av_io.py cad/lod3-inferred-prototype-01/build_hinoki_lod3_master.py tests/test_hinoki_lod3_inferred.py
git commit -m "fix: close LOD 3 AV IO head scope"
```

## Task 6: Build the stand, base, and kinematic extrema (deferred)

Task 6 is deferred by user decision in the current handoff. No stand/base solids, kinematic validation, or full-product assembly/STP claim is made for this checkpoint.

**Files:**

- Create: `cad/lod3-inferred-prototype-01/hinoki_lod3_stand.py`
- Modify: `cad/lod3-inferred-prototype-01/build_hinoki_lod3_master.py`
- Modify: `tests/test_hinoki_lod3_inferred.py`

- [ ] Test VESA 100 × 100 M4 holes, 140 × 140 × 4 plate, yoke, swivel, lift carriage, dual guides, assist proxy, hard stops, cable path, covers, 520 × 225 base, 500 × 205 × 6 steel plate, feet, 100 mm lift, ±10° tilt, ±20° swivel, and overall height 521–621 mm.
- [ ] Add posture probes for `(height, tilt, swivel)` at every min/max combination. Assert no unauthorised intersection above 0.01 mm³ and projected centre-of-mass support margin at least 25 mm.
- [ ] Run RED:

```powershell
python -B -m unittest tests.test_hinoki_lod3_inferred.TestStandKinematics -v
```

Expected: stand module missing and posture assertions fail.

- [ ] Implement transform functions that derive every posture from one nominal assembly. Keep motion envelopes/reference objects in `08_Reference_Datums_Keepouts`; keep physical parts in `06_Stand_Base_Kinematics`.
- [ ] Run GREEN. Expected: all extrema pass, overall depth stays at or below 225.1 mm, and no self-interference is reported.
- [ ] Commit:

```powershell
git add -- cad/lod3-inferred-prototype-01/hinoki_lod3_stand.py cad/lod3-inferred-prototype-01/build_hinoki_lod3_master.py tests/test_hinoki_lod3_inferred.py
git commit -m "feat: build LOD 3 stand and kinematics"
```

## Task 7: Validate the head-only Task 5 checkpoint

**Files:**

- Create: `cad/lod3-inferred-prototype-01/review_hinoki_lod3.py`
- Modify: `cad/lod3-inferred-prototype-01/build_hinoki_lod3_master.py`
- Modify: `tests/test_hinoki_lod3_inferred.py`

- [ ] Test head-only semantic physical parts, eight-group ownership, positive valid volumes, complete metadata, exact authorised-contact matrix, forbidden-overlap threshold 0.01 mm³, required feature evidence, head envelope ±0.1 mm, and failure sentinel uniqueness. Stand envelopes and motion gates are deferred with Task 6.
- [ ] Run RED:

```powershell
python -B -m unittest tests.test_hinoki_lod3_inferred.TestMasterValidation -v
```

Expected: review JSON is absent and integrated part-count/contact gates fail.

- [ ] Implement `validate_master()` returning machine-readable head-only checks and an overall `Pass` only when every active hard gate passes. Record limitations verbatim and never convert assumptions into known values.
- [ ] Run GREEN. Expected: temporary head-only validation reports `Pass` and zero forbidden overlap failures; no stand envelope or motion gate is evaluated.
- [ ] Commit:

```powershell
git add -- cad/lod3-inferred-prototype-01/review_hinoki_lod3.py cad/lod3-inferred-prototype-01/build_hinoki_lod3_master.py tests/test_hinoki_lod3_inferred.py
git commit -m "feat: validate integrated LOD 3 master"
```

## Task 8: Export the approved head-only STEP package

**Files:**

- Create: `cad/lod3-inferred-prototype-01/export_hinoki_lod3.py`
- Modify: `tests/test_hinoki_lod3_inferred.py`

- [ ] Test same-directory staging, head STEP/manifest/validation reopen, millimetre scale, expected head semantic-body membership, rollback preserving old bytes, temp cleanup, and all FreeCAD documents closed. Full-product and stand/base STEP outputs are deferred and are not active gates.
- [ ] Run RED:

```powershell
python -B -m unittest tests.test_hinoki_lod3_inferred.TestAtomicExport -v
```

Expected: exporter missing and rollback assertions fail.

- [ ] Implement staged export to the exact approved head-only filenames. Reopen and validate the active set before replacing any formal artifact.
- [ ] Run GREEN. Expected: the temporary head STEP and required JSON files reopen, deliberate injected failure preserves prior bytes, and no temp files remain.
- [ ] Commit:

```powershell
git add -- cad/lod3-inferred-prototype-01/export_hinoki_lod3.py tests/test_hinoki_lod3_inferred.py
git commit -m "feat: export atomic LOD 3 STEP package"
```

## Task 9: Generate phone-review images

**Files:**

- Create: `cad/lod3-inferred-prototype-01/preview_hinoki_lod3.py`
- Modify: `tests/test_hinoki_lod3_inferred.py`

- [ ] Test creation of front, rear, isometric, exploded, and airflow-cutaway PNGs at minimum 1600 × 1200, white background, shaded-with-edges draw style, readable file size, and atomic replacement.
- [ ] Run RED:

```powershell
python -B -m unittest tests.test_hinoki_lod3_inferred.TestReviewImages -v
```

Expected: preview files are missing.

- [ ] Implement deterministic cameras, semantic colors, translucent rear housing for isometric/cutaway, and arrows/labels only in the airflow view. Do not ray-trace or photorealistically render.
- [ ] Run GREEN. Expected: five temporary PNGs pass dimension and reopen checks.
- [ ] Commit:

```powershell
git add -- cad/lod3-inferred-prototype-01/preview_hinoki_lod3.py tests/test_hinoki_lod3_inferred.py
git commit -m "feat: add LOD 3 mobile review views"
```

## Task 10: Derive the controlled FLOEFD package

**Files:**

- Create: `cad/lod3-inferred-prototype-01/derive_hinoki_lod3_floefd.py`
- Modify: `tests/test_hinoki_lod3_inferred.py`

- [ ] Test explicit Keep/Aggregate/Suppress disposition for every master part, one connected internal air, air/solid overlap at most 0.01 mm³, connected unobstructed inlet/outlet, each opening at least 6000 mm² or recorded impedance equivalent, exact ten-source 57 W map, complete materials, master-envelope containment, and stand/base exclusion from the internal-air package.
- [ ] Run RED:

```powershell
python -B -m unittest tests.test_hinoki_lod3_inferred.TestFloefdDerivation -v
```

Expected: suppression map and derived files are missing.

- [ ] Implement deterministic derivation from validated master only. Subtract retained solids from the sealed internal cavity, connect the two approved vent fields, and reject multiple air solids. Publish solids STEP, internal-air STEP, setup JSON, and review JSON atomically.
- [ ] Run GREEN. Expected: derived review says `Pass`, internal air has one solid, and heat sum is 57.0 W.
- [ ] Commit:

```powershell
git add -- cad/lod3-inferred-prototype-01/derive_hinoki_lod3_floefd.py tests/test_hinoki_lod3_inferred.py
git commit -m "feat: derive LOD 3 FLOEFD handoff"
```

## Task 11: Publish formal artifacts and handoff documentation

**Files:**

- Create: all approved formal files below `cad/lod3-inferred-prototype-01/`
- Modify: `README.md`
- Modify: `tests/test_hinoki_lod3_inferred.py`

- [ ] Add formal-artifact probes for exact filenames, independent reopen, manifest count/schema, validation `Pass`, review image dimensions, FLOEFD case values, and limitation wording.
- [ ] Run all LOD 3 tests against temporary outputs first:

```powershell
python -B -m unittest tests.test_hinoki_lod3_inferred -v
```

Expected: all LOD 3 tests pass.

- [ ] Run the builder, validator, exporter, image generator, and FLOEFD derivation once with formal paths. Expected sentinels: `HINOKI_LOD3_BUILD_OK`, `HINOKI_LOD3_REVIEW_OK`, `HINOKI_LOD3_EXPORT_OK`, `HINOKI_LOD3_PREVIEW_OK`, `HINOKI_LOD3_FLOEFD_OK`.
- [ ] Rerun formal-artifact tests and the existing thermal regression suite:

```powershell
python -B -m unittest tests.test_hinoki_lod3_inferred tests.test_hinoki_thermal_cht -v
```

Expected: all tests pass; the existing 16-solid/1-air thermal package remains unchanged.

- [ ] Update `README.md` with exact downloads, build/review/export commands, Simcenter FLOEFD import steps, source hierarchy, and non-release limitations while keeping the README below 250 lines.
- [ ] Verify no placeholders, whitespace errors, or unrelated artifact changes:

```powershell
rg -n "manufacturing release|placeholder|pending decision" cad/lod3-inferred-prototype-01 README.md docs/superpowers/plans/2026-09-02-hinoki-lod3-inferred-engineering-prototype-plan.md
git diff --check
git status --short
```

Expected: only intentional limitation phrases match; `git diff --check` is silent; unrelated Iteration and thermal preview files remain untracked/unmodified.

- [ ] Commit the formal handoff:

```powershell
git add -- cad/lod3-inferred-prototype-01 README.md tests/test_hinoki_lod3_inferred.py
git commit -m "feat: deliver Hinoki LOD 3 inferred prototype"
```

## Final review gate

- [ ] Confirm the plan covers all 13 sections of `docs/superpowers/specs/2026-09-02-hinoki-lod3-inferred-engineering-prototype-design.md`.
- [ ] Confirm every parameter is numeric in millimetres/watts/degrees/°C as declared and JSON serialisation uses the same units.
- [ ] Confirm there are no unresolved markers, generic test instructions, or cross-task placeholders in implementation files.
- [ ] Confirm `ManufacturingAuthority` is false for every manifest row and the validation report retains the inferred-prototype limitation.
- [ ] Confirm exact formal outputs reopen independently and old Iteration 01/02 assets were neither rewritten nor staged.
