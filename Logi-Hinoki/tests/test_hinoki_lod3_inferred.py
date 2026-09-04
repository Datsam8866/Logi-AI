"""Contract and geometry tests for the Hinoki LOD 3 inferred prototype."""

from importlib.util import module_from_spec, spec_from_file_location
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = PROJECT_ROOT / "cad" / "lod3-inferred-prototype-01"
PARAMETERS_FILE = PACKAGE_ROOT / "hinoki_lod3_parameters.py"
SOURCES_FILE = PACKAGE_ROOT / "hinoki_lod3_sources.py"
BUILD_SCRIPT = PACKAGE_ROOT / "build_hinoki_lod3_master.py"
REVIEW_SCRIPT = PACKAGE_ROOT / "review_hinoki_lod3.py"
AV_IO_FILE = PACKAGE_ROOT / "hinoki_lod3_av_io.py"
SOURCE_INDEXER = PACKAGE_ROOT / "index_hinoki_lod3_sources.py"
PLAN_FILE = PROJECT_ROOT / "docs" / "superpowers" / "plans" / "2026-09-02-hinoki-lod3-inferred-engineering-prototype-plan.md"
SPEC_FILE = PROJECT_ROOT / "docs" / "superpowers" / "specs" / "2026-09-02-hinoki-lod3-inferred-engineering-prototype-design.md"
FREECAD_CMD = Path(
    os.environ.get(
        "FREECAD_CMD",
        r"C:\Users\skuan1\AppData\Local\Programs\FreeCAD 1.1\bin\freecadcmd.exe",
    )
)


def load_module(path, name):
    spec = spec_from_file_location(name, path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_freecad_script(script_path, env, timeout=180):
    source = script_path.read_text(encoding="utf-8")
    launcher = "source = {!r}\nexec(compile(source, {!r}, 'exec'))\n".format(
        source, str(script_path)
    )
    return subprocess.run(
        [str(FREECAD_CMD), "-c"],
        cwd=Path(tempfile.gettempdir()),
        env=env,
        input=launcher,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


class TestSourceInventory(unittest.TestCase):
    FIXTURES = {
        "Hinoki_Master_Parameters_and_Assumption_Log.xlsx": b"hinoki-parameters",
        "Dixie and Hinoki table.xlsx": b"hinoki-dixie-table",
        "Dixie/3D/001_dixie65_set_asm_20250425_asm.stp": (
            b"DIXIE_STEP_BINARY_BYTES_DO_NOT_COPY" + b"x" * (1024 * 1024 + 17)
        ),
        "Dixie/BOM/logitech_Dixie65_Parts list_REV_20250506V1.xlsx": (
            b"dixie-bom"
        ),
        "Dixie/2D/main-housing.pdf": b"dixie-2d",
        "Dixie/Panel/panel-data.xlsx": b"dixie-panel",
        "Dixie/Thermal/thermal-pad-drawing.pdf": b"dixie-thermal",
    }

    def _write_fixtures(self, source_root, excluded=()):
        for relative_path, content in self.FIXTURES.items():
            if relative_path in excluded:
                continue
            fixture_path = source_root / relative_path
            fixture_path.parent.mkdir(parents=True, exist_ok=True)
            fixture_path.write_bytes(content)

    def test_index_records_external_reference_authority_without_source_bytes(self):
        self.assertTrue(SOURCE_INDEXER.exists(), "source indexer must exist")
        indexer = load_module(SOURCE_INDEXER, "index_hinoki_lod3_sources")
        with tempfile.TemporaryDirectory(prefix="hinoki_lod3_sources_") as temp_dir:
            temp_root = Path(temp_dir)
            source_root = temp_root / "references"
            output_path = temp_root / "hinoki_lod3_source_index.json"
            self._write_fixtures(source_root)

            result = indexer.build_source_index(source_root, output_path)

            self.assertEqual(
                result,
                json.loads(output_path.read_text(encoding="utf-8")),
            )
            records = {record["path"]: record for record in result["sources"]}
            self.assertEqual(set(self.FIXTURES), set(records))
            self.assertGreater(
                len(
                    self.FIXTURES[
                        "Dixie/3D/001_dixie65_set_asm_20250425_asm.stp"
                    ]
                ),
                1024 * 1024,
            )
            for relative_path, content in self.FIXTURES.items():
                record = records[relative_path]
                self.assertEqual(
                    {
                        "path",
                        "sha256",
                        "byte_size",
                        "authority_class",
                        "external_reference",
                        "copied_into_repository",
                    },
                    set(record),
                )
                self.assertEqual(
                    hashlib.sha256(content).hexdigest(),
                    record["sha256"],
                )
                self.assertEqual(len(content), record["byte_size"])
                expected_authority = (
                    "Known"
                    if not relative_path.startswith("Dixie/")
                    else "DixieReference"
                )
                self.assertEqual(expected_authority, record["authority_class"])
                self.assertTrue(record["external_reference"])
                self.assertFalse(record["copied_into_repository"])

            self.assertIn(
                {
                    "literal": "14498.4 mm",
                    "reason": (
                        "Conflicts with approved 742 mm Hinoki envelope; "
                        "uniform Dixie scaling is prohibited."
                    ),
                },
                result["rejected_literals"],
            )
            self.assertNotIn(
                self.FIXTURES[
                    "Dixie/3D/001_dixie65_set_asm_20250425_asm.stp"
                ],
                output_path.read_bytes(),
            )

    def test_publish_failure_preserves_existing_output_and_cleans_temp(self):
        indexer = load_module(SOURCE_INDEXER, "index_hinoki_lod3_sources_atomic")
        with tempfile.TemporaryDirectory(prefix="hinoki_lod3_atomic_") as temp_dir:
            temp_root = Path(temp_dir)
            source_root = temp_root / "references"
            output_path = temp_root / "hinoki_lod3_source_index.json"
            self._write_fixtures(source_root)
            original = b"existing-source-index"
            output_path.write_bytes(original)

            real_os = getattr(indexer, "os", None)

            class FailingOS:
                @staticmethod
                def replace(source, target):
                    raise OSError("injected publish failure")

            indexer.os = FailingOS
            try:
                with self.assertRaisesRegex(OSError, "injected publish failure"):
                    indexer.build_source_index(source_root, output_path)
            finally:
                if real_os is None:
                    del indexer.os
                else:
                    indexer.os = real_os

            self.assertEqual(original, output_path.read_bytes())
            self.assertEqual(
                [],
                list(temp_root.glob(output_path.name + ".*.tmp")),
            )

    def test_each_build_returns_independent_rejected_literal_data(self):
        indexer = load_module(SOURCE_INDEXER, "index_hinoki_lod3_sources_copy")
        with tempfile.TemporaryDirectory(prefix="hinoki_lod3_copy_") as temp_dir:
            temp_root = Path(temp_dir)
            source_root = temp_root / "references"
            output_path = temp_root / "hinoki_lod3_source_index.json"
            self._write_fixtures(source_root)

            first = indexer.build_source_index(source_root, output_path)
            first["rejected_literals"][0]["literal"] = "tampered"
            second = indexer.build_source_index(source_root, output_path)

            self.assertEqual(
                "14498.4 mm",
                second["rejected_literals"][0]["literal"],
            )

    def test_source_change_during_hash_fails_without_publishing(self):
        indexer = load_module(SOURCE_INDEXER, "index_hinoki_lod3_sources_change")
        with tempfile.TemporaryDirectory(prefix="hinoki_lod3_change_") as temp_dir:
            temp_root = Path(temp_dir)
            source_root = temp_root / "references"
            output_path = temp_root / "hinoki_lod3_source_index.json"
            self._write_fixtures(source_root)
            original = b"existing-source-index"
            output_path.write_bytes(original)
            changing_path = (
                source_root / "Hinoki_Master_Parameters_and_Assumption_Log.xlsx"
            )

            real_open = open

            class ChangingReader:
                def __init__(self, handle):
                    self.handle = handle
                    self.changed = False

                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc_value, traceback):
                    self.handle.close()

                def read(self, size):
                    data = self.handle.read(size)
                    if not self.changed:
                        stat = changing_path.stat()
                        os.utime(
                            changing_path,
                            ns=(stat.st_atime_ns, stat.st_mtime_ns + 2_000_000_000),
                        )
                        self.changed = True
                    return data

            def changing_open(path, mode):
                handle = real_open(path, mode)
                if Path(path) == changing_path and mode == "rb":
                    return ChangingReader(handle)
                return handle

            indexer.open = changing_open
            try:
                with self.assertRaisesRegex(RuntimeError, "changed during indexing"):
                    indexer.build_source_index(source_root, output_path)
            finally:
                del indexer.open

            self.assertEqual(original, output_path.read_bytes())
            self.assertEqual(
                [],
                list(temp_root.glob(output_path.name + ".*.tmp")),
            )

    def test_index_fails_when_a_required_source_group_is_missing(self):
        self.assertTrue(SOURCE_INDEXER.exists(), "source indexer must exist")
        indexer = load_module(SOURCE_INDEXER, "index_hinoki_lod3_sources_missing")
        with tempfile.TemporaryDirectory(
            prefix="hinoki_lod3_sources_missing_"
        ) as temp_dir:
            temp_root = Path(temp_dir)
            source_root = temp_root / "references"
            output_path = temp_root / "hinoki_lod3_source_index.json"
            missing = "Dixie/Thermal/thermal-pad-drawing.pdf"
            self._write_fixtures(source_root, excluded=(missing,))

            with self.assertRaisesRegex(FileNotFoundError, r"Dixie[/\\]Thermal"):
                indexer.build_source_index(source_root, output_path)
            self.assertFalse(output_path.exists())


class TestFrozenEngineeringContract(unittest.TestCase):
    def test_collision_clearance_contract(self):
        p = load_module(PARAMETERS_FILE, "hinoki_lod3_parameters_clearance")
        self.assertEqual(
            ((321.0, 196.0), (421.0, 196.0), (321.0, 296.0), (421.0, 296.0)),
            p.VESA_MOUNT_POINTS,
        )
        self.assertEqual(0.5, p.COLLISION_CLEARANCE["linear"])
        self.assertEqual(0.5, p.COLLISION_CLEARANCE["radial"])
        self.assertEqual(0.8, p.COLLISION_CLEARANCE["shield_wall"])
        # After Task 8 quality remediation, corner and VESA bosses root on
        # the mid-frame lap with a 0.5 mm interference-fit engagement so
        # boss<->mid_frame contact is boolean-continuous (not just plane-
        # touching). Boss base sits at z=24.5, top at z=59.2 (34.7 mm tall).
        self.assertEqual(24.5, p.COLLISION_CLEARANCE["rear_boss_z"])
        self.assertEqual(34.7, p.COLLISION_CLEARANCE["rear_boss_height"])
        self.assertEqual(34.7, p.COLLISION_CLEARANCE["vesa_boss_height"])
        self.assertEqual(0.5, p.COLLISION_CLEARANCE["boss_root_engagement"])

    def test_frozen_product_envelope_and_display_stack(self):
        p = load_module(PARAMETERS_FILE, "hinoki_lod3_parameters")
        self.assertEqual((742.0, 492.0, 62.0), tuple(p.HEAD.values()))
        self.assertEqual(
            (726.0, 446.0, 3.2),
            tuple(p.DISPLAY_STACK["Cover_Glass"].values()),
        )
        self.assertEqual(
            6000.0,
            p.VENTS["Inlet_Lower_Rear"]["minimum_open_area"],
        )
        self.assertEqual(
            (
                "01_Display_Stack",
                "02_Housing_Structure",
                "03_Electronics_Thermal",
                "04_Camera_Lighting_Sensors",
                "05_Audio_IO_Cables",
                "06_Stand_Base_Kinematics",
                "07_Fasteners_Seals_Consumables",
                "08_Reference_Datums_Keepouts",
            ),
            p.REQUIRED_TOP_GROUPS,
        )

    def test_source_precedence_rejects_uniform_dixie_scale(self):
        s = load_module(SOURCES_FILE, "hinoki_lod3_sources")
        result = s.resolve_candidates(
            "HeadWidth",
            (
                {
                    "source_class": "DixieReference",
                    "value": 14498.4,
                    "source_reference": "Dixie conflicting literal",
                },
                {
                    "source_class": "Known",
                    "value": 742.0,
                    "source_reference": "Approved Hinoki baseline",
                },
            ),
        )
        self.assertEqual(742.0, result["value"])
        self.assertEqual("Known", result["source_class"])
        self.assertEqual(1, len(result["rejected_candidates"]))
        self.assertFalse(s.UNIFORM_DIXIE_SCALE_POLICY["allowed"])
        self.assertEqual("MP-077", s.UNIFORM_DIXIE_SCALE_POLICY["parameter_id"])

    def test_thermal_case_is_exactly_57_w(self):
        p = load_module(PARAMETERS_FILE, "hinoki_lod3_parameters")
        self.assertEqual(35.0, p.THERMAL_CASE["ambient_c"])
        self.assertEqual("NaturalConvection", p.THERMAL_CASE["cooling_mode"])
        self.assertFalse(p.THERMAL_CASE["fan_present"])
        self.assertEqual(13, len(p.HEAT_LOADS_W))
        self.assertAlmostEqual(57.0, sum(p.HEAT_LOADS_W.values()), places=9)
        self.assertAlmostEqual(20.0, p.PANEL_MODULE_BUDGET_W, places=9)
        panel_ids = p.HEAT_BUDGET_GROUPS["Panel_Module"]
        self.assertAlmostEqual(
            20.0,
            sum(p.HEAT_LOADS_W[name] for name in panel_ids),
            places=9,
        )
        self.assertNotIn("Heat_Panel_Backlight", p.HEAT_LOADS_W)

    def test_active_output_contract_is_head_only(self):
        p = load_module(PARAMETERS_FILE, "hinoki_lod3_parameters_output_contract")
        self.assertEqual(
            {
                "master_fcstd",
                "head_step",
                "manifest_json",
                "validation_json",
            },
            set(p.OUTPUT_FILES),
        )
        self.assertNotIn("full_step", p.OUTPUT_FILES)
        self.assertNotIn("stand_base_step", p.OUTPUT_FILES)
        self.assertTrue(
            all(
                "full" not in filename.lower()
                and "stand" not in filename.lower()
                for filename in p.OUTPUT_FILES.values()
            )
        )

        plan = PLAN_FILE.read_text(encoding="utf-8")
        task7 = plan.split("## Task 7", 1)[1].split("## Task 8", 1)[0].lower()
        task8 = plan.split("## Task 8", 1)[1].split("## Task 9", 1)[0].lower()
        self.assertIn("head-only", task7)
        self.assertNotIn("head/stand envelope", task7)
        self.assertNotIn("stand motion and interference evidence pass", task7)
        self.assertIn("head-only", task8)
        self.assertNotIn("full_assembly.step", task8)
        self.assertNotIn("stand_base.step", task8)

        spec = SPEC_FILE.read_text(encoding="utf-8")
        outputs = spec.split("## 9. Outputs", 1)[1].split("## 10.", 1)[0]
        self.assertIn("Hinoki_LOD3_Head.step", outputs)
        self.assertNotIn("Hinoki_LOD3_Full_Assembly.step", outputs)
        self.assertNotIn("Hinoki_LOD3_Stand_Base.step", outputs)

    def test_manifest_schema_denies_manufacturing_authority(self):
        p = load_module(PARAMETERS_FILE, "hinoki_lod3_parameters")
        record = p.part_metadata(
            part_id="HNK-DS-001",
            part_name="Cover_Glass",
            parent_assembly="01_Display_Stack",
            material_intent="Display glass",
            source_class="EngineeringAssumption",
            source_reference="Approved LOD 3 design section 5.1",
            confidence="Medium",
            thermal_disposition="Keep",
            heat_load_w=0.0,
        )
        self.assertEqual(set(p.METADATA_KEYS), set(record))
        self.assertIs(False, record["ManufacturingAuthority"])
        self.assertEqual("A", record["Revision"])
        self.assertIn("not manufacturing release", p.PROTOTYPE_LIMITATION.lower())


class TestDisplayHousingGeometry(unittest.TestCase):
    def test_builder_creates_controlled_head_and_display_stack(self):
        with tempfile.TemporaryDirectory(prefix="hinoki_lod3_head_") as temp_dir:
            model_path = Path(temp_dir) / "Hinoki_LOD3_Head_Test.FCStd"
            env = os.environ.copy()
            env["HINOKI_LOD3_MODEL_OUT"] = str(model_path)
            result = run_freecad_script(BUILD_SCRIPT, env)
            combined_output = result.stdout + result.stderr
            self.assertEqual(
                0,
                result.returncode,
                msg=combined_output,
            )
            self.assertIn("HINOKI_LOD3_BUILD_OK", combined_output)
            self.assertTrue(model_path.exists())

            probe = r"""
import FreeCAD as App

doc = App.open(r"{model_path}")
expected_groups = {groups!r}
actual_groups = tuple(
    obj.Label for obj in doc.Objects
    if obj.TypeId == "App::DocumentObjectGroup"
)
assert actual_groups == expected_groups, actual_groups

head_parts = [
    obj for obj in doc.Objects
    if hasattr(obj, "Shape")
    and not obj.Shape.isNull()
    and getattr(obj, "IsSemanticPart", False)
    and getattr(obj, "ParentAssembly", "") != "08_Reference_Datums_Keepouts"
]
box = head_parts[0].Shape.BoundBox
for obj in head_parts[1:]:
    box.add(obj.Shape.BoundBox)
assert abs(box.XLength - 742.0) <= 0.1, box.XLength
assert abs(box.YLength - 492.0) <= 0.1, box.YLength
assert abs(box.ZLength - 62.0) <= 0.1, box.ZLength

expected_layers = {{
    "Cover_Glass": (726.0, 446.0, 3.2),
    "PCAP_Sensor": (724.0, 444.0, 0.8),
    "Optical_Bond": (724.0, 444.0, 0.5),
    "LCD_Cell": (712.0, 402.0, 2.5),
    "BLU_Optical_Films": (716.0, 406.0, 1.5),
    "Light_Guide_Plate": (716.0, 406.0, 4.0),
    "Panel_Backplate": None,
}}
for name, dimensions in expected_layers.items():
    obj = doc.getObject(name)
    assert obj is not None and obj.Shape.isValid() and obj.Shape.Volume > 0.0
    if dimensions is not None:
        actual = (obj.Shape.BoundBox.XLength, obj.Shape.BoundBox.YLength, obj.Shape.BoundBox.ZLength)
        assert all(abs(a - b) <= 0.01 for a, b in zip(actual, dimensions)), (name, actual)
    assert obj.ManufacturingAuthority is False
    assert obj.SourceReference

assert doc.getObject("Backlight_Unit") is None, "old monolithic BLU must be removed"

rear = doc.getObject("Rear_Enclosure")
assert rear.Shape.isValid() and rear.Shape.Volume > 0.0
assert abs(rear.WallThickness.Value - 2.8) <= 0.001
assert abs(rear.InletOpenArea.Value - 6000.0) <= 0.1
assert abs(rear.OutletOpenArea.Value - 6000.0) <= 0.1
assert rear.RibFeatureCount >= 4, rear.RibFeatureCount
assert rear.RibHostPart == "Rear_Enclosure", rear.RibHostPart
assert len(tuple(rear.RibFeatureIds)) == rear.RibFeatureCount
assert doc.getObject("Structural_Rib_01") is None, "standalone rib parts must be fused into rear cover"

boss = doc.getObject("Primary_Boss_01")
assert abs(boss.BossOuterDiameter.Value - 7.0) <= 0.001
assert boss.HostPart == "Metal_Mid_Frame"
vesa_boss = doc.getObject("VESA_Boss_01")
assert vesa_boss is not None and vesa_boss.HostPart == "Metal_Mid_Frame"
mid_frame = doc.getObject("Metal_Mid_Frame")
assert mid_frame is not None and mid_frame.Shape.isValid() and mid_frame.Shape.Volume > 0.0
assert abs(mid_frame.PerimeterWallThickness.Value - 2.0) <= 0.001
assert doc.getObject("Front_Bezel") is not None, "renamed front frame must exist as Front_Bezel"
assert doc.getObject("Front_Frame") is None, "old Front_Frame name must be gone"
assert doc.getObject("VESA_Reinforcement") is None, "VESA reinforcement must fuse into mid-frame"
assert doc.getObject("Inlet_Vent_Field").Shape.Solids
assert doc.getObject("Outlet_Vent_Field").Shape.Solids

for obj in head_parts:
    assert obj.Shape.isValid() and obj.Shape.Volume > 0.0, obj.Name
    assert obj.PartID and obj.PartName and obj.ParentAssembly
    assert obj.MaterialIntent and obj.SourceClass and obj.SourceReference
    assert obj.Confidence and obj.ThermalDisposition and obj.Revision
    assert obj.ManufacturingAuthority is False

App.closeDocument(doc.Name)
assert not App.listDocuments()
print("HINOKI_LOD3_HEAD_PROBE_OK parts={{}}".format(len(head_parts)))
""".format(
                model_path=model_path.as_posix(),
                groups=(
                    "01_Display_Stack",
                    "02_Housing_Structure",
                    "03_Electronics_Thermal",
                    "04_Camera_Lighting_Sensors",
                    "05_Audio_IO_Cables",
                    "06_Stand_Base_Kinematics",
                    "07_Fasteners_Seals_Consumables",
                    "08_Reference_Datums_Keepouts",
                ),
            )
            probe_result = subprocess.run(
                [str(FREECAD_CMD), "-c"],
                cwd=Path(tempfile.gettempdir()),
                input="exec({!r})\n".format(probe),
                capture_output=True,
                text=True,
                check=False,
                timeout=180,
            )
            self.assertEqual(
                0,
                probe_result.returncode,
                msg=probe_result.stdout + probe_result.stderr,
            )
            self.assertIn(
                "HINOKI_LOD3_HEAD_PROBE_OK",
                probe_result.stdout + probe_result.stderr,
            )


class TestElectronicsThermalGeometry(unittest.TestCase):
    def test_builder_adds_boards_heat_sources_and_passive_path(self):
        with tempfile.TemporaryDirectory(prefix="hinoki_lod3_et_") as temp_dir:
            model_path = Path(temp_dir) / "Hinoki_LOD3_ET_Test.FCStd"
            env = os.environ.copy()
            env["HINOKI_LOD3_MODEL_OUT"] = str(model_path)
            result = run_freecad_script(BUILD_SCRIPT, env)
            combined_output = result.stdout + result.stderr
            self.assertEqual(0, result.returncode, combined_output)
            self.assertIn("HINOKI_LOD3_BUILD_OK", combined_output)

            probe = r"""
import FreeCAD as App

doc = App.open(r"{model_path}")
expected_boards = {{
    "Carrier_PCB": (250.0, 140.0, 1.6),
    "Compute_SOM_PCB": (90.0, 70.0, 1.6),
    "Power_PCB": (160.0, 100.0, 1.6),
    "IO_PCB": (180.0, 30.0, 1.6),
    "WiFi_BLE_Module": (30.0, 20.0, 3.0),
}}
for name, expected in expected_boards.items():
    obj = doc.getObject(name)
    assert obj is not None and obj.Shape.isValid() and obj.Shape.Volume > 0.0, name
    actual = (obj.Shape.BoundBox.XLength, obj.Shape.BoundBox.YLength, obj.Shape.BoundBox.ZLength)
    assert all(abs(a - b) <= 0.01 for a, b in zip(actual, expected)), (name, actual)
    assert len(obj.Shape.Edges) > 12, name + " must include mounting-hole evidence"

expected_thermal = {{
    # Iter 2 (Task 8): thermal components extended so adjacent solids in
    # the QC7790->rear cover conduction chain have a small (0.1..0.4 mm)
    # authorised contact overlap instead of unbuilt plane touches, and
    # Aluminum_Interface + Rear_Hatch_TIM are resized to close the historic
    # 11 mm air-gap between the heat spreader and the rear I/O cover.
    "Heat_QC7790": (35.0, 35.0, 2.1),
    "TIM_QC7790": (35.0, 35.0, 1.2),
    "Copper_Spreader": (100.0, 80.0, 2.2),
    "Aluminum_Interface": (128.0, 120.0, 13.9),
    "Rear_Hatch_TIM": (80.0, 40.0, 5.4),
}}
for name, expected in expected_thermal.items():
    obj = doc.getObject(name)
    assert obj is not None and obj.Shape.isValid() and obj.Shape.Volume > 0.0, name
    actual = (obj.Shape.BoundBox.XLength, obj.Shape.BoundBox.YLength, obj.Shape.BoundBox.ZLength)
    assert all(abs(a - b) <= 0.01 for a, b in zip(actual, expected)), (name, actual)

for name in ("Heat_Pipe_Left", "Heat_Pipe_Right"):
    obj = doc.getObject(name)
    assert obj.Shape.isValid() and obj.Shape.Volume > 0.0
    assert abs(obj.Diameter.Value - 6.0) <= 0.001

heat_parts = [
    obj for obj in doc.Objects
    if getattr(obj, "IsSemanticPart", False) and obj.HeatLoadW > 0.0
]
assert len(heat_parts) == 13, [(obj.Name, obj.HeatLoadW) for obj in heat_parts]
assert abs(sum(obj.HeatLoadW for obj in heat_parts) - 57.0) <= 1e-9
assert {{obj.HeatSourceID for obj in heat_parts}} == {heat_names!r}
panel_ids = {{"Heat_BLU_LED", "Heat_BLU_Driver", "Heat_TCON", "Heat_Panel_Gate_Source"}}
panel_watts = sum(
    obj.HeatLoadW for obj in heat_parts if obj.HeatSourceID in panel_ids
)
assert abs(panel_watts - 20.0) <= 1e-9, panel_watts

lighting_heat = doc.getObject("Heat_Front_Lighting")
assert abs(lighting_heat.HeatLoadW - 4.0) <= 1e-9
assert tuple(lighting_heat.AuthorizedContactTargets) == (
    "Front_Light_Left",
    "Front_Light_Right",
)
for light_name in lighting_heat.AuthorizedContactTargets:
    light = doc.getObject(light_name)
    assert lighting_heat.Shape.common(light.Shape).Volume > 0.01, light_name
camera = doc.getObject("Camera_Module")
assert tuple(camera.AuthorizedContactTargets) == ("Heat_Camera",)
assert camera.Shape.common(lighting_heat.Shape).Volume <= 0.01

for obj in doc.Objects:
    if getattr(obj, "IsSemanticPart", False):
        assert obj.MaterialIntent and obj.SourceReference
        assert obj.ManufacturingAuthority is False

App.closeDocument(doc.Name)
assert not App.listDocuments()
print("HINOKI_LOD3_ELECTRONICS_THERMAL_PROBE_OK heat_parts={{}}".format(len(heat_parts)))
""".format(
                model_path=model_path.as_posix(),
                heat_names=set(
                    (
                        "Heat_BLU_LED",
                        "Heat_BLU_Driver",
                        "Heat_TCON",
                        "Heat_Panel_Gate_Source",
                        "Heat_QC7790",
                        "Heat_Memory",
                        "Heat_Carrier_PMIC",
                        "Heat_IO",
                        "Heat_WiFi_BLE",
                        "Heat_Camera",
                        "Heat_Audio",
                        "Heat_Radar_ALS",
                        "Heat_Front_Lighting",
                    )
                ),
            )
            probe_result = subprocess.run(
                [str(FREECAD_CMD), "-c"],
                cwd=Path(tempfile.gettempdir()),
                input="exec({!r})\n".format(probe),
                capture_output=True,
                text=True,
                check=False,
                timeout=180,
            )
            combined_probe = probe_result.stdout + probe_result.stderr
            self.assertEqual(0, probe_result.returncode, combined_probe)
            self.assertIn(
                "HINOKI_LOD3_ELECTRONICS_THERMAL_PROBE_OK",
                combined_probe,
            )


class TestAvIoGeometry(unittest.TestCase):
    def test_camera_fov_contract_and_forward_reference(self):
        p = load_module(PARAMETERS_FILE, "hinoki_lod3_parameters_fov")
        self.assertTrue(
            hasattr(p, "CAMERA_OPTICS"),
            "missing controlled CAMERA_OPTICS parameters",
        )
        optics = p.CAMERA_OPTICS
        self.assertEqual(140.0, optics["hfov_deg"])
        self.assertEqual(-1.0, optics["forward_axis_z"])
        self.assertEqual(0.0, optics["optical_origin_z"])
        self.assertGreater(optics["validation_distance"], 0.0)

        with tempfile.TemporaryDirectory(prefix="hinoki_lod3_fov_") as temp_dir:
            model_path = Path(temp_dir) / "Hinoki_LOD3_FOV_Test.FCStd"
            env = os.environ.copy()
            env["HINOKI_LOD3_MODEL_OUT"] = str(model_path)
            result = run_freecad_script(BUILD_SCRIPT, env)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

            probe = r"""
import math
import FreeCAD as App

doc = App.open(r"{model_path}")
fov = doc.getObject("Camera_FOV_Reference")
internal = doc.getObject("Camera_Optical_Keepout")
assert fov is not None and fov.GeometryRole == "ExternalOpticalReference"
assert fov.Shape.isValid() and fov.Shape.Volume > 0.0
assert abs(fov.HorizontalFOV - 140.0) <= 1e-9
assert abs(fov.ForwardAxisZ + 1.0) <= 1e-9
assert abs(fov.OpticalOriginZ.Value) <= 1e-9
assert abs(fov.ValidationDistance.Value - {distance}) <= 0.01
measured_hfov = math.degrees(
    2.0 * math.atan(fov.FarHalfWidth.Value / fov.ValidationDistance.Value)
)
assert abs(measured_hfov - 140.0) <= 0.01, measured_hfov
assert fov.Shape.BoundBox.ZMax <= 0.01
assert abs(fov.Shape.BoundBox.ZMin + {distance}) <= 0.01
assert internal is not None and internal.GeometryRole == "InternalOpticalKeepout"
assert internal.Shape.isValid() and internal.Shape.Volume > 0.0
assert internal.Shape.BoundBox.ZMin >= -0.01
assert internal.Shape.BoundBox.ZMax <= {internal_depth} + 0.01
App.closeDocument(doc.Name)
print("HINOKI_LOD3_FOV_PROBE_OK measured_hfov={{:.3f}}".format(measured_hfov))
""".format(
                model_path=model_path.as_posix(),
                distance=optics["validation_distance"],
                internal_depth=optics["lens_to_window_distance"],
            )
            probe_result = subprocess.run(
                [str(FREECAD_CMD), "-c"],
                cwd=Path(tempfile.gettempdir()),
                input="exec({!r})\n".format(probe),
                capture_output=True,
                text=True,
                check=False,
                timeout=180,
            )
            combined_probe = probe_result.stdout + probe_result.stderr
            self.assertEqual(0, probe_result.returncode, combined_probe)
            self.assertIn("HINOKI_LOD3_FOV_PROBE_OK", combined_probe)

    def test_av_cavity_prevents_hard_package_overlaps(self):
        with tempfile.TemporaryDirectory(prefix="hinoki_lod3_av_overlap_") as temp_dir:
            model_path = Path(temp_dir) / "Hinoki_LOD3_AV_Overlap_Test.FCStd"
            env = os.environ.copy()
            env["HINOKI_LOD3_MODEL_OUT"] = str(model_path)
            result = run_freecad_script(BUILD_SCRIPT, env)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

            probe = r"""
import FreeCAD as App

doc = App.open(r"{model_path}")
cavity = doc.getObject("AV_Cavity")
assert cavity is not None, "missing explicit AV_Cavity"
assert cavity.GeometryRole == "CavityReference"
assert cavity.Shape.isValid() and cavity.Shape.Volume > 0.0
assert cavity.AuthorizedContactIntent
barrel = doc.getObject("Camera_Barrel")
assert getattr(barrel, "GeometryRole", "") == "PackageEnvelope"
assert barrel.ParentAssembly == "08_Reference_Datums_Keepouts"

hardware_names = (
    "Camera_Module",
    "Front_Light_Left",
    "Front_Light_Right",
    "Radar_Holder",
    "Speaker_Left",
    "Speaker_Right",
)
obstacle_names = (
    "Cover_Glass",
    "PCAP_Sensor",
    "Optical_Bond",
    "LCD_Cell",
    "BLU_Optical_Films",
    "Light_Guide_Plate",
    "Panel_Backplate",
    "Metal_Mid_Frame",
    "Front_Bezel",
    "Rear_Enclosure",
) + tuple("Primary_Boss_{{:02d}}".format(index) for index in range(1, 5)) + tuple(
    "VESA_Boss_{{:02d}}".format(index) for index in range(1, 5)
)
for hardware_name in hardware_names:
    hardware = doc.getObject(hardware_name)
    assert hardware is not None and hardware.Shape.isValid(), hardware_name
    for obstacle_name in obstacle_names:
        obstacle = doc.getObject(obstacle_name)
        overlap = hardware.Shape.common(obstacle.Shape).Volume
        assert overlap <= 0.01, (hardware_name, obstacle_name, overlap)

for index, first_name in enumerate(hardware_names):
    for second_name in hardware_names[index + 1:]:
        overlap = doc.getObject(first_name).Shape.common(
            doc.getObject(second_name).Shape
        ).Volume
        assert overlap <= 0.01, (first_name, second_name, overlap)
App.closeDocument(doc.Name)
print("HINOKI_LOD3_AV_OVERLAP_PROBE_OK")
""".format(model_path=model_path.as_posix())
            probe_result = subprocess.run(
                [str(FREECAD_CMD), "-c"],
                cwd=Path(tempfile.gettempdir()),
                input="exec({!r})\n".format(probe),
                capture_output=True,
                text=True,
                check=False,
                timeout=180,
            )
            combined_probe = probe_result.stdout + probe_result.stderr
            self.assertEqual(0, probe_result.returncode, combined_probe)
            self.assertIn("HINOKI_LOD3_AV_OVERLAP_PROBE_OK", combined_probe)

    def test_ports_cut_through_rear_service_opening(self):
        p = load_module(PARAMETERS_FILE, "hinoki_lod3_parameters_ports")
        self.assertTrue(
            hasattr(p, "IO_PORT_GEOMETRY"),
            "missing controlled IO_PORT_GEOMETRY parameters",
        )
        with tempfile.TemporaryDirectory(prefix="hinoki_lod3_ports_") as temp_dir:
            model_path = Path(temp_dir) / "Hinoki_LOD3_Ports_Test.FCStd"
            env = os.environ.copy()
            env["HINOKI_LOD3_MODEL_OUT"] = str(model_path)
            result = run_freecad_script(BUILD_SCRIPT, env)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

            probe = r"""
import FreeCAD as App

doc = App.open(r"{model_path}")
rear = doc.getObject("Rear_Enclosure")
cover = doc.getObject("Rear_IO_Cover")
for port_name in {port_names!r}:
    port = doc.getObject(port_name)
    cutter = doc.getObject(port_name + "_Clearance_Hole")
    assert port.GeometryRole == "ConnectorBody"
    assert cutter.GeometryRole == "ClearanceHole"
    assert cutter.PhysicalCollision is False
    assert cutter.Shape.BoundBox.ZMin < {rear_z}
    assert cutter.Shape.BoundBox.ZMax > {head_depth}
    cover_box = cover.Shape.BoundBox
    centre = cutter.Shape.BoundBox.Center
    assert cover_box.XMin < centre.x < cover_box.XMax, (port_name, centre.x)
    assert cover_box.YMin < centre.y < cover_box.YMax, (port_name, centre.y)
    assert port.Shape.BoundBox.ZMax <= {head_depth} + 0.01
    assert port.Shape.common(rear.Shape).Volume <= 0.01, port_name
    assert port.Shape.common(cover.Shape).Volume <= 0.01, port_name
    assert cutter.Shape.common(rear.Shape).Volume <= 0.01, port_name
    assert cutter.Shape.common(cover.Shape).Volume <= 0.01, port_name
App.closeDocument(doc.Name)
print("HINOKI_LOD3_PORT_CUT_PROBE_OK")
""".format(
                model_path=model_path.as_posix(),
                port_names=tuple(p.IO_PORTS),
                rear_z=p.HEAD["depth"] - p.HOUSING["rear_wall"],
                head_depth=p.HEAD["depth"],
            )
            probe_result = subprocess.run(
                [str(FREECAD_CMD), "-c"],
                cwd=Path(tempfile.gettempdir()),
                input="exec({!r})\n".format(probe),
                capture_output=True,
                text=True,
                check=False,
                timeout=180,
            )
            combined_probe = probe_result.stdout + probe_result.stderr
            self.assertEqual(0, probe_result.returncode, combined_probe)
            self.assertIn("HINOKI_LOD3_PORT_CUT_PROBE_OK", combined_probe)

    def test_ports_preserve_vesa_and_tim_geometry(self):
        package_path = PACKAGE_ROOT.as_posix()
        with tempfile.TemporaryDirectory(prefix="hinoki_lod3_ports_preserve_") as temp_dir:
            probe = r"""
import sys
import FreeCAD as App

sys.path.insert(0, r"{package_path}")
from hinoki_lod3_av_io import build_av_io
from hinoki_lod3_common import make_groups
from hinoki_lod3_display_housing import build_display_housing
from hinoki_lod3_electronics_thermal import build_electronics_thermal
import hinoki_lod3_parameters as p

doc = App.newDocument("Hinoki_LOD3_Port_Preservation")
groups = make_groups(doc, p.REQUIRED_TOP_GROUPS)
build_display_housing(doc, groups)
build_electronics_thermal(doc, groups)
tim_before = doc.getObject("Rear_Hatch_TIM").Shape.copy()
build_av_io(doc, groups)
# Rear_Hatch_TIM is nowhere near the AV cluster or IO ports and must remain
# byte-identical geometry after build_av_io. Metal_Mid_Frame IS legitimately
# cut by the AV cavity (front-side keepout for camera/lighting/audio) so we
# only assert that ports do not intersect its remaining shape.
for name, before in (("Rear_Hatch_TIM", tim_before),):
    after = doc.getObject(name).Shape
    assert abs(after.Volume - before.Volume) <= 0.01, (name, before.Volume, after.Volume)
    assert before.cut(after).Volume <= 0.01, (name, "removed", before.cut(after).Volume)
    assert after.cut(before).Volume <= 0.01, (name, "added", after.cut(before).Volume)
for port_name in p.IO_PORTS:
    port = doc.getObject(port_name)
    assert abs(port.Shape.Volume - p.IO_PORT_GEOMETRY["body_width"] * p.IO_PORT_GEOMETRY["body_height"] * p.IO_PORT_GEOMETRY["body_depth"]) <= 0.01, port_name
    assert port.Shape.common(doc.getObject("Metal_Mid_Frame").Shape).Volume <= 0.01, port_name
    assert port.Shape.common(doc.getObject("Rear_Hatch_TIM").Shape).Volume <= 0.01, port_name
App.closeDocument(doc.Name)
assert not App.listDocuments()
print("HINOKI_LOD3_PORT_SUPPORT_GEOMETRY_PROBE_OK")
""".format(package_path=package_path)
            probe_result = subprocess.run(
                [str(FREECAD_CMD), "-c"],
                cwd=Path(tempfile.gettempdir()),
                input="exec({!r})\n".format(probe),
                capture_output=True,
                text=True,
                check=False,
                timeout=180,
            )
            combined_probe = probe_result.stdout + probe_result.stderr
            self.assertEqual(0, probe_result.returncode, combined_probe)
            self.assertIn("HINOKI_LOD3_PORT_SUPPORT_GEOMETRY_PROBE_OK", combined_probe)

    def test_av_io_dimensions_use_owned_controlled_assumptions(self):
        p = load_module(PARAMETERS_FILE, "hinoki_lod3_parameters_av_owned")
        required_blocks = (
            "SHUTTER_GEOMETRY",
            "ALS_GEOMETRY",
            "MICROPHONE_GEOMETRY",
            "SPEAKER_GEOMETRY",
            "IO_PORT_GEOMETRY",
        )
        for block_name in required_blocks:
            self.assertTrue(
                hasattr(p, block_name),
                "missing controlled " + block_name,
            )
            block = getattr(p, block_name)
            self.assertTrue(block["assumption_id"], block_name)
            self.assertTrue(block["source_reference"], block_name)
        source = AV_IO_FILE.read_text(encoding="utf-8")
        self.assertNotIn(
            'p.BOARD_ENVELOPES["IO_PCB"]["thickness"]',
            source,
        )
        self.assertNotIn(
            'p.CAMERA_LIGHT_SENSOR["Front_Light_Left"]["depth"]',
            source,
        )

    def test_task5_microphone_geometry_uses_distinct_radius_and_depth(self):
        source = AV_IO_FILE.read_text(encoding="utf-8")
        self.assertIn(
            "Part.makeCylinder(\n                microphone_radius,\n                microphone_geometry[\"depth\"],",
            source,
        )
        with tempfile.TemporaryDirectory(prefix="hinoki_lod3_microphone_geometry_") as temp_dir:
            model_path = Path(temp_dir) / "Hinoki_LOD3_Microphone_Geometry_Test.FCStd"
            env = os.environ.copy()
            env["HINOKI_LOD3_MODEL_OUT"] = str(model_path)
            result = run_freecad_script(BUILD_SCRIPT, env)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            probe = r"""
import FreeCAD as App

doc = App.open(r"{model_path}")
for name in ("Microphone_Left", "Microphone_Right"):
    obj = doc.getObject(name)
    assert abs(obj.Diameter.Value - 3.2) <= 0.01, (name, obj.Diameter.Value)
    assert abs(obj.Depth.Value - 1.6) <= 0.01, (name, obj.Depth.Value)
    assert abs(obj.Shape.BoundBox.XLength - obj.Diameter.Value) <= 0.01, name
    assert abs(obj.Shape.BoundBox.YLength - obj.Diameter.Value) <= 0.01, name
    assert abs(obj.Shape.BoundBox.ZLength - obj.Depth.Value) <= 0.01, name
App.closeDocument(doc.Name)
print("HINOKI_LOD3_MICROPHONE_GEOMETRY_PROBE_OK")
""".format(model_path=model_path.as_posix())
            probe_result = subprocess.run(
                [str(FREECAD_CMD), "-c"],
                cwd=Path(tempfile.gettempdir()),
                input="exec({!r})\n".format(probe),
                capture_output=True,
                text=True,
                check=False,
                timeout=180,
            )
            combined_probe = probe_result.stdout + probe_result.stderr
            self.assertEqual(0, probe_result.returncode, combined_probe)
            self.assertIn("HINOKI_LOD3_MICROPHONE_GEOMETRY_PROBE_OK", combined_probe)

    def test_task5_physical_parts_have_no_unauthorized_intersections(self):
        with tempfile.TemporaryDirectory(prefix="hinoki_lod3_task5_collision_") as temp_dir:
            model_path = Path(temp_dir) / "Hinoki_LOD3_Task5_Collision_Test.FCStd"
            env = os.environ.copy()
            env["HINOKI_LOD3_MODEL_OUT"] = str(model_path)
            result = run_freecad_script(BUILD_SCRIPT, env)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            probe = r"""
import FreeCAD as App

doc = App.open(r"{model_path}")
task_assemblies = ("04_Camera_Lighting_Sensors", "05_Audio_IO_Cables")
obstacle_assemblies = (
    "01_Display_Stack",
    "02_Housing_Structure",
    "03_Electronics_Thermal",
    "07_Fasteners_Seals_Consumables",
)
reference_roles = (
    "PackageEnvelope",
    "MotionStateReference",
    "MotionKeepout",
    "InternalOpticalKeepout",
    "ExternalOpticalReference",
    "CavityReference",
    "OpticalKeepout",
    "AcousticKeepout",
    "ClearanceHole",
)
physical = lambda obj: (
    getattr(obj, "IsSemanticPart", False)
    and getattr(obj, "ParentAssembly", "") != "08_Reference_Datums_Keepouts"
    and getattr(obj, "GeometryRole", "") not in reference_roles
    and getattr(obj, "Shape", None) is not None
    and not obj.Shape.isNull()
)
task_parts = [obj for obj in doc.Objects if physical(obj) and obj.ParentAssembly in task_assemblies]
obstacles = [obj for obj in doc.Objects if physical(obj) and obj.ParentAssembly in obstacle_assemblies]
def exact_contact(first, second):
    return (
        second.Name in tuple(getattr(first, "AuthorizedContactTargets", ()))
        and first.Name in tuple(getattr(second, "AuthorizedContactTargets", ()))
    )

authorized_collisions = []
max_unauthorized_intersection = 0.0
max_unauthorized_pair = None
for task in task_parts:
    for obstacle in obstacles:
        overlap = task.Shape.common(obstacle.Shape).Volume
        pair = (task.Name, obstacle.Name)
        if exact_contact(task, obstacle):
            assert overlap > 0.01, (pair, overlap)
            authorized_collisions.append((pair, overlap))
        else:
            if overlap > max_unauthorized_intersection:
                max_unauthorized_intersection = overlap
                max_unauthorized_pair = pair
for index, first in enumerate(task_parts):
    for second in task_parts[index + 1:]:
        overlap = first.Shape.common(second.Shape).Volume
        pair = (first.Name, second.Name)
        if exact_contact(first, second):
            assert overlap > 0.01, (pair, overlap)
            authorized_collisions.append((pair, overlap))
        else:
            if overlap > max_unauthorized_intersection:
                max_unauthorized_intersection = overlap
                max_unauthorized_pair = pair
assert max_unauthorized_intersection <= 0.01, (
    max_unauthorized_pair,
    max_unauthorized_intersection,
)
assert set(authorized_collisions) == {{
    (("Camera_Module", "Heat_Camera"), 526.6800000000001),
    (("Front_Light_Left", "Heat_Front_Lighting"), 7680.0),
    (("Front_Light_Right", "Heat_Front_Lighting"), 7680.0),
}}, authorized_collisions
App.closeDocument(doc.Name)
print("HINOKI_LOD3_TASK5_COLLISION_PROBE_OK authorized={{}} max_unauthorized={{:.6f}}".format(
    len(authorized_collisions), max_unauthorized_intersection
))
""".format(model_path=model_path.as_posix())
            probe_result = subprocess.run(
                [str(FREECAD_CMD), "-c"],
                cwd=Path(tempfile.gettempdir()),
                input="exec({!r})\n".format(probe),
                capture_output=True,
                text=True,
                check=False,
                timeout=180,
            )
            combined_probe = probe_result.stdout + probe_result.stderr
            self.assertEqual(0, probe_result.returncode, combined_probe)
            self.assertIn("HINOKI_LOD3_TASK5_COLLISION_PROBE_OK", combined_probe)

    def test_shutter_symmetry_shape_and_traceability_contract(self):
        with tempfile.TemporaryDirectory(prefix="hinoki_lod3_av_contract_") as temp_dir:
            model_path = Path(temp_dir) / "Hinoki_LOD3_AV_Contract_Test.FCStd"
            env = os.environ.copy()
            env["HINOKI_LOD3_MODEL_OUT"] = str(model_path)
            result = run_freecad_script(BUILD_SCRIPT, env)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

            probe = r"""
import FreeCAD as App

doc = App.open(r"{model_path}")
closed = doc.getObject("Privacy_Shutter")
opened = doc.getObject("Privacy_Shutter_Open")
optics = doc.getObject("Camera_Optical_Keepout")
assert opened is not None, "missing explicit Privacy_Shutter_Open state"
assert closed.Shape.common(optics.Shape).Volume > 0.01
assert opened.Shape.common(optics.Shape).Volume <= 0.01
assert abs(
    opened.Shape.BoundBox.XMin
    - closed.Shape.BoundBox.XMin
    - closed.Travel.Value
) <= 0.01

for left_name, right_name in (
    ("Front_Light_Left", "Front_Light_Right"),
    ("Speaker_Left", "Speaker_Right"),
    ("Passive_Radiator_Left", "Passive_Radiator_Right"),
    ("Microphone_Left", "Microphone_Right"),
    ("Speaker_Left_Acoustic_Keepout", "Speaker_Right_Acoustic_Keepout"),
):
    left = doc.getObject(left_name)
    right = doc.getObject(right_name)
    assert left.Shape.isValid() and left.Shape.Volume > 0.0, left_name
    assert right.Shape.isValid() and right.Shape.Volume > 0.0, right_name
    assert abs(
        left.Shape.BoundBox.Center.x
        + right.Shape.BoundBox.Center.x
        - 742.0
    ) <= 0.01, (left_name, right_name)
    assert abs(
        left.Shape.BoundBox.Center.y - right.Shape.BoundBox.Center.y
    ) <= 0.01
    assert abs(
        left.Shape.BoundBox.Center.z - right.Shape.BoundBox.Center.z
    ) <= 0.01

reference_names = (
    "Camera_Barrel",
    "Camera_Optical_Keepout",
    "Camera_FOV_Reference",
    "ALS_Optical_Path",
    "Shutter_Travel_Envelope",
    "AV_Cavity",
    "Speaker_Left_Acoustic_Keepout",
    "Speaker_Right_Acoustic_Keepout",
)
for name in reference_names:
    obj = doc.getObject(name)
    assert obj is not None and obj.Shape.isValid(), name
    assert obj.Shape.Volume > 0.0, name
    assert obj.PhysicalCollision is False, name

task_parts = [
    obj for obj in doc.Objects
    if getattr(obj, "IsSemanticPart", False)
    and (
        obj.ParentAssembly in (
            "04_Camera_Lighting_Sensors",
            "05_Audio_IO_Cables",
        )
        or hasattr(obj, "GeometryRole")
    )
]
source_references = {{obj.SourceReference for obj in task_parts}}
assert len(source_references) >= 8, source_references
assert all(
    "A-LOD3" in obj.SourceReference
    or "Design section" in obj.SourceReference
    or "LI-IMX477" in obj.SourceReference
    for obj in task_parts
), [(obj.Name, obj.SourceReference) for obj in task_parts]
App.closeDocument(doc.Name)
print("HINOKI_LOD3_AV_CONTRACT_PROBE_OK refs={{}}".format(
    len(source_references)
))
""".format(model_path=model_path.as_posix())
            probe_result = subprocess.run(
                [str(FREECAD_CMD), "-c"],
                cwd=Path(tempfile.gettempdir()),
                input="exec({!r})\n".format(probe),
                capture_output=True,
                text=True,
                check=False,
                timeout=180,
            )
            combined_probe = probe_result.stdout + probe_result.stderr
            self.assertEqual(0, probe_result.returncode, combined_probe)
            self.assertIn("HINOKI_LOD3_AV_CONTRACT_PROBE_OK", combined_probe)

    def test_builder_adds_camera_lighting_sensors_audio_io(self):
        with tempfile.TemporaryDirectory(prefix="hinoki_lod3_av_io_") as temp_dir:
            model_path = Path(temp_dir) / "Hinoki_LOD3_AV_IO_Test.FCStd"
            env = os.environ.copy()
            env["HINOKI_LOD3_MODEL_OUT"] = str(model_path)
            result = run_freecad_script(BUILD_SCRIPT, env)
            combined_output = result.stdout + result.stderr
            self.assertEqual(0, result.returncode, combined_output)
            self.assertIn("HINOKI_LOD3_BUILD_OK", combined_output)

            probe = r"""
import FreeCAD as App

doc = App.open(r"{model_path}")
expected_boxes = {{
    "Camera_Module": (38.0, 38.0, 25.78),
    "Camera_Barrel": (104.0, 46.0, 32.0),
    "Front_Light_Left": (120.0, 8.0, 8.0),
    "Front_Light_Right": (120.0, 8.0, 8.0),
    "Radar_Holder": (59.8, 18.0, 16.3),
}}
for name, expected in expected_boxes.items():
    obj = doc.getObject(name)
    assert obj is not None, "missing named AV/I/O part: " + name
    assert obj.Shape.isValid() and obj.Shape.Volume > 0.0, name
    actual = (
        obj.Shape.BoundBox.XLength,
        obj.Shape.BoundBox.YLength,
        obj.Shape.BoundBox.ZLength,
    )
    assert all(abs(a - b) <= 0.01 for a, b in zip(actual, expected)), (name, actual)

shutter = doc.getObject("Privacy_Shutter")
assert shutter is not None, "missing named AV/I/O part: Privacy_Shutter"
assert shutter.Shape.isValid() and shutter.Shape.Volume > 0.0
assert shutter.Captive is True and shutter.Travel.Value > 0.0
assert doc.getObject("Shutter_Travel_Envelope") is not None

als = doc.getObject("ALS_Optical_Path")
assert als is not None, "missing named AV/I/O part: ALS_Optical_Path"
assert als.GeometryRole == "OpticalKeepout"
assert doc.getObject("Camera_Optical_Keepout") is not None

for name in ("Speaker_Left", "Speaker_Right"):
    obj = doc.getObject(name)
    assert obj is not None, "missing named AV/I/O part: " + name
    assert abs(obj.Diameter.Value - 40.0) <= 0.01
    assert obj.Shape.isValid() and obj.Shape.Volume > 0.0
for name in ("Passive_Radiator_Left", "Passive_Radiator_Right"):
    obj = doc.getObject(name)
    assert obj is not None, "missing named AV/I/O part: " + name
    assert abs(obj.Width.Value - 50.0) <= 0.01
    assert abs(obj.Height.Value - 25.0) <= 0.01
for name in ("Microphone_Left", "Microphone_Right"):
    obj = doc.getObject(name)
    assert obj is not None, "missing named AV/I/O part: " + name
    assert obj.ElementCount == 1
for name in ("Speaker_Left_Acoustic_Keepout", "Speaker_Right_Acoustic_Keepout"):
    obj = doc.getObject(name)
    assert obj is not None and obj.GeometryRole == "AcousticKeepout", name

route_objects = [
    obj for obj in doc.Objects
    if getattr(obj, "GeometryRole", "") in (
        "RoutedCable",
        "CableObstructionEnvelope",
    )
    or "Cable_Route" in obj.Name
    or obj.Name.endswith("_Obstruction_Envelope")
]
assert not route_objects, [obj.Name for obj in route_objects]

port_names = {port_names!r}
for port_name in port_names:
    port = doc.getObject(port_name)
    hole = doc.getObject(port_name + "_Clearance_Hole")
    assert port is not None, "missing named AV/I/O part: " + port_name
    assert port.PortType == port_name and port.GeometryRole == "ConnectorBody"
    assert hole is not None and hole.GeometryRole == "ClearanceHole"
    assert port.Shape.isValid() and port.Shape.Volume > 0.0
    assert hole.Shape.isValid() and hole.Shape.Volume > 0.0

for obj in doc.Objects:
    if getattr(obj, "IsSemanticPart", False):
        assert obj.ManufacturingAuthority is False, obj.Name
        assert obj.SourceReference, obj.Name
        if obj.ParentAssembly in (
            "04_Camera_Lighting_Sensors",
            "05_Audio_IO_Cables",
        ) or getattr(obj, "GeometryRole", "") == "PackageEnvelope":
            box = obj.Shape.BoundBox
            assert box.XMin >= -0.01 and box.XMax <= 742.01, obj.Name
            assert box.YMin >= -0.01 and box.YMax <= 492.01, obj.Name
            assert box.ZMin >= -0.01 and box.ZMax <= 62.01, obj.Name

App.closeDocument(doc.Name)
assert not App.listDocuments()
print("HINOKI_LOD3_AV_IO_PROBE_OK ports={{}}".format(len(port_names)))
""".format(
                model_path=model_path.as_posix(),
                port_names=(
                    "HDMI_Input",
                    "USB_A_1",
                    "USB_A_2",
                    "USB_C_Display_Data_PD90W",
                    "Ethernet",
                    "Line_Out_3p5mm",
                ),
            )
            probe_result = subprocess.run(
                [str(FREECAD_CMD), "-c"],
                cwd=Path(tempfile.gettempdir()),
                input="exec({!r})\n".format(probe),
                capture_output=True,
                text=True,
                check=False,
                timeout=180,
            )
            combined_probe = probe_result.stdout + probe_result.stderr
            self.assertEqual(0, probe_result.returncode, combined_probe)
            self.assertIn("HINOKI_LOD3_AV_IO_PROBE_OK", combined_probe)


class TestMasterValidation(unittest.TestCase):
    def _build_temporary_master(self, temp_root):
        model_path = temp_root / "Hinoki_LOD3_Master_Validation.FCStd"
        env = os.environ.copy()
        env["HINOKI_LOD3_MODEL_OUT"] = str(model_path)
        result = run_freecad_script(BUILD_SCRIPT, env)
        combined_output = result.stdout + result.stderr
        self.assertEqual(0, result.returncode, combined_output)
        self.assertIn("HINOKI_LOD3_BUILD_OK", combined_output)
        self.assertTrue(model_path.exists(), combined_output)
        return model_path

    def test_head_only_review_reports_all_active_hard_gates(self):
        self.assertTrue(REVIEW_SCRIPT.exists(), "LOD 3 review script must exist")
        parameters = load_module(PARAMETERS_FILE, "hinoki_lod3_validation_parameters")
        with tempfile.TemporaryDirectory(prefix="hinoki_lod3_review_") as temp_dir:
            temp_root = Path(temp_dir)
            model_path = self._build_temporary_master(temp_root)
            review_path = temp_root / "Hinoki_LOD3_Validation.json"
            env = os.environ.copy()
            env["HINOKI_LOD3_MODEL_PATH"] = str(model_path)
            env["HINOKI_LOD3_REVIEW_OUT"] = str(review_path)

            result = run_freecad_script(REVIEW_SCRIPT, env)
            combined_output = result.stdout + result.stderr

            self.assertEqual(0, result.returncode, combined_output)
            self.assertEqual(1, combined_output.count("HINOKI_LOD3_REVIEW_OK"))
            self.assertNotIn("HINOKI_LOD3_REVIEW_FAIL", combined_output)
            self.assertTrue(review_path.exists())
            report = json.loads(review_path.read_text(encoding="utf-8"))

            overlap_probe = r"""
import json
import FreeCAD as App

doc = App.open(r"{model_path}")
physical = [
    obj for obj in doc.Objects
    if getattr(obj, "IsSemanticPart", False)
    and getattr(obj, "ParentAssembly", "") != "08_Reference_Datums_Keepouts"
    and getattr(obj, "PhysicalCollision", True)
    and getattr(obj, "Shape", None) is not None
    and not obj.Shape.isNull()
]
authorized = {{
    tuple(sorted(pair)) for pair in (
        ("Camera_Module", "Heat_Camera"),
        ("Front_Light_Left", "Heat_Front_Lighting"),
        ("Front_Light_Right", "Heat_Front_Lighting"),
        ("Metal_Mid_Frame", "Primary_Boss_01"),
        ("Metal_Mid_Frame", "Primary_Boss_02"),
        ("Metal_Mid_Frame", "Primary_Boss_03"),
        ("Metal_Mid_Frame", "Primary_Boss_04"),
        ("Metal_Mid_Frame", "VESA_Boss_01"),
        ("Metal_Mid_Frame", "VESA_Boss_02"),
        ("Metal_Mid_Frame", "VESA_Boss_03"),
        ("Metal_Mid_Frame", "VESA_Boss_04"),
        ("Heat_QC7790", "TIM_QC7790"),
        ("Copper_Spreader", "TIM_QC7790"),
        ("Copper_Spreader", "Heat_Pipe_Left"),
        ("Copper_Spreader", "Heat_Pipe_Right"),
        ("Aluminum_Interface", "Heat_Pipe_Left"),
        ("Aluminum_Interface", "Heat_Pipe_Right"),
        ("Aluminum_Interface", "Rear_Hatch_TIM"),
        ("Rear_Hatch_TIM", "Rear_IO_Cover"),
    )
}}
forbidden = []
for index, left in enumerate(physical):
    for right in physical[index + 1:]:
        pair = tuple(sorted((left.Name, right.Name)))
        if pair in authorized:
            continue
        overlap = float(left.Shape.common(right.Shape).Volume)
        if overlap > 0.01:
            forbidden.append({{
                "parts": [left.Name, right.Name],
                "overlap_mm3": overlap,
            }})
App.closeDocument(doc.Name)
print("HINOKI_LOD3_ALL_PHYSICAL_OVERLAPS " + json.dumps({{
    "physical_count": len(physical),
    "forbidden": forbidden,
}}, sort_keys=True))
raise SystemExit(1 if forbidden else 0)
""".format(model_path=model_path.as_posix())
            overlap_result = subprocess.run(
                [str(FREECAD_CMD), "-c"],
                cwd=Path(tempfile.gettempdir()),
                input="exec({!r})\n".format(overlap_probe),
                capture_output=True,
                text=True,
                check=False,
                timeout=180,
            )
            overlap_output = overlap_result.stdout + overlap_result.stderr
            self.assertEqual(0, overlap_result.returncode, overlap_output)
            self.assertIn(
                '"physical_count": 78',
                overlap_output,
            )
            self.assertIn('"forbidden": []', overlap_output)

        self.assertEqual("Pass", report["status"])
        self.assertEqual("Pass", report.get("overall"))
        self.assertEqual("HeadOnlyTask8QualityRemediation", report["scope"])
        self.assertEqual(parameters.PROTOTYPE_LIMITATION, report["limitations"])
        self.assertEqual(0.01, report["overlap_threshold_mm3"])
        self.assertEqual(
            {
                "semantic_part_count",
                "physical_part_count",
                "eight_group_ownership",
                "valid_positive_physical_geometry",
                "complete_metadata",
                "exact_authorized_contact_matrix",
                "no_forbidden_overlaps",
                "required_feature_evidence",
                "head_envelope",
                "enclosure_mating_continuous",
                "rib_host_attachment",
                "fastener_engagement",
                "unique_heat_source_mapping_and_budget",
                "panel_module_budget_conserved",
            },
            set(report["hard_gates"]),
        )
        self.assertTrue(all(report["hard_gates"].values()))
        self.assertEqual(
            ["stand_envelope", "stand_motion", "stand_interference"],
            report["deferred_gates"],
        )
        serialized = json.dumps(report, sort_keys=True).lower()
        self.assertNotIn("vesa_motion", serialized)
        self.assertNotIn("extreme_posture", serialized)

        part_count = report["semantic_parts"]["count"]
        self.assertEqual(parameters.EXPECTED_SEMANTIC_PART_COUNT, part_count)
        self.assertTrue(report["semantic_parts"]["names_unique"])
        self.assertEqual(
            list(parameters.REQUIRED_TOP_GROUPS),
            report["group_ownership"]["required_groups"],
        )
        self.assertEqual([], report["group_ownership"]["failures"])
        physical_count = parameters.EXPECTED_PHYSICAL_PART_COUNT
        self.assertEqual(physical_count, report["physical_geometry"]["part_count"])
        self.assertEqual([], report["physical_geometry"]["failures"])
        self.assertTrue(report["enclosure_mating"]["z_coverage_continuous"])
        self.assertLessEqual(report["enclosure_mating"]["remedied_gap_mm"], 0.1)
        self.assertTrue(report["rib_host"]["ok"])
        self.assertGreaterEqual(report["rib_host"]["rib_feature_count"], 4)
        self.assertTrue(report["fastener_engagement"]["ok"])
        self.assertTrue(report["heat_sources"]["ok"])
        self.assertAlmostEqual(57.0, report["heat_sources"]["total_w"], places=6)
        self.assertTrue(report["budget_groups"]["panel_module_ok"])

        self.assertEqual(
            list(parameters.METADATA_KEYS), report["metadata"]["required_keys"]
        )
        self.assertEqual([], report["metadata"]["incomplete_parts"])
        self.assertEqual(
            [], report["metadata"]["manufacturing_authority_failures"]
        )
        self.assertGreater(
            report["metadata"]["source_class_counts"]["EngineeringAssumption"],
            0,
        )
        self.assertTrue(
            all(
                record["ManufacturingAuthority"] is False
                for record in report["metadata"]["parts"]
            )
        )
        metadata_by_name = {
            record["PartName"]: record for record in report["metadata"]["parts"]
        }
        self.assertEqual(
            "EngineeringAssumption",
            metadata_by_name["Privacy_Shutter"]["SourceClass"],
        )
        self.assertEqual(
            "CompetitorOfficial",
            metadata_by_name["Camera_Module"]["SourceClass"],
        )
        self.assertEqual(
            "Derived", metadata_by_name["Cover_Glass"]["SourceClass"]
        )

        actual_contact_pairs = {
            tuple(sorted(contact["parts"]))
            for contact in report["authorized_contacts"]
        }
        # Task 8 quality remediation expands the authorised-contact matrix
        # from 3 AV/lighting bonds to 19 pairs, adding 8 structural
        # boss->mid-frame root engagements and 8 thermal-path contacts
        # from the QC7790 die to the rear I/O cover.
        expected_contact_pairs = {
            ("Camera_Module", "Heat_Camera"),
            ("Front_Light_Left", "Heat_Front_Lighting"),
            ("Front_Light_Right", "Heat_Front_Lighting"),
            ("Metal_Mid_Frame", "Primary_Boss_01"),
            ("Metal_Mid_Frame", "Primary_Boss_02"),
            ("Metal_Mid_Frame", "Primary_Boss_03"),
            ("Metal_Mid_Frame", "Primary_Boss_04"),
            ("Metal_Mid_Frame", "VESA_Boss_01"),
            ("Metal_Mid_Frame", "VESA_Boss_02"),
            ("Metal_Mid_Frame", "VESA_Boss_03"),
            ("Metal_Mid_Frame", "VESA_Boss_04"),
            ("Heat_QC7790", "TIM_QC7790"),
            ("Copper_Spreader", "TIM_QC7790"),
            ("Copper_Spreader", "Heat_Pipe_Left"),
            ("Copper_Spreader", "Heat_Pipe_Right"),
            ("Aluminum_Interface", "Heat_Pipe_Left"),
            ("Aluminum_Interface", "Heat_Pipe_Right"),
            ("Aluminum_Interface", "Rear_Hatch_TIM"),
            ("Rear_Hatch_TIM", "Rear_IO_Cover"),
        }
        self.assertEqual(
            {tuple(sorted(pair)) for pair in expected_contact_pairs},
            actual_contact_pairs,
        )
        self.assertTrue(
            all(
                contact["overlap_mm3"] > report["overlap_threshold_mm3"]
                for contact in report["authorized_contacts"]
            )
        )
        self.assertEqual([], report["forbidden_overlaps"])
        authorized_pair_count = len(expected_contact_pairs)
        self.assertEqual(
            physical_count * (physical_count - 1) // 2 - authorized_pair_count,
            report["authorized_contact_matrix"].get("checked_forbidden_pair_count"),
        )

        self.assertEqual(
            {
                "wall",
                "rib",
                "boss",
                "bend",
                "hole",
                "hatch",
                "fastener",
                "vent",
                "thermal_contact",
            },
            set(report["feature_evidence"]),
        )
        self.assertTrue(
            all(
                report["feature_evidence"][feature]
                for feature in report["feature_evidence"]
            )
        )
        self.assertEqual(
            [742.0, 492.0, 62.0], report["head_envelope"]["expected_mm"]
        )
        self.assertEqual(0.1, report["head_envelope"]["tolerance_mm"])
        self.assertTrue(report["head_envelope"]["within_tolerance"])

    def test_review_rejects_injected_rib_collision_and_does_not_publish(self):
        with tempfile.TemporaryDirectory(prefix="hinoki_lod3_rib_collision_") as temp_dir:
            temp_root = Path(temp_dir)
            model_path = self._build_temporary_master(temp_root)
            injected_path = temp_root / "injected_rib_collision.FCStd"
            source = REVIEW_SCRIPT.read_text(encoding="utf-8")
            probe = """
import json
import FreeCAD as App

namespace = {{"__name__": "hinoki_lod3_collision_probe", "__file__": r"{script_path}"}}
exec(compile({source!r}, r"{script_path}", "exec"), namespace)
doc = App.open(r"{model_path}")
try:
    doc.getObject("SOM_Shield_Can").Shape = doc.getObject("Power_Shield_Can").Shape.copy()
    doc.recompute()
    doc.saveAs(r"{injected_path}")
    report = namespace["validate_master"](doc)
finally:
    App.closeDocument(doc.Name)
print("HINOKI_LOD3_INJECTED_REPORT " + json.dumps({{
    "status": report["status"],
    "overall": report["overall"],
    "no_forbidden_overlaps": report["hard_gates"]["no_forbidden_overlaps"],
    "forbidden_overlaps": report["forbidden_overlaps"],
}}, sort_keys=True))
""".format(
                script_path=REVIEW_SCRIPT.as_posix(),
                source=source,
                model_path=model_path.as_posix(),
                injected_path=injected_path.as_posix(),
            )
            probe_result = subprocess.run(
                [str(FREECAD_CMD), "-c"],
                cwd=Path(tempfile.gettempdir()),
                input="exec({!r})\n".format(probe),
                capture_output=True,
                text=True,
                check=False,
                timeout=180,
            )
            probe_output = probe_result.stdout + probe_result.stderr
            self.assertEqual(0, probe_result.returncode, probe_output)
            self.assertTrue(injected_path.exists(), probe_output)
            sentinel = "HINOKI_LOD3_INJECTED_REPORT "
            payloads = [
                line.split(sentinel, 1)[1]
                for line in probe_output.splitlines()
                if sentinel in line
            ]
            self.assertEqual(1, len(payloads), probe_output)
            report = json.loads(payloads[0])
            self.assertEqual("Fail", report["status"])
            self.assertEqual("Fail", report["overall"])
            self.assertFalse(report["no_forbidden_overlaps"])
            overlaps = {
                tuple(sorted(entry["parts"])): entry["overlap_mm3"]
                for entry in report["forbidden_overlaps"]
            }
            collision_pair = ("Power_Shield_Can", "SOM_Shield_Can")
            self.assertIn(collision_pair, overlaps)
            self.assertGreater(overlaps[collision_pair], 0.01)

            review_path = temp_root / "must_not_publish.json"
            env = os.environ.copy()
            env["HINOKI_LOD3_MODEL_PATH"] = str(injected_path)
            env["HINOKI_LOD3_REVIEW_OUT"] = str(review_path)
            result = run_freecad_script(REVIEW_SCRIPT, env)
            combined_output = result.stdout + result.stderr
            self.assertNotEqual(0, result.returncode, combined_output)
            self.assertEqual(1, combined_output.count("HINOKI_LOD3_REVIEW_FAIL"))
            self.assertNotIn("HINOKI_LOD3_REVIEW_OK", combined_output)
            self.assertFalse(review_path.exists())

    def test_build_rejects_failed_integrated_part_count_and_contact_gates(self):
        with tempfile.TemporaryDirectory(prefix="hinoki_lod3_build_gate_") as temp_dir:
            model_path = Path(temp_dir) / "must_not_publish.FCStd"
            source = BUILD_SCRIPT.read_text(encoding="utf-8")
            probe = """
namespace = {{"__name__": "hinoki_lod3_build_gate_probe", "__file__": r"{script_path}"}}
exec(compile({source!r}, r"{script_path}", "exec"), namespace)
assert "validate_master" in namespace, "build must integrate validate_master"
namespace["validate_master"] = lambda doc: {{
    "status": "Fail",
    "hard_gates": {{
        "semantic_part_count": False,
        "exact_authorized_contact_matrix": False,
    }},
}}
namespace["save_atomically"] = lambda doc, destination: (_ for _ in ()).throw(
    AssertionError("validation was bypassed")
)
result_code = namespace["main"]()
assert result_code == 1, result_code
print("HINOKI_LOD3_BUILD_VALIDATION_GATE_PROBE_OK")
""".format(script_path=BUILD_SCRIPT.as_posix(), source=source)
            env = os.environ.copy()
            env["HINOKI_LOD3_MODEL_OUT"] = str(model_path)
            result = subprocess.run(
                [str(FREECAD_CMD), "-c"],
                cwd=Path(tempfile.gettempdir()),
                env=env,
                input="exec({!r})\n".format(probe),
                capture_output=True,
                text=True,
                check=False,
                timeout=180,
            )
            combined_output = result.stdout + result.stderr
            self.assertEqual(0, result.returncode, combined_output)
            self.assertIn(
                "HINOKI_LOD3_BUILD_VALIDATION_GATE_PROBE_OK",
                combined_output,
            )
            self.assertEqual(1, combined_output.count("HINOKI_LOD3_BUILD_FAILED"))
            self.assertNotIn("HINOKI_LOD3_BUILD_OK", combined_output)
            self.assertFalse(model_path.exists())

    def test_review_failure_sentinel_is_unique_and_does_not_publish(self):
        self.assertTrue(REVIEW_SCRIPT.exists(), "LOD 3 review script must exist")
        with tempfile.TemporaryDirectory(prefix="hinoki_lod3_review_fail_") as temp_dir:
            temp_root = Path(temp_dir)
            review_path = temp_root / "review.json"
            env = os.environ.copy()
            env["HINOKI_LOD3_MODEL_PATH"] = str(temp_root / "missing.FCStd")
            env["HINOKI_LOD3_REVIEW_OUT"] = str(review_path)
            result = run_freecad_script(REVIEW_SCRIPT, env)
            combined_output = result.stdout + result.stderr

            self.assertNotEqual(0, result.returncode, combined_output)
            self.assertEqual(1, combined_output.count("HINOKI_LOD3_REVIEW_FAIL"))
            self.assertNotIn("HINOKI_LOD3_REVIEW_OK", combined_output)
            self.assertFalse(review_path.exists())

    def test_blocked_staging_directory_preserves_failure_signal_and_existing_files(self):
        for existing_destination in (False, True):
            with self.subTest(existing_destination=existing_destination):
                with tempfile.TemporaryDirectory(prefix="hinoki_lod3_staging_fail_") as temp_dir:
                    model_path = Path(temp_dir) / "model.FCStd"
                    original_contents = b"existing destination must remain unchanged"
                    if existing_destination:
                        model_path.write_bytes(original_contents)
                    staging_directory = Path(temp_dir) / "model.FCStd.tmp.FCStd"
                    staging_directory.mkdir()
                    marker = staging_directory / "keep.txt"
                    marker.write_text("do not remove", encoding="utf-8")
                    env = os.environ.copy()
                    env["HINOKI_LOD3_MODEL_OUT"] = str(model_path)

                    result = run_freecad_script(BUILD_SCRIPT, env)
                    combined_output = result.stdout + result.stderr

                    self.assertNotEqual(0, result.returncode, combined_output)
                    self.assertEqual(
                        1, combined_output.count("HINOKI_LOD3_BUILD_FAILED")
                    )
                    self.assertNotIn("HINOKI_LOD3_BUILD_OK", combined_output)
                    self.assertNotIn("Traceback", combined_output)
                    if existing_destination:
                        self.assertEqual(original_contents, model_path.read_bytes())
                    else:
                        self.assertFalse(model_path.exists())
                    self.assertTrue(staging_directory.is_dir())
                    self.assertEqual(
                        "do not remove", marker.read_text(encoding="utf-8")
                    )
                    self.assertEqual(
                        ["keep.txt"],
                        sorted(p.name for p in staging_directory.iterdir()),
                    )

    def test_standalone_build_failure_has_nonzero_unique_sentinel(self):
        with tempfile.TemporaryDirectory(prefix="hinoki_lod3_build_fail_") as temp_dir:
            destination_directory = Path(temp_dir) / "destination_is_a_directory"
            destination_directory.mkdir()
            env = os.environ.copy()
            env["HINOKI_LOD3_MODEL_OUT"] = str(destination_directory)

            result = run_freecad_script(BUILD_SCRIPT, env)
            combined_output = result.stdout + result.stderr

            self.assertNotEqual(0, result.returncode, combined_output)
            self.assertEqual(1, combined_output.count("HINOKI_LOD3_BUILD_FAILED"))
            self.assertNotIn("HINOKI_LOD3_BUILD_OK", combined_output)
            self.assertNotIn("Traceback", combined_output)
            self.assertEqual([], list(Path(temp_dir).glob("*.tmp.FCStd")))



class TestAtomicExport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.export_script = PACKAGE_ROOT / "export_hinoki_lod3.py"
        if not cls.export_script.exists():
            return
        cls.workspace = tempfile.TemporaryDirectory(prefix="hinoki_lod3_export_")
        cls.addClassCleanup(cls.workspace.cleanup)
        cls.root = Path(cls.workspace.name)
        cls.model_path = cls.root / "source.FCStd"
        env = os.environ.copy()
        env["HINOKI_LOD3_MODEL_OUT"] = str(cls.model_path)
        result = run_freecad_script(BUILD_SCRIPT, env)
        if result.returncode or "HINOKI_LOD3_BUILD_OK" not in result.stdout:
            raise AssertionError(result.stdout + result.stderr)

    def _probe(self, body):
        self.assertTrue(self.export_script.exists(), "Task 8 exporter must exist")
        import textwrap
        with tempfile.TemporaryDirectory(dir=self.root, prefix="case_") as case_dir:
            root = Path(case_dir)
            script = root / "probe.py"
            script.write_text(
                "import sys, json, os\nfrom pathlib import Path\n"
                "import FreeCAD as App\nimport Import, Part\n"
                + "sys.path.insert(0, {!r})\n".format(str(PACKAGE_ROOT))
                + "import export_hinoki_lod3 as ex\n"
                + "root = Path({!r})\nmodel = Path({!r})\n".format(str(root), str(self.model_path))
                + "try:\n" + textwrap.indent(textwrap.dedent(body), "    ")
                + "\nexcept Exception:\n    import traceback\n    traceback.print_exc()\n    raise SystemExit(1)\n"
                + "print('ATOMIC_EXPORT_PROBE_OK')\nraise SystemExit(0)\n",
                encoding="utf-8",
            )
            result = run_freecad_script(script, os.environ.copy(), timeout=240)
            output = result.stdout + result.stderr
            self.assertEqual(0, result.returncode, output)
            self.assertIn("ATOMIC_EXPORT_PROBE_OK", output)

    def test_roundtrip_package_membership_scale_metadata_and_cleanup(self):
        self._probe('''
            target = root / "package"
            source_bytes = model.read_bytes()
            report = ex.export_package(model, target)
            assert model.read_bytes() == source_bytes
            assert not App.listDocuments()
            expected_files = {ex.p.OUTPUT_FILES[key] for key in ("head_step", "manifest_json", "validation_json")}
            assert {item.name for item in target.iterdir()} == expected_files
            manifest = json.loads((target / ex.p.OUTPUT_FILES["manifest_json"]).read_text())
            validation = json.loads((target / ex.p.OUTPUT_FILES["validation_json"]).read_text())
            assert validation == report and report["status"] == "Pass"
            assert report["step_export"]["units"] == "mm"
            assert report["step_export"]["body_count"] == 78
            assert manifest["limitations"] == ex.p.PROTOTYPE_LIMITATION
            assert len(manifest["parts"]) == 96
            source = App.openDocument(str(model))
            expected = {obj.Name: obj for obj in source.Objects if getattr(obj, "IsSemanticPart", False)
                        and obj.ParentAssembly != "08_Reference_Datums_Keepouts"
                        and getattr(obj, "PhysicalCollision", True)}
            exported = {row["name"] for row in manifest["parts"] if row["exported"]}
            assert exported == set(expected) == set(report["step_export"]["names"])
            for row in manifest["parts"]:
                original = source.getObject(row["name"])
                assert all(row[key] == getattr(original, key) for key in ex.p.METADATA_KEYS)
                assert row["ManufacturingAuthority"] is False
            reopened = App.newDocument("IndependentStepProbe")
            Import.insert(str(target / ex.p.OUTPUT_FILES["head_step"]), reopened.Name)
            # Semantic compound roots count once; importer children do not count again.
            assembly = reopened.getObject("Hinoki_LOD3_Head_Export")
            assert assembly is not None
            bodies = [obj for obj in assembly.Group if obj.TypeId in ("Part::Feature", "App::Part")]
            def body_name(obj):
                return obj.Name if obj.TypeId == "App::Part" else obj.Label
            assert len(bodies) == len(expected), [(obj.Name, obj.Label) for obj in reopened.Objects]
            assert {body_name(obj) for obj in bodies} == exported
            for obj in bodies:
                original = expected[body_name(obj)].Shape
                assert obj.Shape.isValid() and obj.Shape.Volume > 0
                assert len(obj.Shape.Solids) == len(original.Solids)
                assert abs(obj.Shape.Volume - original.Volume) <= max(0.01, original.Volume * 1e-7)
                for field in ("XMin", "YMin", "ZMin", "XMax", "YMax", "ZMax"):
                    assert abs(getattr(obj.Shape.BoundBox, field) - getattr(original.BoundBox, field)) <= 0.1
            for name in tuple(App.listDocuments()):
                App.closeDocument(name)
            assert not App.listDocuments()
        ''')

    def test_publication_failure_restores_every_old_or_absent_destination(self):
        self._probe('''
            from unittest.mock import patch
            for existing in ((), (0, 1, 2), (0, 2), (1,)):
                for failure_index in range(3):
                    target = root / (str(existing) + str(failure_index))
                    target.mkdir()
                    pairs = []
                    original = {}
                    for index, key in enumerate(("head_step", "manifest_json", "validation_json")):
                        destination = target / ex.p.OUTPUT_FILES[key]
                        if index in existing:
                            original[destination] = ("old-" + key).encode()
                            destination.write_bytes(original[destination])
                        stage = target / (".staged-" + destination.name)
                        stage.write_bytes(b"replacement")
                        pairs.append((stage, destination))
                    real_replace = os.replace
                    calls = []
                    def fail_once(source, destination):
                        assert Path(source).parent == Path(destination).parent
                        if len(calls) == failure_index:
                            calls.append("failed")
                            raise OSError("injected replacement failure")
                        calls.append("ok")
                        return real_replace(source, destination)
                    with patch.object(ex.os, "replace", side_effect=fail_once):
                        try:
                            ex._publish_files(pairs)
                        except OSError as error:
                            assert "injected replacement failure" in str(error)
                        else:
                            raise AssertionError("publication must fail")
                    assert {path: path.read_bytes() for path in target.iterdir()} == original
        ''')

    def test_reimport_rejects_wrong_membership_and_scale_with_no_document_leak(self):
        self._probe('''
            source = App.newDocument("ShapeSource")
            item = source.addObject("Part::Feature", "ExpectedPart")
            item.Label = item.Name
            item.Shape = Part.makeBox(10, 20, 30)
            expected = {item.Name: {"bbox_mm": [0, 0, 0, 10, 20, 30], "volume_mm3": 6000.0, "solid_count": 1}}
            for scenario in ("name", "scale"):
                item.Label = "WrongPart" if scenario == "name" else "ExpectedPart"
                item.Shape = Part.makeBox(10, 20, 30) if scenario == "name" else Part.makeBox(100, 200, 300)
                path = root / (scenario + ".step")
                Import.export([item], str(path))
                before = set(App.listDocuments())
                try:
                    ex._validate_step(path, expected)
                except RuntimeError:
                    pass
                else:
                    raise AssertionError("invalid STEP accepted: " + scenario)
                assert set(App.listDocuments()) == before
            App.closeDocument(source.Name)
        ''')

    def test_failed_step_validation_preserves_package_and_cleans_all_staging(self):
        self._probe('''
            from unittest.mock import patch
            target = root / "package"
            target.mkdir()
            original = {}
            for key in ("head_step", "manifest_json", "validation_json"):
                path = target / ex.p.OUTPUT_FILES[key]
                original[path] = ("old-" + key).encode()
                path.write_bytes(original[path])
            def fail_validation(path, expected):
                assert path.parent == target and path not in original
                assert path.suffix == ".step" and path.exists()
                raise RuntimeError("injected reimport failure")
            with patch.object(ex, "_validate_step", side_effect=fail_validation):
                try:
                    ex.export_package(model, target)
                except RuntimeError as error:
                    assert "injected reimport failure" in str(error)
                else:
                    raise AssertionError("export must fail")
            assert {path: path.read_bytes() for path in target.iterdir()} == original
            assert not App.listDocuments()
        ''')

    def test_corrupt_staged_json_is_not_published(self):
        self._probe('''
            from unittest.mock import patch
            target = root / "package"
            original_write = Path.write_text
            def corrupt_manifest(path, data, *args, **kwargs):
                if "Part_Manifest" in path.name:
                    data = json.dumps({"parts": [], "limitations": "incorrect"})
                return original_write(path, data, *args, **kwargs)
            with patch.object(Path, "write_text", new=corrupt_manifest):
                try:
                    ex.export_package(model, target)
                except RuntimeError as error:
                    assert "JSON" in str(error)
                else:
                    raise AssertionError("corrupted manifest accepted")
            assert list(target.iterdir()) == []
            assert not App.listDocuments()
        ''')

    def test_cli_missing_model_has_one_failure_sentinel_and_no_outputs(self):
        self.assertTrue(self.export_script.exists(), "Task 8 exporter must exist")
        with tempfile.TemporaryDirectory(dir=self.root) as case_dir:
            env = os.environ.copy()
            env["HINOKI_LOD3_MODEL_PATH"] = str(Path(case_dir) / "missing.FCStd")
            env["HINOKI_LOD3_EXPORT_DIR"] = case_dir
            result = run_freecad_script(self.export_script, env)
            output = result.stdout + result.stderr
            self.assertNotEqual(0, result.returncode, output)
            self.assertEqual(1, output.count("HINOKI_LOD3_EXPORT_FAIL"), output)
            self.assertNotIn("HINOKI_LOD3_EXPORT_OK", output)
            self.assertEqual([], list(Path(case_dir).iterdir()))


class TestReviewImages(unittest.TestCase):
    """Task 9: phone-review PNG generator (preview_hinoki_lod3.py).

    Exercises the deterministic preview pipeline: five PNGs at
    1600 x 1200 with white background, "shaded-with-edges" draw style
    (filled colour interior + darker outline stroke), readable file size
    (not truncated / not oversized), and atomic replacement of any
    pre-existing destination file.
    """

    EXPECTED_PREVIEWS = (
        "Hinoki_LOD3_Preview_Front.png",
        "Hinoki_LOD3_Preview_Rear.png",
        "Hinoki_LOD3_Preview_Isometric.png",
        "Hinoki_LOD3_Preview_Exploded.png",
        "Hinoki_LOD3_Preview_AirflowCutaway.png",
    )
    MIN_WIDTH = 1600
    MIN_HEIGHT = 1200
    MIN_SIZE_BYTES = 8 * 1024
    MAX_SIZE_BYTES = 5 * 1024 * 1024

    @classmethod
    def setUpClass(cls):
        cls.preview_script = PACKAGE_ROOT / "preview_hinoki_lod3.py"
        cls.workspace = tempfile.TemporaryDirectory(prefix="hinoki_lod3_preview_")
        cls.addClassCleanup(cls.workspace.cleanup)
        cls.root = Path(cls.workspace.name)
        cls.model_path = cls.root / "source.FCStd"
        cls.manifest_path = cls.root / "Hinoki_LOD3_Part_Manifest.json"
        cls.validation_path = cls.root / "Hinoki_LOD3_Validation.json"

        env = os.environ.copy()
        env["HINOKI_LOD3_MODEL_OUT"] = str(cls.model_path)
        build_result = run_freecad_script(BUILD_SCRIPT, env)
        if build_result.returncode or "HINOKI_LOD3_BUILD_OK" not in build_result.stdout:
            raise AssertionError(build_result.stdout + build_result.stderr)

        export_script = PACKAGE_ROOT / "export_hinoki_lod3.py"
        env_export = os.environ.copy()
        env_export["HINOKI_LOD3_MODEL_PATH"] = str(cls.model_path)
        env_export["HINOKI_LOD3_EXPORT_DIR"] = str(cls.root)
        export_result = run_freecad_script(export_script, env_export)
        if export_result.returncode or "HINOKI_LOD3_EXPORT_OK" not in export_result.stdout:
            raise AssertionError(export_result.stdout + export_result.stderr)

    def _run_preview(self, out_dir=None, extra_env=None):
        env = os.environ.copy()
        env["HINOKI_LOD3_MANIFEST_PATH"] = str(self.manifest_path)
        env["HINOKI_LOD3_PREVIEW_DIR"] = str(out_dir or self.root)
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            [sys.executable, str(self.preview_script)],
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=180,
        )

    def test_preview_script_exists(self):
        self.assertTrue(self.preview_script.exists(),
                        "Task 9 preview script must exist")

    def test_previews_produced_with_success_sentinel(self):
        with tempfile.TemporaryDirectory(dir=self.root, prefix="ok_") as tmp_dir:
            result = self._run_preview(out_dir=Path(tmp_dir))
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertIn("HINOKI_LOD3_PREVIEW_OK", result.stdout)
            self.assertNotIn("HINOKI_LOD3_PREVIEW_FAIL", result.stdout + result.stderr)
            for filename in self.EXPECTED_PREVIEWS:
                self.assertTrue((Path(tmp_dir) / filename).exists(),
                                "missing preview: " + filename)

    def test_preview_dimensions_and_size_within_bounds(self):
        from PIL import Image
        import sys as _sys
        with tempfile.TemporaryDirectory(dir=self.root, prefix="dims_") as tmp_dir:
            result = self._run_preview(out_dir=Path(tmp_dir))
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            for filename in self.EXPECTED_PREVIEWS:
                path = Path(tmp_dir) / filename
                size_bytes = path.stat().st_size
                self.assertGreaterEqual(size_bytes, self.MIN_SIZE_BYTES,
                                        (filename, "under-min", size_bytes))
                self.assertLessEqual(size_bytes, self.MAX_SIZE_BYTES,
                                     (filename, "over-max", size_bytes))
                with Image.open(path) as img:
                    self.assertGreaterEqual(img.width, self.MIN_WIDTH,
                                            (filename, img.size))
                    self.assertGreaterEqual(img.height, self.MIN_HEIGHT,
                                            (filename, img.size))
                    self.assertEqual(img.mode, "RGB", (filename, img.mode))

    def test_preview_white_background_and_shaded_with_edges(self):
        from PIL import Image
        with tempfile.TemporaryDirectory(dir=self.root, prefix="style_") as tmp_dir:
            result = self._run_preview(out_dir=Path(tmp_dir))
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            for filename in self.EXPECTED_PREVIEWS:
                path = Path(tmp_dir) / filename
                with Image.open(path) as img:
                    top_left = img.getpixel((5, 5))
                    top_right = img.getpixel((img.width - 6, 5))
                    self.assertEqual((255, 255, 255), top_left,
                                     (filename, "top-left not white"))
                    self.assertEqual((255, 255, 255), top_right,
                                     (filename, "top-right not white"))
                    centre = img.getpixel((img.width // 2, img.height // 2))
                    self.assertNotEqual((255, 255, 255), centre,
                                        (filename, "centre pixel is white; "
                                                   "no shaded part rendered"))
                    # Shaded-with-edges: rasterised polygons must include
                    # dark edge strokes AND filled interiors. Scan the
                    # central 60% of the canvas at 12 px pitch to prove
                    # the render includes at least one edge-dark pixel
                    # (sum(rgb) <= 270) and at least one non-white filled
                    # pixel (0 < sum(rgb) < 3*250).
                    xs = range(img.width // 5, img.width * 4 // 5, 12)
                    ys = range(img.height // 5, img.height * 4 // 5, 12)
                    samples = [img.getpixel((x, y)) for x in xs for y in ys]
                    darkest = min(samples, key=sum)
                    self.assertLessEqual(sum(darkest), 300,
                                         (filename, "no dark edge stroke detected", darkest))
                    filled = [s for s in samples if sum(s) < 3 * 250 and sum(s) > 0]
                    self.assertGreaterEqual(len(filled), 50,
                                            (filename, "not enough shaded interior fill",
                                             len(filled)))

    def test_atomic_replacement_of_existing_preview(self):
        with tempfile.TemporaryDirectory(dir=self.root, prefix="atomic_") as tmp_dir:
            tmp_root = Path(tmp_dir)
            placeholder = b"OLD_PREVIEW_BYTES_MUST_BE_REPLACED_ATOMICALLY"
            for filename in self.EXPECTED_PREVIEWS:
                (tmp_root / filename).write_bytes(placeholder)
            result = self._run_preview(out_dir=tmp_root)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            for filename in self.EXPECTED_PREVIEWS:
                new_bytes = (tmp_root / filename).read_bytes()
                self.assertNotEqual(placeholder, new_bytes,
                                    (filename, "atomic replace did not happen"))
                self.assertTrue(new_bytes.startswith(b"\x89PNG"),
                                (filename, "not a PNG after replace"))
            # No leftover .tmp files in the directory.
            leftovers = sorted(p.name for p in tmp_root.glob("*.tmp"))
            self.assertEqual([], leftovers,
                             ("stray temp file after atomic replace", leftovers))

    def test_missing_manifest_fails_without_partial_output(self):
        with tempfile.TemporaryDirectory(dir=self.root, prefix="missing_") as tmp_dir:
            tmp_root = Path(tmp_dir)
            missing_manifest = tmp_root / "does_not_exist.json"
            result = self._run_preview(
                out_dir=tmp_root,
                extra_env={"HINOKI_LOD3_MANIFEST_PATH": str(missing_manifest)},
            )
            self.assertNotEqual(0, result.returncode,
                                result.stdout + result.stderr)
            self.assertIn("HINOKI_LOD3_PREVIEW_FAIL", result.stdout + result.stderr)
            self.assertNotIn("HINOKI_LOD3_PREVIEW_OK", result.stdout)
            # Directory must contain no PNGs and no .tmp remnants.
            self.assertEqual([], list(tmp_root.glob("*.png")))
            self.assertEqual([], list(tmp_root.glob("*.tmp")))


if __name__ == "__main__":
    unittest.main()
