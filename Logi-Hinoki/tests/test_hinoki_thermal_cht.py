"""Contract checks for the approved Hinoki FLOEFD thermal CHT case."""

from importlib.util import module_from_spec, spec_from_file_location
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PARAMETERS_FILE = PROJECT_ROOT / "cad" / "thermal-simulation-01" / "hinoki_thermal_parameters.py"
BUILD_SCRIPT = PROJECT_ROOT / "cad" / "thermal-simulation-01" / "build_hinoki_thermal_cht.py"
CAD_FILE = PROJECT_ROOT / "cad" / "thermal-simulation-01" / "Hinoki_Thermal_CHT_Model.FCStd"
FREECAD_CMD = Path(
    os.environ.get(
        "FREECAD_CMD",
        r"C:\\Users\\skuan1\\AppData\\Local\\Programs\\FreeCAD 1.1\\bin\\freecadcmd.exe",
    )
)


def load_parameters():
    spec = spec_from_file_location("hinoki_thermal_parameters", PARAMETERS_FILE)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_freecad_builder(script_path, env):
    """Run source as an absolute compiled script from the system temp directory."""
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
    )


class HinokiThermalCHTTests(unittest.TestCase):
  def test_parameter_contract_matches_approved_floefd_case(self):
    self.assertTrue(PARAMETERS_FILE.exists(), "thermal parameters module must exist")
    p = load_parameters()

    self.assertEqual(p.HEAD, {"width": 742.0, "height": 492.0, "depth": 62.0})
    self.assertEqual(p.GLASS_THICKNESS, 3.0)
    self.assertEqual(p.REAR_WALL, 2.5)
    self.assertEqual(p.MIDFRAME_THICKNESS, 2.0)
    self.assertEqual(p.ACTIVE_AREA, {"width": 708.4, "height": 398.5})
    self.assertEqual(p.AMBIENT_C, 35.0)
    self.assertEqual(p.COOLING_MODE, "NaturalConvection")
    self.assertEqual(p.GRAVITY_MM_S2, (0.0, -9810.0, 0.0))
    self.assertEqual(p.VENT, {"width": 400.0, "height": 15.0, "area": 6000.0})

    self.assertEqual(p.HEAT_LOADS_W, {
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
    })
    self.assertEqual(len(p.HEAT_LOADS_W), 10)
    self.assertEqual(sum(p.HEAT_LOADS_W.values()), 57.0)

    self.assertEqual(p.SOLID_BODIES, (
        "Cover_Glass",
        "Mid_Frame",
        "Rear_Enclosure",
        "Heat_Panel_Backlight",
        "Carrier_PCB",
        "Heat_Spreader",
        "TIM_QC7790",
        "Heat_QC7790",
        "Heat_Memory",
        "Heat_Carrier_PMIC",
        "Heat_IO",
        "Heat_WiFi_BLE",
        "Heat_Camera",
        "Heat_Audio",
        "Heat_Radar_ALS",
        "Heat_Front_Lighting",
    ))
    self.assertEqual(p.FLUID_BODIES, ("Internal_Air_Volume",))
    self.assertEqual(p.BOUNDARY_FACES, (
        "Inlet_Opening_Lower_Rear",
        "Outlet_Opening_Upper_Rear",
    ))

    expected_materials = {
        "Cover_Glass": "Generic glass",
        "Heat_Panel_Backlight": "FLOEFD equivalent display stack",
        "Mid_Frame": "Aluminum 6061",
        "Rear_Enclosure": "PC/ABS",
        "Carrier_PCB": "FLOEFD equivalent PCB",
        "Heat_Spreader": "Aluminum 6061",
        "TIM_QC7790": "Isotropic TIM; k=3 W/m-K",
        "Internal_Air_Volume": "Air",
    }
    for body, material in expected_materials.items():
        self.assertEqual(p.MATERIAL_INTENT[body], material)
    self.assertEqual(set(p.SOLID_BODIES) | set(p.FLUID_BODIES), set(p.MATERIAL_INTENT))

    self.assertEqual(p.MODEL_FILE, "Hinoki_Thermal_CHT_Model.FCStd")
    self.assertEqual(p.SOLIDS_STEP, "Hinoki_Thermal_CHT_Solids.step")
    self.assertEqual(p.AIR_STEP, "Hinoki_Thermal_Internal_Air.step")
    self.assertEqual(p.SETUP_JSON, "Hinoki_Thermal_FLOEFD_Setup.json")
    self.assertEqual(p.REVIEW_JSON, "Hinoki_Thermal_CHT_Review.json")

  def test_native_thermal_cht_builder_creates_reopenable_complete_model(self):
    """The thermal builder must produce a complete, native CHT handoff model."""
    self.assertTrue(FREECAD_CMD.exists(), "FreeCAD command-line executable must exist")
    self.assertTrue(BUILD_SCRIPT.exists(), "thermal CHT builder must exist")
    self.assertTrue(CAD_FILE.exists(), "tracked formal FCStd must exist")
    original_cad_bytes = CAD_FILE.read_bytes()
    p = load_parameters()

    with tempfile.TemporaryDirectory() as temp_dir:
      temporary_cad = Path(temp_dir) / p.MODEL_FILE
      builder_env = os.environ.copy()
      builder_env["HINOKI_THERMAL_MODEL_PATH"] = str(temporary_cad)
      result = run_freecad_builder(BUILD_SCRIPT, builder_env)
      combined_output = result.stdout + result.stderr
      self.assertEqual(result.returncode, 0, combined_output)
      self.assertIn("HINOKI_THERMAL_BUILD_OK", combined_output)
      self.assertTrue(temporary_cad.exists(), "builder must create the requested FCStd")

      probe = r'''
import FreeCAD as App

doc = App.open(r"{cad_file}")
required_groups = (
    "Thermal_Solids", "Heat_Sources", "Fluid_Regions",
    "Boundary_References", "Thermal_Metadata",
)
group_names = tuple(
    obj.Name for obj in doc.Objects if obj.TypeId == "App::DocumentObjectGroup"
)
assert group_names == required_groups, "top groups: " + repr(group_names)

solid_names = {solid_names!r}
for name in solid_names:
    obj = doc.getObject(name)
    assert obj is not None, "missing solid " + name
    assert obj.TypeId == "Part::Feature", name + " must be a Part::Feature"
    assert obj.Shape.isValid() and obj.Shape.Volume > 0.0, name + " must be valid"
    assert obj.Shape.Solids, name + " must contain leaf solids"
    for leaf in obj.Shape.Solids:
        assert leaf.isValid() and leaf.isClosed(), name + " leaf must be closed"
    assert obj.Classification and obj.MaterialIntent and obj.Units == "mm"

air = doc.getObject("Internal_Air_Volume")
assert air is not None and air.Shape.isValid() and air.Shape.Volume > 0.0
assert len(air.Shape.Solids) == 1, "internal air must be one connected solid"
assert air.MaterialIntent == "Air" and air.Units == "mm"

for name in {boundary_names!r}:
    boundary = doc.getObject(name)
    assert boundary is not None and boundary.Shape.isValid(), "missing boundary " + name
    assert boundary.Classification == "ReferenceOnly"
    assert boundary.ExportPolicy == "ReferenceOnly"
    assert abs(boundary.Shape.Area - {vent_area!r}) < 0.1
    normal = boundary.Shape.normalAt(0.0, 0.0)
    assert normal.z > 0.999, name + " normal must face +Z"
    assert abs(boundary.Shape.BoundBox.ZMin - {head_depth!r}) < 1e-6
    assert air.Shape.common(boundary.Shape).Area > 5999.9, name + " must open to air"

glass = doc.getObject("Cover_Glass").Shape.BoundBox
panel = doc.getObject("Heat_Panel_Backlight").Shape.BoundBox
mid = doc.getObject("Mid_Frame").Shape.BoundBox
rear = doc.getObject("Rear_Enclosure").Shape
assert (glass.XMin, glass.YMin, glass.ZMin) == (-371.0, 0.0, 0.0)
assert (glass.XLength, glass.YLength, glass.ZLength) == (742.0, 492.0, 3.0)
assert abs(panel.XMin + 354.2) < 1e-6 and abs(panel.YMin - 28.0) < 1e-6
assert (panel.XLength, panel.YLength, panel.ZLength) == (708.4, 398.5, 12.0)
assert (mid.XMin, mid.YMin, mid.ZMin) == (-368.5, 2.5, 15.0)
assert (mid.XLength, mid.YLength, mid.ZLength) == (737.0, 487.0, 2.0)
assert rear.isValid() and rear.Volume > 0.0
assert abs(rear.BoundBox.ZMax - 62.0) < 1e-6

stack = ("Mid_Frame", "Heat_Spreader", "TIM_QC7790", "Heat_QC7790", "Carrier_PCB")
for lower, upper in zip(stack, stack[1:]):
    lower_shape = doc.getObject(lower).Shape
    upper_shape = doc.getObject(upper).Shape
    assert lower_shape.common(upper_shape).Volume < 1e-7
    assert abs(lower_shape.BoundBox.ZMax - upper_shape.BoundBox.ZMin) < 1e-6
for name in ("Heat_Memory", "Heat_Carrier_PMIC"):
    shape = doc.getObject(name).Shape
    assert abs(shape.BoundBox.ZMin - 21.0) < 1e-6
    assert abs(shape.BoundBox.ZMax - 23.0) < 1e-6
    assert shape.common(doc.getObject("Heat_QC7790").Shape).Volume < 1e-7
    assert abs(shape.BoundBox.ZMax - doc.getObject("Carrier_PCB").Shape.BoundBox.ZMin) < 1e-6

loads = {loads!r}
observed_heat = 0.0
for name, expected in loads.items():
    obj = doc.getObject(name)
    assert "HeatLoadW" in obj.PropertiesList, name + " needs a heat load"
    assert abs(obj.HeatLoadW - expected) < 1e-6
    observed_heat += obj.HeatLoadW
assert abs(observed_heat - 57.0) < 1e-6

materials = {materials!r}
for name, expected in materials.items():
    assert doc.getObject(name).MaterialIntent == expected

metadata = doc.getObject("Thermal_Model_Metadata")
assert metadata is not None
assert abs(metadata.AmbientC - 35.0) < 1e-6
assert tuple(metadata.GravityMmS2) == (0.0, -9810.0, 0.0)
assert abs(metadata.TotalHeatW - 57.0) < 1e-6
assert metadata.CoolingMode == "NaturalConvection"
print("HINOKI_THERMAL_REOPEN_OK")
'''.format(
          cad_file=temporary_cad.as_posix(),
          solid_names=p.SOLID_BODIES,
          boundary_names=p.BOUNDARY_FACES,
          vent_area=p.VENT["area"],
          head_depth=p.HEAD["depth"],
          loads=dict(p.HEAT_LOADS_W),
          materials=dict(p.MATERIAL_INTENT),
      )
      reopen = subprocess.run(
          [str(FREECAD_CMD), "-c"],
          cwd=Path(tempfile.gettempdir()),
          input="exec({!r})\n".format(probe),
          capture_output=True,
          text=True,
          check=False,
      )
      self.assertEqual(reopen.returncode, 0, reopen.stdout + reopen.stderr)
      self.assertIn("HINOKI_THERMAL_REOPEN_OK", reopen.stdout + reopen.stderr)
      self.assertEqual(
          CAD_FILE.read_bytes(),
          original_cad_bytes,
          "temporary builder test must not alter the tracked formal FCStd",
      )
