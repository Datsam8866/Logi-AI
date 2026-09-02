"""Contract checks for the Hinoki Calm Crown Iteration 03 CAD."""

from pathlib import Path
import ast
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


def run_freecad_script(script_path, env=None, cwd=PROJECT_ROOT):
    return subprocess.run(
        [str(FREECAD_CMD), "-c"],
        cwd=cwd,
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
        builder_tree = ast.parse(BUILD_SCRIPT.read_text(encoding="utf-8"))
        assignments = {
            target.id: node.value
            for node in builder_tree.body
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name)
        }
        expected_head_dimensions = {
            "HEAD_WIDTH": "width",
            "HEAD_HEIGHT": "height",
            "HEAD_DEPTH": "depth",
            "HEAD_RADIUS": "corner_radius",
        }

        for name, dimension in expected_head_dimensions.items():
            controlled_dimension = assignments[name]
            self.assertIsInstance(controlled_dimension, ast.Subscript)
            self.assertIsInstance(controlled_dimension.value, ast.Attribute)
            self.assertIsInstance(controlled_dimension.value.value, ast.Name)
            self.assertEqual(controlled_dimension.value.value.id, "parameters")
            self.assertEqual(controlled_dimension.value.attr, "HEAD")
            self.assertEqual(controlled_dimension.slice.value, dimension)

        for name in ("HEAD_BOTTOM_Y", "CROWN_HEIGHT"):
            controlled_dimension = assignments[name]
            self.assertIsInstance(controlled_dimension, ast.Attribute)
            self.assertIsInstance(controlled_dimension.value, ast.Name)
            self.assertEqual(controlled_dimension.value.id, "parameters")
            self.assertEqual(controlled_dimension.attr, name)

    def test_builder_derives_active_area_x_origin_from_controlled_width(self):
        builder_tree = ast.parse(BUILD_SCRIPT.read_text(encoding="utf-8"))
        active_opening = next(
            node
            for node in ast.walk(builder_tree)
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "active_opening"
                for target in node.targets
            )
        )

        origin_x = active_opening.value.args[4].elts[0]
        self.assertIsInstance(origin_x, ast.BinOp)
        self.assertIsInstance(origin_x.op, ast.Div)
        self.assertIsInstance(origin_x.left, ast.UnaryOp)
        self.assertIsInstance(origin_x.left.op, ast.USub)
        controlled_width = origin_x.left.operand
        self.assertIsInstance(controlled_width, ast.Subscript)
        self.assertIsInstance(controlled_width.value, ast.Attribute)
        self.assertEqual(controlled_width.value.attr, "ACTIVE_AREA")
        self.assertEqual(controlled_width.slice.value, "width")

    def test_builder_derives_crown_traceability_text_from_controlled_height(self):
        builder_tree = ast.parse(BUILD_SCRIPT.read_text(encoding="utf-8"))
        controlled_height = next(
            node
            for node in ast.walk(builder_tree)
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "CROWN_HEIGHT"
                for target in node.targets
            )
        )
        self.assertIsInstance(controlled_height.value, ast.Attribute)
        self.assertIsInstance(controlled_height.value.value, ast.Name)
        self.assertEqual(controlled_height.value.value.id, "parameters")
        self.assertEqual(controlled_height.value.attr, "CROWN_HEIGHT")

        crown_feature = next(
            node
            for node in ast.walk(builder_tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "add_feature"
            and isinstance(node.args[2], ast.Constant)
            and node.args[2].value == "Crown_Shell"
        )

        requirement_text = crown_feature.args[7]
        self.assertIsInstance(requirement_text, ast.Call)
        self.assertIsInstance(requirement_text.func, ast.Attribute)
        self.assertEqual(requirement_text.func.attr, "format")
        self.assertIsInstance(requirement_text.args[0], ast.Name)
        self.assertEqual(requirement_text.args[0].id, "CROWN_HEIGHT")

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

    def test_native_cad_contains_rear_architecture_and_internal_claims(self):
        """Task 3 rear parts and reference-only claims are machine traceable."""
        self.assertTrue(FREECAD_CMD.exists(), "FreeCAD command-line executable must exist")

        original_cad_bytes = CAD_FILE.read_bytes()
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary_cad_file = Path(temp_dir) / "Hinoki_CalmCrown_Concept.FCStd"
            builder_env = os.environ.copy()
            builder_env["HINOKI_CALM_CROWN_OUTPUT_PATH"] = str(temporary_cad_file)
            run_freecad_script(BUILD_SCRIPT, env=builder_env)
            self.assertEqual(
                CAD_FILE.read_bytes(),
                original_cad_bytes,
                "Builder test must not overwrite tracked Iteration 03 CAD",
            )

            probe = """
import FreeCAD as App
doc = App.open(r'{cad_file}')
visible_names = ('Rear_Shell', 'Rear_Service_Cover', 'Vent_Insert_Lower', 'IO_Recess')
claim_names = {claim_names!r}
required = visible_names + claim_names
missing = [name for name in required if doc.getObject(name) is None]
assert not missing, 'Missing Task 3 objects: ' + ', '.join(missing)

for name in required:
    obj = doc.getObject(name)
    assert obj.TypeId == 'Part::Feature', name + ' must be a Part::Feature'
    assert obj.Shape.isValid(), name + ' must have valid geometry'
    assert obj.Shape.Volume > 0.0, name + ' must have positive volume'
    for property_name in ('Classification', 'RequirementIDs', 'AssumptionIDs',
                          'ExportPolicy', 'Source', 'ReviewStatus'):
        assert property_name in obj.PropertiesList, name + ' missing ' + property_name
        assert getattr(obj, property_name), name + ' must set ' + property_name

rear_shell = doc.getObject('Rear_Shell')
service_cover = doc.getObject('Rear_Service_Cover')
vent = doc.getObject('Vent_Insert_Lower')
io_recess = doc.getObject('IO_Recess')
product_parts = [
    obj for obj in doc.Objects
    if obj.TypeId == 'Part::Feature'
    and getattr(obj, 'ExportPolicy', '') == 'ProductGeometry'
]
assert product_parts, 'CAD must contain product solids'
for obj in product_parts:
    assert obj.Shape.isValid(), obj.Name + ' product solid must be valid'
    assert obj.Shape.Volume > 0.0, obj.Name + ' product solid must have positive volume'
assert rear_shell.Shape.BoundBox.ZMax > 0.0
assert rear_shell.Shape.BoundBox.ZLength > service_cover.Shape.BoundBox.ZLength
assert abs(service_cover.Shape.BoundBox.XLength - 260.0) < 1e-6
assert abs(service_cover.Shape.BoundBox.YLength - 220.0) < 1e-6
assert vent.Shape.BoundBox.YMin < service_cover.Shape.BoundBox.YMin
assert io_recess.Shape.BoundBox.ZMin >= rear_shell.Shape.BoundBox.ZMin

for name in claim_names:
    obj = doc.getObject(name)
    assert obj.ExportPolicy == 'ReferenceOnly', name + ' must be reference-only'
    assert 'DefaultVisibility' in obj.PropertiesList
    assert not obj.DefaultVisibility, name + ' must be hidden by default'

vesa = doc.getObject('VESA_Reinforcement_Claim')
assert 'VESAPattern' in vesa.PropertiesList
assert abs(vesa.VESAPattern.Value - 100.0) < 1e-6
print('Calm Crown native rear and internal architecture checks passed')
""".format(
                cad_file=temporary_cad_file.as_posix(),
                claim_names=load_parameters().REQUIRED_INTERNAL_CLAIMS,
            )
            result = subprocess.run(
                [str(FREECAD_CMD), "-c"],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
                input="exec({!r})\n".format(probe),
            )
        self.assertIn(
            "Calm Crown native rear and internal architecture checks passed",
            result.stdout + result.stderr,
        )

    def test_builder_runs_from_non_project_cwd_with_absolute_paths(self):
        self.assertTrue(FREECAD_CMD.exists(), "FreeCAD command-line executable must exist")
        non_project_cwd = Path(os.environ.get("WINDIR", r"C:\\Windows")) / "Temp"
        self.assertTrue(non_project_cwd.exists(), "Windows temporary directory must exist")

        with tempfile.TemporaryDirectory() as temp_dir:
            temporary_cad_file = Path(temp_dir) / "Hinoki_CalmCrown_Concept.FCStd"
            builder_env = os.environ.copy()
            builder_env["HINOKI_CALM_CROWN_OUTPUT_PATH"] = str(temporary_cad_file)
            result = run_freecad_script(
                BUILD_SCRIPT, env=builder_env, cwd=non_project_cwd
            )
            self.assertIn(
                "Hinoki Calm Crown architecture generated:", result.stdout
            )
            self.assertTrue(temporary_cad_file.exists())

            probe = """
import FreeCAD as App
doc = App.open(r'{cad_file}')
assert doc.getObject('Front_Glass') is not None
assert doc.getObject('Front_Glass').Shape.isValid()
print('Calm Crown non-project cwd build checks passed')
""".format(cad_file=temporary_cad_file.as_posix())
            result = subprocess.run(
                [str(FREECAD_CMD), "-c"],
                cwd=non_project_cwd,
                check=True,
                capture_output=True,
                text=True,
                input=probe,
            )
        self.assertIn("Calm Crown non-project cwd build checks passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
