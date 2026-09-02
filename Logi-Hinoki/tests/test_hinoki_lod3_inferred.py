"""Contract and geometry tests for the Hinoki LOD 3 inferred prototype."""

from importlib.util import module_from_spec, spec_from_file_location
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = PROJECT_ROOT / "cad" / "lod3-inferred-prototype-01"
PARAMETERS_FILE = PACKAGE_ROOT / "hinoki_lod3_parameters.py"
SOURCES_FILE = PACKAGE_ROOT / "hinoki_lod3_sources.py"
BUILD_SCRIPT = PACKAGE_ROOT / "build_hinoki_lod3_master.py"
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


class TestFrozenEngineeringContract(unittest.TestCase):
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
        self.assertEqual(10, len(p.HEAT_LOADS_W))
        self.assertAlmostEqual(57.0, sum(p.HEAT_LOADS_W.values()), places=9)

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
    "Backlight_Unit": (716.0, 406.0, 12.0),
}}
for name, dimensions in expected_layers.items():
    obj = doc.getObject(name)
    assert obj is not None and obj.Shape.isValid() and obj.Shape.Volume > 0.0
    actual = (obj.Shape.BoundBox.XLength, obj.Shape.BoundBox.YLength, obj.Shape.BoundBox.ZLength)
    assert all(abs(a - b) <= 0.01 for a, b in zip(actual, dimensions)), (name, actual)
    assert obj.ManufacturingAuthority is False
    assert obj.SourceReference

rear = doc.getObject("Rear_Enclosure")
assert rear.Shape.isValid() and rear.Shape.Volume > 0.0
assert abs(rear.WallThickness.Value - 2.8) <= 0.001
assert abs(rear.InletOpenArea.Value - 6000.0) <= 0.1
assert abs(rear.OutletOpenArea.Value - 6000.0) <= 0.1

rib = doc.getObject("Structural_Rib_01")
boss = doc.getObject("Primary_Boss_01")
assert abs(rib.RibThickness.Value - 1.7) <= 0.001
assert abs(boss.BossOuterDiameter.Value - 7.0) <= 0.001
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
    "Heat_QC7790": (35.0, 35.0, 2.0),
    "TIM_QC7790": (35.0, 35.0, 1.0),
    "Copper_Spreader": (100.0, 80.0, 2.0),
    "Aluminum_Interface": (220.0, 120.0, 2.5),
    "Rear_Hatch_TIM": (80.0, 40.0, 1.5),
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
assert len(heat_parts) == 10, [(obj.Name, obj.HeatLoadW) for obj in heat_parts]
assert abs(sum(obj.HeatLoadW for obj in heat_parts) - 57.0) <= 1e-9
assert {{obj.HeatSourceID for obj in heat_parts}} == {heat_names!r}

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
                        "Heat_Panel_Backlight",
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


if __name__ == "__main__":
    unittest.main()
