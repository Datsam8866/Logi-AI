"""Contract checks for the approved Hinoki FLOEFD thermal CHT case."""

from importlib.util import module_from_spec, spec_from_file_location
import ast
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
        timeout=120,
    )


def thermal_validation_probe(cad_file, p):
    """Return one native FreeCAD probe shared by temporary and formal FCStds."""
    return r'''
import FreeCAD as App
import Part
import hashlib
import itertools

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
heat_loads = {loads!r}
boundary_names = {boundary_names!r}
expected_group_members = {{
    "Thermal_Solids": set(solid_names) - set(heat_loads),
    "Heat_Sources": set(heat_loads),
    "Fluid_Regions": {{"Internal_Air_Volume"}},
    "Boundary_References": set(boundary_names),
    "Thermal_Metadata": {{"Thermal_Model_Metadata"}},
}}
for group_name, expected_members in expected_group_members.items():
    actual_members = {{obj.Name for obj in doc.getObject(group_name).Group}}
    assert actual_members == expected_members, group_name + " membership: " + repr(actual_members)

for name in solid_names:
    obj = doc.getObject(name)
    assert obj is not None, "missing solid " + name
    assert obj.TypeId == "Part::Feature", name + " must be a Part::Feature"
    assert obj.Shape.isValid() and obj.Shape.Volume > 0.0, name + " must be valid"
    assert obj.Shape.Solids, name + " must contain leaf solids"
    for leaf in obj.Shape.Solids:
        assert leaf.isValid() and leaf.isClosed() and leaf.Volume > 0.0, name + " leaf must be closed"
    assert obj.Classification and obj.MaterialIntent and obj.Units == "mm"

air = doc.getObject("Internal_Air_Volume")
assert air is not None and air.Shape.isValid() and air.Shape.Volume > 0.0
assert len(air.Shape.Solids) == 1, "internal air must be one connected solid"
assert air.MaterialIntent == "Air" and air.Units == "mm"
air_solid_overlaps = [
    (air.Shape.common(doc.getObject(name).Shape).Volume, name)
    for name in solid_names
]
max_air_solid_overlap, max_air_solid_name = max(air_solid_overlaps)
assert max_air_solid_overlap <= 0.01, "Internal air overlaps " + max_air_solid_name

head_width = {head_width!r}
head_height = {head_height!r}
head_depth = {head_depth!r}
rear_wall = {rear_wall!r}
vent_width = {vent_width!r}
vent_height = {vent_height!r}
vent_area = {vent_area!r}
lower_vent_y = 20.0
upper_vent_y = head_height - lower_vent_y - vent_height
vent_channels = [
    Part.makeBox(
        vent_width, vent_height, rear_wall,
        App.Vector(-vent_width / 2.0, y_origin, head_depth - rear_wall),
    )
    for y_origin in (lower_vent_y, upper_vent_y)
]
rear = doc.getObject("Rear_Enclosure").Shape
for name in boundary_names:
    boundary = doc.getObject(name)
    assert boundary is not None and boundary.Shape.isValid(), "missing boundary " + name
    assert boundary.Shape.ShapeType == "Face", name + " must be a face"
    assert boundary.Classification == "ReferenceOnly"
    assert boundary.ExportPolicy == "ReferenceOnly"
    assert abs(boundary.Shape.Area - vent_area) < 0.1
    normal = boundary.Shape.normalAt(0.0, 0.0)
    assert normal.z > 0.999, name + " normal must face +Z"
    assert abs(boundary.Shape.BoundBox.ZMin - head_depth) < 1e-6
    assert rear.common(boundary.Shape).Area <= 0.01, name + " must be cut through rear enclosure"
    assert air.Shape.common(boundary.Shape).Area > vent_area - 0.1, name + " must open to air"

for heat_name in heat_loads:
    heat = doc.getObject(heat_name)
    bbox = heat.Shape.BoundBox
    assert bbox.XMin >= -head_width / 2.0 - 0.01 and bbox.XMax <= head_width / 2.0 + 0.01
    assert bbox.YMin >= -0.01 and bbox.YMax <= head_height + 0.01
    assert bbox.ZMin >= -0.01 and bbox.ZMax <= head_depth + 0.01
    for channel in vent_channels:
        assert heat.Shape.common(channel).Volume <= 0.01, heat_name + " intersects a rear vent channel"

pairwise_overlaps = [
    doc.getObject(left).Shape.common(doc.getObject(right).Shape).Volume
    for left, right in itertools.combinations(solid_names, 2)
]
assert max(pairwise_overlaps) <= 0.01, "physical solids overlap"

glass = doc.getObject("Cover_Glass").Shape.BoundBox
panel = doc.getObject("Heat_Panel_Backlight").Shape.BoundBox
mid = doc.getObject("Mid_Frame").Shape.BoundBox
assert (glass.XMin, glass.YMin, glass.ZMin) == (-371.0, 0.0, 0.0)
assert (glass.XLength, glass.YLength, glass.ZLength) == (742.0, 492.0, 3.0)
assert abs(panel.XMin + 354.2) < 1e-6 and abs(panel.YMin - 28.0) < 1e-6
assert (panel.XLength, panel.YLength, panel.ZLength) == (708.4, 398.5, 12.0)
assert (mid.XMin, mid.YMin, mid.ZMin) == (-368.5, 2.5, 15.0)
assert (mid.XLength, mid.YLength, mid.ZLength) == (737.0, 487.0, 2.0)

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

observed_heat = 0.0
for name, expected in heat_loads.items():
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
signature = "air_solids={{}};vents={{}};heat={{:.3f}};max_overlap={{:.6f}};bbox={{:.3f}},{{:.3f}},{{:.3f}},{{:.3f}},{{:.3f}},{{:.3f}}".format(
    len(air.Shape.Solids),
    ",".join("{{:.3f}}".format(doc.getObject(name).Shape.Area) for name in boundary_names),
    observed_heat,
    max(pairwise_overlaps),
    min(doc.getObject(name).Shape.BoundBox.XMin for name in solid_names),
    min(doc.getObject(name).Shape.BoundBox.YMin for name in solid_names),
    min(doc.getObject(name).Shape.BoundBox.ZMin for name in solid_names),
    max(doc.getObject(name).Shape.BoundBox.XMax for name in solid_names),
    max(doc.getObject(name).Shape.BoundBox.YMax for name in solid_names),
    max(doc.getObject(name).Shape.BoundBox.ZMax for name in solid_names),
)
print("HINOKI_THERMAL_REOPEN_OK")
print("HINOKI_THERMAL_SIGNATURE " + signature)
print(
    "HINOKI_THERMAL_AIR_SOLID_MAX name={{}} volume={{:.6f}}".format(
        max_air_solid_name, max_air_solid_overlap
    )
)
fingerprint_names = solid_names + ("Internal_Air_Volume",) + boundary_names
def shape_center_of_mass(shape):
    leaves = shape.Solids
    if leaves:
        total_volume = sum(leaf.Volume for leaf in leaves)
        return App.Vector(
            sum(leaf.CenterOfMass.x * leaf.Volume for leaf in leaves) / total_volume,
            sum(leaf.CenterOfMass.y * leaf.Volume for leaf in leaves) / total_volume,
            sum(leaf.CenterOfMass.z * leaf.Volume for leaf in leaves) / total_volume,
        )
    faces = shape.Faces
    total_area = sum(face.Area for face in faces)
    return App.Vector(
        sum(face.CenterOfMass.x * face.Area for face in faces) / total_area,
        sum(face.CenterOfMass.y * face.Area for face in faces) / total_area,
        sum(face.CenterOfMass.z * face.Area for face in faces) / total_area,
    )
for name in fingerprint_names:
    shape = doc.getObject(name).Shape
    bounds = shape.BoundBox
    centre = shape_center_of_mass(shape)
    fingerprint = (
        name,
        shape.ShapeType,
        len(shape.Solids),
        tuple(round(value, 6) for value in (
            bounds.XMin, bounds.YMin, bounds.ZMin,
            bounds.XMax, bounds.YMax, bounds.ZMax,
        )),
        round(shape.Volume, 6),
        tuple(round(value, 6) for value in (centre.x, centre.y, centre.z)),
        len(shape.Faces),
        len(shape.Edges),
        hashlib.sha256(shape.exportBrepToString().encode("utf-8")).hexdigest(),
    )
    print("HINOKI_THERMAL_FINGERPRINT " + repr(fingerprint))
print("HINOKI_THERMAL_FINGERPRINTS_OK")
'''.format(
        cad_file=cad_file.as_posix(),
        solid_names=p.SOLID_BODIES,
        loads=dict(p.HEAT_LOADS_W),
        boundary_names=p.BOUNDARY_FACES,
        head_width=p.HEAD["width"],
        head_height=p.HEAD["height"],
        head_depth=p.HEAD["depth"],
        rear_wall=p.REAR_WALL,
        vent_width=p.VENT["width"],
        vent_height=p.VENT["height"],
        vent_area=p.VENT["area"],
        materials=dict(p.MATERIAL_INTENT),
    )


def run_freecad_probe(cad_file, p):
    return subprocess.run(
        [str(FREECAD_CMD), "-c"],
        cwd=Path(tempfile.gettempdir()),
        input="exec({!r})\n".format(thermal_validation_probe(cad_file, p)),
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


def signature_from(result):
    for line in (result.stdout + result.stderr).splitlines():
        if line.startswith("HINOKI_THERMAL_SIGNATURE "):
            return line.partition(" ")[2]
    return ""


def fingerprints_from(result):
    fingerprints = {}
    for line in (result.stdout + result.stderr).splitlines():
        if line.startswith("HINOKI_THERMAL_FINGERPRINT "):
            fingerprint = ast.literal_eval(line.partition(" ")[2])
            fingerprints[fingerprint[0]] = fingerprint
    return fingerprints


def assert_matching_fingerprints(test_case, temporary, formal, expected_names):
    test_case.assertEqual(set(temporary), set(expected_names))
    test_case.assertEqual(set(formal), set(expected_names))
    for name in expected_names:
        test_case.assertEqual(
            temporary[name],
            formal[name],
            "formal/temp geometry fingerprint differs for " + name,
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

      reopen = run_freecad_probe(temporary_cad, p)
      self.assertEqual(reopen.returncode, 0, reopen.stdout + reopen.stderr)
      self.assertIn("HINOKI_THERMAL_REOPEN_OK", reopen.stdout + reopen.stderr)
      self.assertIn("HINOKI_THERMAL_FINGERPRINTS_OK", reopen.stdout + reopen.stderr)
      formal_reopen = run_freecad_probe(CAD_FILE, p)
      self.assertEqual(formal_reopen.returncode, 0, formal_reopen.stdout + formal_reopen.stderr)
      self.assertIn("HINOKI_THERMAL_FINGERPRINTS_OK", formal_reopen.stdout + formal_reopen.stderr)
      self.assertEqual(signature_from(reopen), signature_from(formal_reopen))
      expected_fingerprint_names = (
          p.SOLID_BODIES + p.FLUID_BODIES + p.BOUNDARY_FACES
      )
      assert_matching_fingerprints(
          self,
          fingerprints_from(reopen),
          fingerprints_from(formal_reopen),
          expected_fingerprint_names,
      )
      self.assertEqual(
          CAD_FILE.read_bytes(),
          original_cad_bytes,
          "temporary builder test must not alter the tracked formal FCStd",
      )

  def test_atomic_publish_closes_source_and_returns_output_path(self):
    """Atomic save must verify a separately reopened document and preserve old output on failure."""
    self.assertTrue(FREECAD_CMD.exists(), "FreeCAD command-line executable must exist")
    source = BUILD_SCRIPT.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as temp_dir:
      output_path = Path(temp_dir) / "atomic-output.FCStd"
      forced_failure_path = Path(temp_dir) / "existing-output.FCStd"
      launcher = r'''
from pathlib import Path
import FreeCAD as App

namespace = {{"__name__": "thermal_atomic_regression", "__file__": r"{script_path}"}}
exec(compile({source!r}, r"{script_path}", "exec"), namespace)
result = namespace["build_document"](Path(r"{output_path}"))
assert isinstance(result, Path), "builder must return its published path, not a closed document"
assert result == Path(r"{output_path}") and result.exists()
assert not any(name.startswith("Hinoki_Thermal_CHT_Model") for name in App.listDocuments()), "source document remained open"

forced_failure = Path(r"{forced_failure_path}")
original_bytes = b"existing formal output survives failed validation"
forced_failure.write_bytes(original_bytes)
bad = App.newDocument("AtomicFailure")
try:
    namespace["publish_atomically"](bad, forced_failure)
except RuntimeError:
    pass
else:
    raise AssertionError("invalid document must fail atomic validation")
assert forced_failure.read_bytes() == original_bytes
assert not list(forced_failure.parent.glob("." + forced_failure.stem + ".*.FCStd"))
print("HINOKI_ATOMIC_INDEPENDENT_REOPEN_OK")
'''.format(
          script_path=BUILD_SCRIPT.as_posix(),
          source=source,
          output_path=output_path.as_posix(),
          forced_failure_path=forced_failure_path.as_posix(),
      )
      result = subprocess.run(
          [str(FREECAD_CMD), "-c"],
          cwd=Path(tempfile.gettempdir()),
          input="exec({!r})\n".format(launcher),
          capture_output=True,
          text=True,
          check=False,
          timeout=120,
      )
      self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
      self.assertIn("HINOKI_ATOMIC_INDEPENDENT_REOPEN_OK", result.stdout + result.stderr)

  def test_aggregate_signature_cannot_detect_a_single_legal_body_move(self):
    """A product-wide summary may stay equal while one named body changes position."""
    def aggregate_signature(objects):
      boxes = [object_data["bbox"] for object_data in objects.values()]
      return (
          1,
          (6000.0, 6000.0),
          57.0,
          0.0,
          (
              min(box[0] for box in boxes), min(box[1] for box in boxes),
              min(box[2] for box in boxes), max(box[3] for box in boxes),
              max(box[4] for box in boxes), max(box[5] for box in boxes),
          ),
      )

    baseline = {
        "Cover_Glass": {"bbox": (-371.0, 0.0, 0.0, 371.0, 492.0, 3.0)},
        "Rear_Enclosure": {"bbox": (-371.0, 0.0, 17.0, 371.0, 492.0, 62.0)},
        "Heat_IO": {"bbox": (230.0, 50.0, 38.0, 275.0, 80.0, 43.0)},
    }
    moved = {
        **baseline,
        "Heat_IO": {"bbox": (260.0, 90.0, 38.0, 305.0, 120.0, 43.0)},
    }
    self.assertEqual(aggregate_signature(baseline), aggregate_signature(moved))
    self.assertNotEqual(baseline["Heat_IO"], moved["Heat_IO"])

  def test_verify_document_rejects_air_overlapping_a_named_solid(self):
    """Air filled back into a component void must fail the native builder gate."""
    source = BUILD_SCRIPT.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as temp_dir:
      launcher = r'''
from pathlib import Path

namespace = {{"__name__": "air_disjoint_regression", "__file__": r"{script_path}"}}
exec(compile({source!r}, r"{script_path}", "exec"), namespace)
namespace["publish_atomically"] = lambda doc, output_path: doc
doc = namespace["build_document"](Path(r"{temp_dir}") / "unused.FCStd")
air = doc.getObject("Internal_Air_Volume")
solid = doc.getObject("Heat_IO")
air.Shape = air.Shape.fuse(solid.Shape).removeSplitter()
doc.recompute()
try:
    namespace["verify_document"](doc)
except RuntimeError as error:
    assert "Internal air overlaps Heat_IO" in str(error)
    print("HINOKI_AIR_DISJOINT_REJECTION_OK")
else:
    print("HINOKI_AIR_DISJOINT_GATE_LEAKED")
'''.format(
          script_path=BUILD_SCRIPT.as_posix(),
          source=source,
          temp_dir=Path(temp_dir).as_posix(),
      )
      result = subprocess.run(
          [str(FREECAD_CMD), "-c"],
          cwd=Path(tempfile.gettempdir()),
          input="exec({!r})\n".format(launcher),
          capture_output=True,
          text=True,
          check=False,
          timeout=120,
      )
      self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
      self.assertIn("HINOKI_AIR_DISJOINT_REJECTION_OK", result.stdout + result.stderr)
