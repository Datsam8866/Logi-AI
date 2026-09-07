"""Contract checks for the approved Hinoki FLOEFD thermal CHT case."""

from importlib.util import module_from_spec, spec_from_file_location
import ast
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PARAMETERS_FILE = PROJECT_ROOT / "cad" / "thermal-simulation-01" / "hinoki_thermal_parameters.py"
BUILD_SCRIPT = PROJECT_ROOT / "cad" / "thermal-simulation-01" / "build_hinoki_thermal_cht.py"
REVIEW_SCRIPT = PROJECT_ROOT / "cad" / "thermal-simulation-01" / "review_hinoki_thermal_cht.py"
EXPORT_SCRIPT = PROJECT_ROOT / "cad" / "thermal-simulation-01" / "export_hinoki_thermal_cht.py"
CAD_FILE = PROJECT_ROOT / "cad" / "thermal-simulation-01" / "Hinoki_Thermal_CHT_Model.FCStd"
SOLIDS_STEP_FILE = PROJECT_ROOT / "cad" / "thermal-simulation-01" / "Hinoki_Thermal_CHT_Solids.step"
AIR_STEP_FILE = PROJECT_ROOT / "cad" / "thermal-simulation-01" / "Hinoki_Thermal_Internal_Air.step"
SETUP_FILE = PROJECT_ROOT / "cad" / "thermal-simulation-01" / "Hinoki_Thermal_FLOEFD_Setup.json"
REVIEW_FILE = PROJECT_ROOT / "cad" / "thermal-simulation-01" / "Hinoki_Thermal_CHT_Review.json"
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


def run_freecad_review(script_path, env):
    """Run the review source through FreeCAD from a non-project cwd."""
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


def run_freecad_export(script_path, env):
    """Run the exporter source through FreeCAD from a non-project cwd."""
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


def step_reimport_probe(solids_path, air_path, p):
    """Return a native STEP re-import check for the approved mm-scale handoff."""
    return r'''
import FreeCAD as App
import Import

def positive_features(document):
    return [
        obj for obj in document.Objects
        if hasattr(obj, "Shape") and obj.Shape.isValid() and obj.Shape.Volume > 0.0
    ]

def semantic_body_features(document):
    features = positive_features(document)
    containers = [obj for obj in features if len(obj.Shape.Solids) > 1]
    top_container = max(containers, key=lambda obj: obj.Shape.Volume, default=None)
    body_containers = [obj for obj in containers if obj is not top_container]
    def is_container_child(obj):
        return any(
            obj is not container
            and abs(container.Shape.common(obj.Shape).Volume - obj.Shape.Volume) <= 0.01
            for container in body_containers
        )
    return [
        obj for obj in features
        if obj is not top_container and not is_container_child(obj)
    ]

solids = App.newDocument("StepSolidsProbe")
Import.insert(r"{solids_path}", solids.Name)
solid_features = semantic_body_features(solids)
assert len(solid_features) == {solid_count}, "solid STEP feature count: " + repr([
    obj.Name for obj in solid_features
])
solid_box = solid_features[0].Shape.BoundBox
for obj in solid_features[1:]:
    solid_box.add(obj.Shape.BoundBox)
assert 741.9 <= solid_box.XLength <= 742.1
assert 491.9 <= solid_box.YLength <= 492.1
assert 61.9 <= solid_box.ZLength <= 62.1
assert not any("Opening" in obj.Name for obj in solids.Objects)
App.closeDocument(solids.Name)

air = App.newDocument("StepAirProbe")
Import.insert(r"{air_path}", air.Name)
air_features = positive_features(air)
assert len(air_features) == 1, "air STEP feature count: " + repr([
    obj.Name for obj in air_features
])
air_box = air_features[0].Shape.BoundBox
assert air_box.XLength > 700.0 and air_box.YLength > 450.0 and air_box.ZLength > 40.0
assert air_box.XLength < 1000.0 and air_box.YLength < 1000.0 and air_box.ZLength < 100.0
App.closeDocument(air.Name)
assert not App.listDocuments()
print("HINOKI_THERMAL_STEP_REIMPORT_OK solids={{}} air={{}}".format(
    len(solid_features), len(air_features)
))
'''.format(
        solids_path=solids_path.as_posix(),
        air_path=air_path.as_posix(),
        solid_count=len(p.SOLID_BODIES),
    )


def run_step_reimport_probe(solids_path, air_path, p):
    return subprocess.run(
        [str(FREECAD_CMD), "-c"],
        cwd=Path(tempfile.gettempdir()),
        input="exec({!r})\n".format(step_reimport_probe(solids_path, air_path, p)),
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


def geometry_equivalence_probe(formal_path, temporary_path, names):
    return r'''
import FreeCAD as App

formal = App.open(r"{formal_path}")
formal_shapes = {{name: formal.getObject(name).Shape.copy() for name in {names!r}}}
App.closeDocument(formal.Name)
temporary = App.open(r"{temporary_path}")
errors = []
for name in {names!r}:
    first = formal_shapes[name]
    second = temporary.getObject(name).Shape.copy()
    if not first.isValid() or not second.isValid():
        errors.append(name + " has an invalid shape")
        continue
    if first.Solids or second.Solids:
        symmetric_difference = first.cut(second).Volume + second.cut(first).Volume
        common_volume = first.common(second).Volume
        if (
            symmetric_difference > 0.01
            or abs(common_volume - first.Volume) > 0.01
            or abs(common_volume - second.Volume) > 0.01
        ):
            errors.append(
                "{{}} volumetric symdiff={{:.6f}} common={{:.6f}} volumes={{:.6f}},{{:.6f}}".format(
                    name, symmetric_difference, common_volume, first.Volume, second.Volume
                )
            )
    else:
        symmetric_difference = first.cut(second).Area + second.cut(first).Area
        common_area = first.common(second).Area
        if (
            symmetric_difference > 0.01
            or abs(common_area - first.Area) > 0.01
            or abs(common_area - second.Area) > 0.01
        ):
            errors.append(
                "{{}} face symdiff={{:.6f}} common={{:.6f}} areas={{:.6f}},{{:.6f}}".format(
                    name, symmetric_difference, common_area, first.Area, second.Area
                )
            )
    print("HINOKI_THERMAL_GEOMETRY_EQUIVALENT " + name)
if errors:
    print("HINOKI_THERMAL_GEOMETRY_EQUIVALENCE_FAILED " + " | ".join(errors))
else:
    print("HINOKI_THERMAL_GEOMETRY_EQUIVALENCE_OK")
'''.format(
        formal_path=formal_path.as_posix(),
        temporary_path=temporary_path.as_posix(),
        names=tuple(names),
    )


def run_geometry_equivalence_probe(formal_path, temporary_path, names):
    return subprocess.run(
        [str(FREECAD_CMD), "-c"],
        cwd=Path(tempfile.gettempdir()),
        input="exec({!r})\n".format(
            geometry_equivalence_probe(formal_path, temporary_path, names)
        ),
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


def create_geometry_pair(formal_path, temporary_path, temporary_shape):
    """Create two native FCStds with one named shape for equivalence regressions."""
    launcher = r'''
import FreeCAD as App
import Part

def save_document(path, shape):
    doc = App.newDocument("GeometryPair")
    obj = doc.addObject("Part::Feature", "ProbeShape")
    obj.Shape = shape
    doc.recompute()
    doc.saveAs(r"{{}}".format(path))
    App.closeDocument(doc.Name)

box = Part.makeBox(10.0, 20.0, 30.0)
save_document(r"{formal_path}", box)
{temporary_shape}
save_document(r"{temporary_path}", alternate)
formal_hash = box.exportBrepToString()
alternate_hash = alternate.exportBrepToString()
formal_bbox = box.BoundBox
alternate_bbox = alternate.BoundBox
formal_numeric = tuple(round(value, 3) for value in (
    formal_bbox.XMin, formal_bbox.YMin, formal_bbox.ZMin,
    formal_bbox.XMax, formal_bbox.YMax, formal_bbox.ZMax, box.Volume,
))
alternate_numeric = tuple(round(value, 3) for value in (
    alternate_bbox.XMin, alternate_bbox.YMin, alternate_bbox.ZMin,
    alternate_bbox.XMax, alternate_bbox.YMax, alternate_bbox.ZMax, alternate.Volume,
))
print("HINOKI_GEOMETRY_PAIR numeric_equal={{}} hash_equal={{}}".format(
    formal_numeric == alternate_numeric, formal_hash == alternate_hash
))
'''.format(
        formal_path=formal_path.as_posix(),
        temporary_path=temporary_path.as_posix(),
        temporary_shape=temporary_shape,
    )
    return subprocess.run(
        [str(FREECAD_CMD), "-c"],
        cwd=Path(tempfile.gettempdir()),
        input="exec({!r})\n".format(launcher),
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


def assert_matching_fingerprints(
    test_case, temporary, formal, expected_names, temporary_path, formal_path
):
    test_case.assertEqual(set(temporary), set(expected_names))
    test_case.assertEqual(set(formal), set(expected_names))
    result = run_geometry_equivalence_probe(
        formal_path, temporary_path, expected_names
    )
    combined = result.stdout + result.stderr
    test_case.assertEqual(result.returncode, 0, combined)
    test_case.assertIn("HINOKI_THERMAL_GEOMETRY_EQUIVALENCE_OK", combined)


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
          temporary_cad,
          CAD_FILE,
      )
      self.assertEqual(
          CAD_FILE.read_bytes(),
          original_cad_bytes,
          "temporary builder test must not alter the tracked formal FCStd",
      )

  def test_pre_publish_verification_failure_closes_documents_and_preserves_output(self):
    """A failed builder verification must not leak a document or touch prior output."""
    source = BUILD_SCRIPT.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as temp_dir:
      output_path = Path(temp_dir) / "existing.FCStd"
      launcher = r'''
from pathlib import Path
import FreeCAD as App

namespace = {{"__name__": "pre_publish_failure_regression", "__file__": r"{script_path}"}}
exec(compile({source!r}, r"{script_path}", "exec"), namespace)
output = Path(r"{output_path}")
original = b"pre-publish output must survive"
output.write_bytes(original)
def fail_verify(doc):
    raise RuntimeError("forced pre-publish verification failure")
namespace["verify_document"] = fail_verify
try:
    namespace["build_document"](output)
except RuntimeError as error:
    assert "forced pre-publish verification failure" in str(error)
else:
    raise AssertionError("forced verification failure must propagate")
assert output.read_bytes() == original
assert not App.listDocuments()
assert not list(output.parent.glob("." + output.stem + ".*.FCStd"))
print("HINOKI_PRE_PUBLISH_FAILURE_CLEANUP_OK")
'''.format(
          script_path=BUILD_SCRIPT.as_posix(),
          source=source,
          output_path=output_path.as_posix(),
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
      self.assertIn(
          "HINOKI_PRE_PUBLISH_FAILURE_CLEANUP_OK", result.stdout + result.stderr
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

  def test_geometry_equivalence_accepts_hash_mismatched_equivalent_boxes(self):
    """A polygon-face extrusion matching a box must pass the boolean fallback."""
    with tempfile.TemporaryDirectory() as temp_dir:
      formal_path = Path(temp_dir) / "box.FCStd"
      temporary_path = Path(temp_dir) / "polygon.FCStd"
      polygon_box = """
wire = Part.makePolygon((
    App.Vector(0.0, 0.0, 0.0), App.Vector(10.0, 0.0, 0.0),
    App.Vector(10.0, 20.0, 0.0), App.Vector(0.0, 20.0, 0.0),
    App.Vector(0.0, 0.0, 0.0),
))
alternate = Part.Face(wire).extrude(App.Vector(0.0, 0.0, 30.0))
"""
      created = create_geometry_pair(formal_path, temporary_path, polygon_box)
      self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
      self.assertIn(
          "HINOKI_GEOMETRY_PAIR numeric_equal=True hash_equal=False",
          created.stdout + created.stderr,
      )
      equivalent = run_geometry_equivalence_probe(
          formal_path, temporary_path, ("ProbeShape",)
      )
      self.assertEqual(equivalent.returncode, 0, equivalent.stdout + equivalent.stderr)
      self.assertIn(
          "HINOKI_THERMAL_GEOMETRY_EQUIVALENCE_OK",
          equivalent.stdout + equivalent.stderr,
      )

  def test_geometry_equivalence_rejects_nearly_summarized_but_shifted_box(self):
    """Boolean comparison must reject a real shift even if coarse numeric fields match."""
    with tempfile.TemporaryDirectory() as temp_dir:
      formal_path = Path(temp_dir) / "box.FCStd"
      temporary_path = Path(temp_dir) / "shifted.FCStd"
      shifted_box = "alternate = Part.makeBox(10.0, 20.0, 30.0, App.Vector(0.00001, 0.0, 0.0))"
      created = create_geometry_pair(formal_path, temporary_path, shifted_box)
      self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
      self.assertIn(
          "HINOKI_GEOMETRY_PAIR numeric_equal=True hash_equal=False",
          created.stdout + created.stderr,
      )
      rejected = run_geometry_equivalence_probe(
          formal_path, temporary_path, ("ProbeShape",)
      )
      combined = rejected.stdout + rejected.stderr
      self.assertEqual(rejected.returncode, 0, combined)
      self.assertIn(
          "HINOKI_THERMAL_GEOMETRY_EQUIVALENCE_FAILED ProbeShape volumetric",
          combined,
      )
      self.assertNotIn("HINOKI_THERMAL_GEOMETRY_EQUIVALENCE_OK", combined)

  def test_geometry_equivalence_accepts_microshift_within_tolerance(self):
    """A symmetric difference below 0.01 mm³ is accepted by the minimum gate."""
    with tempfile.TemporaryDirectory() as temp_dir:
      formal_path = Path(temp_dir) / "box.FCStd"
      temporary_path = Path(temp_dir) / "microshift.FCStd"
      created = create_geometry_pair(
          formal_path,
          temporary_path,
          "alternate = Part.makeBox(10.0, 20.0, 30.0, App.Vector(0.000001, 0.0, 0.0))",
      )
      self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
      equivalent = run_geometry_equivalence_probe(
          formal_path, temporary_path, ("ProbeShape",)
      )
      self.assertEqual(equivalent.returncode, 0, equivalent.stdout + equivalent.stderr)
      self.assertIn(
          "HINOKI_THERMAL_GEOMETRY_EQUIVALENCE_OK",
          equivalent.stdout + equivalent.stderr,
      )

  def test_verify_document_rejects_air_overlapping_a_named_solid(self):
    """Air filled back into a component void must fail the native builder gate."""
    source = BUILD_SCRIPT.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as temp_dir:
      launcher = r'''
from pathlib import Path

namespace = {{"__name__": "air_disjoint_regression", "__file__": r"{script_path}"}}
exec(compile({source!r}, r"{script_path}", "exec"), namespace)
namespace["publish_atomically"] = lambda doc, output_path: doc
doc = namespace["_build_document"](Path(r"{temp_dir}") / "unused.FCStd")
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

  def test_review_and_setup_evidence_are_generated_in_temporary_outputs(self):
    """Review generation records all minimum FLOEFD gates without formal writes."""
    self.assertTrue(REVIEW_SCRIPT.exists(), "thermal review script must exist")
    self.assertTrue(CAD_FILE.exists(), "formal thermal model must exist")
    p = load_parameters()
    original_cad_bytes = CAD_FILE.read_bytes()

    with tempfile.TemporaryDirectory() as temp_dir:
      temp_root = Path(temp_dir)
      temporary_cad = temp_root / p.MODEL_FILE
      temporary_setup = temp_root / p.SETUP_JSON
      temporary_review = temp_root / p.REVIEW_JSON

      builder_env = os.environ.copy()
      builder_env["HINOKI_THERMAL_MODEL_PATH"] = str(temporary_cad)
      built = run_freecad_builder(BUILD_SCRIPT, builder_env)
      self.assertEqual(built.returncode, 0, built.stdout + built.stderr)

      review_env = os.environ.copy()
      review_env["HINOKI_THERMAL_MODEL_PATH"] = str(temporary_cad)
      review_env["HINOKI_THERMAL_SETUP_PATH"] = str(temporary_setup)
      review_env["HINOKI_THERMAL_REVIEW_PATH"] = str(temporary_review)
      reviewed = run_freecad_review(REVIEW_SCRIPT, review_env)
      combined = reviewed.stdout + reviewed.stderr
      self.assertEqual(reviewed.returncode, 0, combined)
      self.assertIn("HINOKI_THERMAL_REVIEW_OK", combined)
      self.assertTrue(temporary_setup.exists())
      self.assertTrue(temporary_review.exists())

      setup = json.loads(temporary_setup.read_text(encoding="utf-8"))
      self.assertEqual(setup["solver"], "Simcenter FLOEFD")
      self.assertEqual(setup["analysis_type"], "ConjugateHeatTransfer")
      self.assertEqual(setup["units"], "mm, W, degC")
      self.assertEqual(setup["ambient_c"], 35.0)
      self.assertEqual(setup["cooling_mode"], "NaturalConvection")
      self.assertFalse(setup["fan_present"])
      self.assertEqual(setup["gravity_mm_s2"], [0.0, -9810.0, 0.0])
      self.assertEqual(setup["heat_loads_w"], dict(p.HEAT_LOADS_W))
      self.assertEqual(setup["material_intent"], dict(p.MATERIAL_INTENT))
      self.assertEqual(setup["external_domain"], "Create in FLOEFD")
      self.assertEqual(setup["assumption_status"], "Preliminary concept inputs")
      self.assertEqual(
          set(setup["vent_openings"]), set(p.BOUNDARY_FACES)
      )
      self.assertEqual(
          {item["area_mm2"] for item in setup["vent_openings"].values()},
          {6000.0},
      )

      review = json.loads(temporary_review.read_text(encoding="utf-8"))
      self.assertEqual(review["status"], "Pass")
      self.assertTrue(review["hard_gates"])
      self.assertTrue(all(review["hard_gates"].values()))
      self.assertEqual(review["unauthorized_overlaps"], [])
      self.assertEqual(review["total_heat_w"], 57.0)
      self.assertEqual(review["required_objects"], list(
          p.SOLID_BODIES + p.FLUID_BODIES + p.BOUNDARY_FACES
      ))

      self.assertEqual(CAD_FILE.read_bytes(), original_cad_bytes)

  def test_step_export_reimports_isolated_temporary_handoff_files(self):
    """The exporter must atomically create mm-scale STEP solids and connected air."""
    self.assertTrue(EXPORT_SCRIPT.exists(), "thermal STEP exporter must exist")
    self.assertTrue(CAD_FILE.exists(), "formal thermal model must exist")
    p = load_parameters()
    original_model_bytes = CAD_FILE.read_bytes()
    original_solids_bytes = (
        SOLIDS_STEP_FILE.read_bytes() if SOLIDS_STEP_FILE.exists() else None
    )
    original_air_bytes = AIR_STEP_FILE.read_bytes() if AIR_STEP_FILE.exists() else None

    with tempfile.TemporaryDirectory() as temp_dir:
      temp_root = Path(temp_dir)
      temporary_model = temp_root / p.MODEL_FILE
      temporary_solids = temp_root / p.SOLIDS_STEP
      temporary_air = temp_root / p.AIR_STEP
      builder_env = os.environ.copy()
      builder_env["HINOKI_THERMAL_MODEL_PATH"] = str(temporary_model)
      built = run_freecad_builder(BUILD_SCRIPT, builder_env)
      self.assertEqual(built.returncode, 0, built.stdout + built.stderr)

      export_env = os.environ.copy()
      export_env["HINOKI_THERMAL_MODEL_PATH"] = str(temporary_model)
      export_env["HINOKI_THERMAL_SOLIDS_STEP_PATH"] = str(temporary_solids)
      export_env["HINOKI_THERMAL_AIR_STEP_PATH"] = str(temporary_air)
      exported = run_freecad_export(EXPORT_SCRIPT, export_env)
      combined = exported.stdout + exported.stderr
      self.assertEqual(exported.returncode, 0, combined)
      self.assertIn("HINOKI_THERMAL_EXPORT_OK", combined)
      self.assertTrue(temporary_solids.exists())
      self.assertTrue(temporary_air.exists())
      self.assertGreater(temporary_solids.stat().st_size, 10_000)
      self.assertGreater(temporary_air.stat().st_size, 1_000)

      reimport = run_step_reimport_probe(temporary_solids, temporary_air, p)
      self.assertEqual(reimport.returncode, 0, reimport.stdout + reimport.stderr)
      self.assertIn(
          "HINOKI_THERMAL_STEP_REIMPORT_OK solids=16 air=1",
          reimport.stdout + reimport.stderr,
      )

    self.assertEqual(CAD_FILE.read_bytes(), original_model_bytes)
    self.assertEqual(
        SOLIDS_STEP_FILE.read_bytes() if SOLIDS_STEP_FILE.exists() else None,
        original_solids_bytes,
    )
    self.assertEqual(
        AIR_STEP_FILE.read_bytes() if AIR_STEP_FILE.exists() else None,
        original_air_bytes,
    )

  def test_step_export_validation_failure_preserves_old_outputs_and_cleans_temps(self):
    """A staged STEP validation failure cannot replace either existing handoff file."""
    source = EXPORT_SCRIPT.read_text(encoding="utf-8")
    p = load_parameters()
    with tempfile.TemporaryDirectory() as temp_dir:
      root = Path(temp_dir)
      temporary_model = root / p.MODEL_FILE
      built_env = os.environ.copy()
      built_env["HINOKI_THERMAL_MODEL_PATH"] = str(temporary_model)
      built = run_freecad_builder(BUILD_SCRIPT, built_env)
      self.assertEqual(built.returncode, 0, built.stdout + built.stderr)

      solids_path = root / p.SOLIDS_STEP
      air_path = root / p.AIR_STEP
      solids_path.write_bytes(b"old solids STEP survives")
      air_path.write_bytes(b"old air STEP survives")
      launcher = r'''
from pathlib import Path
import FreeCAD as App

namespace = {{"__name__": "step_failure_regression", "__file__": r"{script_path}"}}
exec(compile({source!r}, r"{script_path}", "exec"), namespace)
namespace["_validate_step_reimport"] = lambda *args: (_ for _ in ()).throw(
    RuntimeError("forced STEP validation failure")
)
try:
    namespace["export_handoff"](Path(r"{model_path}"))
except RuntimeError as error:
    assert "forced STEP validation failure" in str(error)
else:
    raise AssertionError("forced STEP validation failure must propagate")
assert Path(r"{solids_path}").read_bytes() == b"old solids STEP survives"
assert Path(r"{air_path}").read_bytes() == b"old air STEP survives"
assert not list(Path(r"{root}").glob(".*.step"))
assert not App.listDocuments()
print("HINOKI_STEP_EXPORT_FAILURE_CLEANUP_OK")
'''.format(
          script_path=EXPORT_SCRIPT.as_posix(),
          source=source,
          model_path=temporary_model.as_posix(),
          solids_path=solids_path.as_posix(),
          air_path=air_path.as_posix(),
          root=root.as_posix(),
      )
      export_env = os.environ.copy()
      export_env["HINOKI_THERMAL_MODEL_PATH"] = str(temporary_model)
      export_env["HINOKI_THERMAL_SOLIDS_STEP_PATH"] = str(solids_path)
      export_env["HINOKI_THERMAL_AIR_STEP_PATH"] = str(air_path)
      result = subprocess.run(
          [str(FREECAD_CMD), "-c"],
          cwd=Path(tempfile.gettempdir()),
          env=export_env,
          input="exec({!r})\n".format(launcher),
          capture_output=True,
          text=True,
          check=False,
          timeout=120,
      )
      self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
      self.assertIn(
          "HINOKI_STEP_EXPORT_FAILURE_CLEANUP_OK", result.stdout + result.stderr
      )

  def test_review_failure_signaling_never_emits_success_sentinel(self):
    """A failed review has a unique failure signal and no success signal."""
    self.assertTrue(REVIEW_SCRIPT.exists(), "thermal review script must exist")
    source = REVIEW_SCRIPT.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as temp_dir:
      setup_path = Path(temp_dir) / "setup.json"
      review_path = Path(temp_dir) / "review.json"
      launcher = r'''
namespace = {{"__name__": "review_failure_signal", "__file__": r"{script_path}"}}
exec(compile({source!r}, r"{script_path}", "exec"), namespace)
namespace["SETUP_PATH"] = __import__("pathlib").Path(r"{setup_path}")
namespace["REVIEW_PATH"] = __import__("pathlib").Path(r"{review_path}")
namespace["review_document"] = lambda model_path: {{
    "status": "Fail",
    "hard_gates": {{"forced_failure": False}},
    "unauthorized_overlaps": [],
}}
assert namespace["main"]() != 0
print("HINOKI_FAILURE_SIGNAL_TEST_DONE")
'''.format(
          script_path=REVIEW_SCRIPT.as_posix(),
          source=source,
          setup_path=setup_path.as_posix(),
          review_path=review_path.as_posix(),
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
      combined = result.stdout + result.stderr
      self.assertEqual(result.returncode, 0, combined)
      self.assertIn("HINOKI_THERMAL_REVIEW_FAIL", combined)
      self.assertNotIn("HINOKI_THERMAL_REVIEW_OK", combined)
      self.assertIn("HINOKI_FAILURE_SIGNAL_TEST_DONE", combined)

  def test_missing_or_broken_model_preserves_review_pair_and_cleans_temps(self):
    """Model-open failures must leave both formal evidence files byte-identical."""
    self.assertTrue(REVIEW_SCRIPT.exists(), "thermal review script must exist")
    for model_kind in ("missing", "broken"):
      with self.subTest(model_kind=model_kind), tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        model_path = temp_root / "model.FCStd"
        setup_path = SETUP_FILE
        review_path = REVIEW_FILE
        setup_original = setup_path.read_bytes()
        review_original = review_path.read_bytes()
        formal_temps_before = set(setup_path.parent.glob(".*.tmp"))
        if model_kind == "broken":
          model_path.write_bytes(b"not a FreeCAD document")

        review_env = os.environ.copy()
        review_env["HINOKI_THERMAL_MODEL_PATH"] = str(model_path)
        review_env["HINOKI_THERMAL_SETUP_PATH"] = str(setup_path)
        review_env["HINOKI_THERMAL_REVIEW_PATH"] = str(review_path)
        result = run_freecad_review(REVIEW_SCRIPT, review_env)
        combined = result.stdout + result.stderr
        self.assertIn("HINOKI_THERMAL_REVIEW_FAIL", combined)
        self.assertNotIn("HINOKI_THERMAL_REVIEW_OK", combined)
        self.assertEqual(setup_path.read_bytes(), setup_original)
        self.assertEqual(review_path.read_bytes(), review_original)
        self.assertEqual(set(setup_path.parent.glob(".*.tmp")), formal_temps_before)

  def test_json_temp_writer_cleans_partial_file_when_write_fails(self):
    """A writer exception after partial output must remove its temporary file."""
    self.assertTrue(REVIEW_SCRIPT.exists(), "thermal review script must exist")
    source = REVIEW_SCRIPT.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as temp_dir:
      launcher = r'''
from pathlib import Path

namespace = {{"__name__": "partial_json_temp_failure", "__file__": r"{script_path}"}}
exec(compile({source!r}, r"{script_path}", "exec"), namespace)
root = Path(r"{temp_dir}")
partial = root / ".review.json.partial.tmp"

class FailingTemporary:
    def write_text(self, content, encoding=None):
        partial.write_text("partial", encoding="utf-8")
        raise OSError("forced JSON writer failure")
    def exists(self):
        return partial.exists()
    def unlink(self):
        partial.unlink()

class FakeTarget:
    parent = root
    name = "review.json"
    def with_name(self, name):
        return FailingTemporary()

try:
    namespace["_write_json_temp"](FakeTarget(), {{"forced": True}})
except OSError as error:
    assert "forced JSON writer failure" in str(error)
else:
    raise AssertionError("writer failure must propagate")
assert not partial.exists()
print("HINOKI_PARTIAL_JSON_TEMP_CLEANUP_OK")
'''.format(
          script_path=REVIEW_SCRIPT.as_posix(),
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
      combined = result.stdout + result.stderr
      self.assertEqual(result.returncode, 0, combined)
      self.assertIn("HINOKI_PARTIAL_JSON_TEMP_CLEANUP_OK", combined)
