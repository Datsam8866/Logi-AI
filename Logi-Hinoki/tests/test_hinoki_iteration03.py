"""Contract checks for the Hinoki Calm Crown Iteration 03 CAD."""

from pathlib import Path
import importlib.util
import os
import subprocess
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CAD_ROOT = PROJECT_ROOT / "cad" / "iteration-03"
PARAMETERS_FILE = CAD_ROOT / "hinoki_calm_crown_parameters.py"
BUILD_SCRIPT = CAD_ROOT / "build_hinoki_calm_crown.py"
CAD_FILE = CAD_ROOT / "Hinoki_CalmCrown_Concept.FCStd"
FREECAD_CMD = Path(
    os.environ.get(
        "FREECAD_CMD",
        r"C:\Users\skuan1\AppData\Local\Programs\FreeCAD 1.1\bin\freecadcmd.exe",
    )
)


def load_parameters():
    spec = importlib.util.spec_from_file_location(
        "hinoki_calm_crown_parameters", PARAMETERS_FILE
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_freecad_script(script_path, env=None):
    return subprocess.run(
        [str(FREECAD_CMD), "-c"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
        env=env,
        input="exec(compile(open(r'{}', encoding='utf-8').read(), r'{}', 'exec'))\n".format(
            script_path.as_posix(), script_path.as_posix()
        ),
    )


class HinokiIteration03Tests(unittest.TestCase):
    def test_builder_uses_controlled_parameters_module(self):
        builder_source = BUILD_SCRIPT.read_text(encoding="utf-8")

        self.assertIn("hinoki_calm_crown_parameters", builder_source)
        self.assertNotIn("HEAD_WIDTH = 742.0", builder_source)
        self.assertNotIn("HEAD_HEIGHT = 492.0", builder_source)
        self.assertNotIn("HEAD_DEPTH = 62.0", builder_source)
        self.assertNotIn("CROWN_HEIGHT = 72.0", builder_source)

    def test_parameter_contract_matches_approved_design(self):
        self.assertTrue(PARAMETERS_FILE.exists())
        p = load_parameters()

        self.assertEqual(
            p.HEAD,
            {
                "width": 742.0,
                "height": 492.0,
                "depth": 62.0,
                "corner_radius": 18.0,
            },
        )
        self.assertEqual(p.CROWN_HEIGHT, 72.0)
        self.assertEqual(p.HEAD_BOTTOM_Y, 115.0)
        self.assertEqual(p.ACTIVE_AREA, {"width": 708.4, "height": 398.5})
        self.assertEqual(p.VESA_PATTERN, 100.0)
        self.assertEqual(
            p.STAND_MOTION,
            {"travel": 120.0, "tilt_forward": -5.0, "tilt_rear": 20.0},
        )
        self.assertEqual(
            p.BASE, {"width": 420.0, "depth": 285.0, "height": 68.0}
        )
        self.assertEqual(
            p.BASE_POWER, {"width": 360.0, "depth": 240.0, "height": 45.0}
        )
        self.assertEqual(
            p.BALLAST, {"width": 380.0, "depth": 250.0, "height": 8.0}
        )

        expected_export_objects = (
            "Front_Glass",
            "Display_Mask",
            "Crown_Shell",
            "Speaker_Insert_Left",
            "Speaker_Insert_Right",
            "Camera_Pill",
            "Camera_Lens_Window",
            "Shutter_Rail",
            "Shutter_Tab_Open",
            "Fill_Light_Left",
            "Fill_Light_Right",
            "Radar_Window",
            "ALS_Window",
            "Rear_Shell",
            "Rear_Service_Cover",
            "Vent_Insert_Lower",
            "IO_Recess",
            "Stand_Fixed_Spine",
            "Stand_Moving_Spine",
            "Pivot_Pod",
            "VESA_Interface_Cover",
            "Base_Upper",
            "Base_Lower",
            "Foot_Left",
            "Foot_Right",
        )
        expected_mic_apertures = (
            "Mic_Aperture_Left_Outer",
            "Mic_Aperture_Left_Inner",
            "Mic_Aperture_Right_Inner",
            "Mic_Aperture_Right_Outer",
        )
        self.assertEqual(p.PRODUCT_EXPORT_OBJECTS, expected_export_objects)
        self.assertIn("Front_Glass", p.PRODUCT_EXPORT_OBJECTS)
        self.assertIn("Rear_Service_Cover", p.PRODUCT_EXPORT_OBJECTS)
        self.assertNotIn("Camera_FOV_KeepOut", p.PRODUCT_EXPORT_OBJECTS)
        self.assertEqual(
            p.FRONT_ARCHITECTURE_OBJECTS, expected_export_objects[:13]
        )
        self.assertEqual(
            p.REQUIRED_VISIBLE_OBJECTS,
            expected_export_objects + expected_mic_apertures,
        )
        self.assertEqual(
            p.REQUIRED_INTERNAL_CLAIMS,
            (
                "Panel_Touch_Claim",
                "Speaker_Claim_Left",
                "Speaker_Claim_Right",
                "Camera_ISP_Claim",
                "QC7790_Claim",
                "Heat_Spreader_Claim",
                "USB_C_Interface_Claim",
                "Rear_IO_Board_Claim",
                "VESA_Reinforcement_Claim",
                "Base_Power_PD_Claim",
                "Ballast_Claim",
                "Cable_Loop_Claim",
            ),
        )

        expected_score_weights = {
            "external_design_completeness": 0.15,
            "architecture_consistency": 0.20,
            "visual_communication": 0.10,
            "geometry_health": 0.20,
            "step_portability": 0.10,
            "requirement_traceability": 0.15,
            "risk_integrity": 0.10,
        }
        self.assertEqual(p.SCORE_WEIGHTS, expected_score_weights)
        self.assertAlmostEqual(sum(p.SCORE_WEIGHTS.values()), 1.0)
        self.assertEqual(p.CONCEPT_SCORE_THRESHOLD, 80.0)
        self.assertEqual(
            p.MINIMUM_CATEGORY_SCORES,
            {
                "external_design_completeness": 3,
                "architecture_consistency": 4,
                "visual_communication": 3,
                "geometry_health": 4,
                "step_portability": 4,
                "requirement_traceability": 4,
                "risk_integrity": 3,
            },
        )

    def test_native_cad_contains_finished_head_and_visible_front_architecture(self):
        self.assertTrue(FREECAD_CMD.exists(), "FreeCAD command-line executable must exist")
        self.assertTrue(BUILD_SCRIPT.exists(), "Iteration 03 builder must exist")
        self.assertTrue(CAD_FILE.exists(), "Tracked Iteration 03 CAD must exist")

        original_cad_bytes = CAD_FILE.read_bytes()
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary_cad_file = Path(temp_dir) / "Hinoki_CalmCrown_Concept.FCStd"
            builder_env = os.environ.copy()
            builder_env["HINOKI_CALM_CROWN_OUTPUT_PATH"] = str(temporary_cad_file)
            run_freecad_script(BUILD_SCRIPT, env=builder_env)
            self.assertTrue(
                temporary_cad_file.exists(), "Iteration 03 native CAD must be created"
            )
            self.assertEqual(
                CAD_FILE.read_bytes(),
                original_cad_bytes,
                "Builder test must not overwrite tracked Iteration 03 CAD",
            )

            probe = """
import FreeCAD as App
doc = App.open(r'{cad_file}')
required = [
    'Visible_ID_Surfaces', 'Structure', 'Internal_Space_Claims',
    'Datums_and_Motion', 'Review_Metadata', 'Front_Glass', 'Display_Mask',
    'Crown_Shell', 'Speaker_Insert_Left', 'Speaker_Insert_Right',
    'Camera_Pill', 'Camera_Lens_Window', 'Shutter_Rail', 'Shutter_Tab_Open',
    'Fill_Light_Left', 'Fill_Light_Right', 'Radar_Window', 'ALS_Window'
]
missing = [name for name in required if doc.getObject(name) is None]
assert not missing, 'Missing objects: ' + ', '.join(missing)
assert tuple(obj.Name for obj in doc.getObject('Visible_ID_Surfaces').Group) == (
    'Front_Glass', 'Display_Mask', 'Crown_Shell', 'Speaker_Insert_Left',
    'Speaker_Insert_Right', 'Camera_Pill', 'Camera_Lens_Window', 'Shutter_Rail',
    'Shutter_Tab_Open', 'Fill_Light_Left', 'Fill_Light_Right', 'Radar_Window',
    'ALS_Window'
)

front_glass = doc.getObject('Front_Glass')
crown_shell = doc.getObject('Crown_Shell')
assert front_glass.Shape.isValid(), 'Front glass must be a valid solid'
assert crown_shell.Shape.isValid(), 'Crown shell must be a valid solid'
assert abs(front_glass.Shape.BoundBox.XLength - 742.0) < 1e-6
assert abs(front_glass.Shape.BoundBox.YLength - 492.0) < 1e-6
assert abs(front_glass.Shape.BoundBox.YMin - 115.0) < 1e-6
assert front_glass.Shape.Volume < 742.0 * 492.0 * front_glass.Shape.BoundBox.ZLength

metadata = doc.getObject('Model_Parameters')
assert metadata is not None, 'Model parameters must record datum conventions'
assert abs(metadata.HeadBottomY - 115.0) < 1e-6
assert metadata.CoordinateSystem == 'X left/right; Y vertical; Z rearward'

for name in required[5:]:
    obj = doc.getObject(name)
    assert obj.Shape.isValid(), name + ' must have valid geometry'
    assert obj.Classification, name + ' must declare Classification'
    assert obj.RequirementIDs, name + ' must declare RequirementIDs'
    assert 'AssumptionIDs' in obj.PropertiesList

front_z_starts = {{
    round(doc.getObject(name).Shape.BoundBox.ZMin, 3)
    for name in ('Front_Glass', 'Display_Mask', 'Crown_Shell', 'Camera_Pill')
}}
assert len(front_z_starts) == 4, 'Front layers need controlled non-coplanar Z datums'
print('Calm Crown native front architecture checks passed')
""".format(cad_file=temporary_cad_file.as_posix())
            result = subprocess.run(
            [str(FREECAD_CMD), "-c"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
            input=probe,
            )
        self.assertIn(
            "Calm Crown native front architecture checks passed", result.stdout
        )


if __name__ == "__main__":
    unittest.main()
