"""Build the native Hinoki FLOEFD conjugate heat-transfer handoff geometry.

Coordinate system: X left/right, Y bottom/top, Z front/rear.  This is a
thermal-analysis handoff model, not manufacturing geometry.
"""

import os
import sys
import uuid
from itertools import combinations
from pathlib import Path

import FreeCAD as App
import Part


SCRIPT_PATH = Path(
    globals().get("__file__", sys._getframe().f_code.co_filename)
).resolve()
if str(SCRIPT_PATH.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT_PATH.parent))

import hinoki_thermal_parameters as parameters


OUTPUT_PATH = Path(
    os.environ.get(
        "HINOKI_THERMAL_MODEL_PATH", SCRIPT_PATH.with_name(parameters.MODEL_FILE)
    )
)

HEAD_WIDTH = parameters.HEAD["width"]
HEAD_HEIGHT = parameters.HEAD["height"]
HEAD_DEPTH = parameters.HEAD["depth"]
ACTIVE_WIDTH = parameters.ACTIVE_AREA["width"]
ACTIVE_HEIGHT = parameters.ACTIVE_AREA["height"]
GLASS_THICKNESS = parameters.GLASS_THICKNESS
MIDFRAME_THICKNESS = parameters.MIDFRAME_THICKNESS
REAR_WALL = parameters.REAR_WALL
VENT_WIDTH = parameters.VENT["width"]
VENT_HEIGHT = parameters.VENT["height"]
VENT_AREA = parameters.VENT["area"]

PANEL_DEPTH = 12.0
PANEL_Y = 28.0
MIDFRAME_Y = REAR_WALL
MIDFRAME_Z = GLASS_THICKNESS + PANEL_DEPTH
REAR_START_Z = MIDFRAME_Z + MIDFRAME_THICKNESS
REAR_DEPTH = HEAD_DEPTH - REAR_START_Z
CAVITY_WIDTH = HEAD_WIDTH - 2.0 * REAR_WALL
CAVITY_HEIGHT = HEAD_HEIGHT - 2.0 * REAR_WALL
CAVITY_DEPTH = REAR_DEPTH - REAR_WALL
VENT_Z = HEAD_DEPTH - REAR_WALL
LOWER_VENT_Y = 20.0
UPPER_VENT_Y = HEAD_HEIGHT - LOWER_VENT_Y - VENT_HEIGHT
TOP_GROUPS = (
    "Thermal_Solids",
    "Heat_Sources",
    "Fluid_Regions",
    "Boundary_References",
    "Thermal_Metadata",
)


def box(length, width, height, origin):
    """Create an axis-aligned solid from its controlled X/Y/Z dimensions."""
    return Part.makeBox(length, width, height, App.Vector(*origin))


def add_group(doc, name):
    group = doc.addObject("App::DocumentObjectGroup", name)
    group.Label = name.replace("_", " ")
    return group


def add_physical_feature(doc, group, name, shape, classification="Solid"):
    """Add a traceable solid using the shared material and unit contract."""
    obj = doc.addObject("Part::Feature", name)
    obj.Label = name.replace("_", " ")
    obj.Shape = shape.removeSplitter() if shape.ShapeType != "Compound" else shape
    obj.addProperty("App::PropertyString", "Classification", "Thermal")
    obj.Classification = classification
    obj.addProperty("App::PropertyString", "MaterialIntent", "Thermal")
    obj.MaterialIntent = parameters.MATERIAL_INTENT[name]
    obj.addProperty("App::PropertyString", "Units", "Thermal")
    obj.Units = "mm"
    group.addObject(obj)
    return obj


def add_heat_feature(doc, group, name, shape):
    obj = add_physical_feature(doc, group, name, shape, "HeatSource")
    obj.addProperty("App::PropertyFloat", "HeatLoadW", "Thermal")
    obj.HeatLoadW = parameters.HEAT_LOADS_W[name]
    return obj


def add_boundary(doc, group, name, y_origin):
    obj = doc.addObject("Part::Feature", name)
    obj.Label = name.replace("_", " ")
    obj.Shape = Part.makePlane(
        VENT_WIDTH,
        VENT_HEIGHT,
        App.Vector(-VENT_WIDTH / 2.0, y_origin, HEAD_DEPTH),
        App.Vector(0.0, 0.0, 1.0),
    )
    obj.addProperty("App::PropertyString", "Classification", "Thermal")
    obj.Classification = "ReferenceOnly"
    obj.addProperty("App::PropertyString", "ExportPolicy", "Thermal")
    obj.ExportPolicy = "ReferenceOnly"
    obj.addProperty("App::PropertyString", "Units", "Thermal")
    obj.Units = "mm"
    group.addObject(obj)
    return obj


def add_metadata(doc, group):
    metadata = doc.addObject("App::FeaturePython", "Thermal_Model_Metadata")
    metadata.Label = "Hinoki Thermal CHT Metadata"
    metadata.addProperty("App::PropertyString", "CoordinateSystem", "Thermal")
    metadata.CoordinateSystem = "X left/right; Y bottom/top; Z front/rear"
    metadata.addProperty("App::PropertyFloat", "AmbientC", "Thermal")
    metadata.AmbientC = parameters.AMBIENT_C
    metadata.addProperty("App::PropertyVector", "GravityMmS2", "Thermal")
    metadata.GravityMmS2 = App.Vector(*parameters.GRAVITY_MM_S2)
    metadata.addProperty("App::PropertyFloat", "TotalHeatW", "Thermal")
    metadata.TotalHeatW = sum(parameters.HEAT_LOADS_W.values())
    metadata.addProperty("App::PropertyString", "CoolingMode", "Thermal")
    metadata.CoolingMode = parameters.COOLING_MODE
    metadata.addProperty("App::PropertyString", "Units", "Thermal")
    metadata.Units = "mm, W, C"
    group.addObject(metadata)
    return metadata


def verify_document(doc):
    required = TOP_GROUPS + (
        *parameters.SOLID_BODIES,
        *parameters.FLUID_BODIES,
        *parameters.BOUNDARY_FACES,
        "Thermal_Model_Metadata",
    )
    missing = [name for name in required if doc.getObject(name) is None]
    if missing:
        raise RuntimeError("Thermal CHT document missing: " + ", ".join(missing))
    group_names = tuple(
        obj.Name for obj in doc.Objects if obj.TypeId == "App::DocumentObjectGroup"
    )
    if group_names != TOP_GROUPS:
        raise RuntimeError("Thermal CHT top groups do not match controlled contract")
    heat_names = tuple(parameters.HEAT_LOADS_W)
    expected_groups = {
        "Thermal_Solids": set(parameters.SOLID_BODIES) - set(heat_names),
        "Heat_Sources": set(heat_names),
        "Fluid_Regions": set(parameters.FLUID_BODIES),
        "Boundary_References": set(parameters.BOUNDARY_FACES),
        "Thermal_Metadata": {"Thermal_Model_Metadata"},
    }
    for group_name, expected_names in expected_groups.items():
        actual_names = {obj.Name for obj in doc.getObject(group_name).Group}
        if actual_names != expected_names:
            raise RuntimeError(group_name + " membership does not match controlled manifest")
    for name in parameters.SOLID_BODIES + parameters.FLUID_BODIES:
        obj = doc.getObject(name)
        shape = obj.Shape
        if not shape.isValid() or shape.Volume <= 0.0:
            raise RuntimeError(name + " is not a valid positive-volume shape")
        if not shape.Solids or any(
            not leaf.isValid() or not leaf.isClosed() or leaf.Volume <= 0.0
            for leaf in shape.Solids
        ):
            raise RuntimeError(name + " does not contain valid closed leaf solids")
        if obj.MaterialIntent != parameters.MATERIAL_INTENT[name] or obj.Units != "mm":
            raise RuntimeError(name + " thermal material or units do not match parameters")
    if len(doc.getObject("Internal_Air_Volume").Shape.Solids) != 1:
        raise RuntimeError("Internal air must be a single connected solid")
    air = doc.getObject("Internal_Air_Volume").Shape
    rear = doc.getObject("Rear_Enclosure").Shape
    vent_channels = tuple(
        box(
            VENT_WIDTH,
            VENT_HEIGHT,
            REAR_WALL,
            (-VENT_WIDTH / 2.0, y_origin, VENT_Z),
        )
        for y_origin in (LOWER_VENT_Y, UPPER_VENT_Y)
    )
    for name in parameters.BOUNDARY_FACES:
        boundary = doc.getObject(name).Shape
        if (
            not boundary.isValid()
            or boundary.ShapeType != "Face"
            or abs(boundary.Area - VENT_AREA) > 0.1
            or boundary.normalAt(0.0, 0.0).z <= 0.999
            or abs(boundary.BoundBox.ZMin - HEAD_DEPTH) > 1e-6
            or rear.common(boundary).Area > 0.01
            or air.common(boundary).Area < VENT_AREA - 0.1
        ):
            raise RuntimeError(name + " is not a valid open rear boundary face")
    for name in heat_names:
        obj = doc.getObject(name)
        if "HeatLoadW" not in obj.PropertiesList or abs(
            obj.HeatLoadW - parameters.HEAT_LOADS_W[name]
        ) > 1e-6:
            raise RuntimeError(name + " heat load does not match parameters")
        bounds = obj.Shape.BoundBox
        if (
            bounds.XMin < -HEAD_WIDTH / 2.0 - 0.01
            or bounds.XMax > HEAD_WIDTH / 2.0 + 0.01
            or bounds.YMin < -0.01
            or bounds.YMax > HEAD_HEIGHT + 0.01
            or bounds.ZMin < -0.01
            or bounds.ZMax > HEAD_DEPTH + 0.01
            or any(obj.Shape.common(channel).Volume > 0.01 for channel in vent_channels)
        ):
            raise RuntimeError(name + " violates head containment or vent clearance")
    for first, second in combinations(parameters.SOLID_BODIES, 2):
        if doc.getObject(first).Shape.common(doc.getObject(second).Shape).Volume > 0.01:
            raise RuntimeError(first + " overlaps " + second)
    metadata = doc.getObject("Thermal_Model_Metadata")
    if (
        abs(metadata.AmbientC - parameters.AMBIENT_C) > 1e-6
        or tuple(metadata.GravityMmS2) != parameters.GRAVITY_MM_S2
        or abs(metadata.TotalHeatW - sum(parameters.HEAT_LOADS_W.values())) > 1e-6
        or metadata.CoolingMode != parameters.COOLING_MODE
    ):
        raise RuntimeError("Thermal metadata does not match controlled parameters")


def publish_atomically(doc, output_path):
    """Save/reopen a same-directory temporary FCStd before atomically publishing."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_name(
        ".{}.{}.FCStd".format(output_path.stem, uuid.uuid4().hex)
    )
    source_name = doc.Name
    reopened = None
    try:
        doc.saveAs(str(temporary_path))
        App.closeDocument(source_name)
        reopened = App.openDocument(str(temporary_path))
        try:
            verify_document(reopened)
        finally:
            App.closeDocument(reopened.Name)
            reopened = None
        os.replace(str(temporary_path), str(output_path))
        return output_path
    finally:
        if reopened is not None and reopened.Name in App.listDocuments():
            App.closeDocument(reopened.Name)
        if source_name in App.listDocuments():
            App.closeDocument(source_name)
        if temporary_path.exists():
            temporary_path.unlink()


def build_document(output_path=OUTPUT_PATH):
    doc = App.newDocument("Hinoki_Thermal_CHT_Model")
    thermal_solids = add_group(doc, "Thermal_Solids")
    heat_sources = add_group(doc, "Heat_Sources")
    fluid_regions = add_group(doc, "Fluid_Regions")
    boundary_references = add_group(doc, "Boundary_References")
    thermal_metadata = add_group(doc, "Thermal_Metadata")

    physical = {}
    physical["Cover_Glass"] = add_physical_feature(
        doc,
        thermal_solids,
        "Cover_Glass",
        box(HEAD_WIDTH, HEAD_HEIGHT, GLASS_THICKNESS, (-HEAD_WIDTH / 2.0, 0.0, 0.0)),
    )
    physical["Heat_Panel_Backlight"] = add_heat_feature(
        doc,
        heat_sources,
        "Heat_Panel_Backlight",
        box(ACTIVE_WIDTH, ACTIVE_HEIGHT, PANEL_DEPTH, (-ACTIVE_WIDTH / 2.0, PANEL_Y, GLASS_THICKNESS)),
    )
    physical["Mid_Frame"] = add_physical_feature(
        doc,
        thermal_solids,
        "Mid_Frame",
        box(CAVITY_WIDTH, CAVITY_HEIGHT, MIDFRAME_THICKNESS, (-CAVITY_WIDTH / 2.0, MIDFRAME_Y, MIDFRAME_Z)),
    )

    rear_outer = box(HEAD_WIDTH, HEAD_HEIGHT, REAR_DEPTH, (-HEAD_WIDTH / 2.0, 0.0, REAR_START_Z))
    rear_cavity = box(CAVITY_WIDTH, CAVITY_HEIGHT, CAVITY_DEPTH, (-CAVITY_WIDTH / 2.0, MIDFRAME_Y, REAR_START_Z))
    lower_vent = box(VENT_WIDTH, VENT_HEIGHT, REAR_WALL, (-VENT_WIDTH / 2.0, 20.0, VENT_Z))
    upper_vent = box(VENT_WIDTH, VENT_HEIGHT, REAR_WALL, (-VENT_WIDTH / 2.0, UPPER_VENT_Y, VENT_Z))
    physical["Rear_Enclosure"] = add_physical_feature(
        doc,
        thermal_solids,
        "Rear_Enclosure",
        rear_outer.cut(rear_cavity).cut(lower_vent).cut(upper_vent).removeSplitter(),
    )

    physical["Heat_Spreader"] = add_physical_feature(
        doc,
        thermal_solids,
        "Heat_Spreader",
        box(160.0, 100.0, 3.0, (-80.0, HEAD_HEIGHT / 2.0 - 50.0, REAR_START_Z)),
    )
    physical["TIM_QC7790"] = add_physical_feature(
        doc,
        thermal_solids,
        "TIM_QC7790",
        box(40.0, 40.0, 1.0, (-20.0, HEAD_HEIGHT / 2.0 - 20.0, 20.0)),
    )
    physical["Heat_QC7790"] = add_heat_feature(
        doc,
        heat_sources,
        "Heat_QC7790",
        box(40.0, 40.0, 2.0, (-20.0, HEAD_HEIGHT / 2.0 - 20.0, 21.0)),
    )
    physical["Heat_Memory"] = add_heat_feature(
        doc,
        heat_sources,
        "Heat_Memory",
        box(30.0, 30.0, 2.0, (-55.0, HEAD_HEIGHT / 2.0 - 15.0, 21.0)),
    )
    physical["Heat_Carrier_PMIC"] = add_heat_feature(
        doc,
        heat_sources,
        "Heat_Carrier_PMIC",
        box(30.0, 30.0, 2.0, (25.0, HEAD_HEIGHT / 2.0 - 15.0, 21.0)),
    )
    physical["Carrier_PCB"] = add_physical_feature(
        doc,
        thermal_solids,
        "Carrier_PCB",
        box(200.0, 120.0, 2.0, (-100.0, HEAD_HEIGHT / 2.0 - 60.0, 23.0)),
    )

    physical["Heat_IO"] = add_heat_feature(
        doc, heat_sources, "Heat_IO", box(45.0, 30.0, 5.0, (230.0, 50.0, 38.0))
    )
    physical["Heat_WiFi_BLE"] = add_heat_feature(
        doc, heat_sources, "Heat_WiFi_BLE", box(35.0, 30.0, 5.0, (-320.0, 410.0, 35.0))
    )
    physical["Heat_Camera"] = add_heat_feature(
        doc, heat_sources, "Heat_Camera", box(60.0, 25.0, 8.0, (-30.0, 430.0, 35.0))
    )
    physical["Heat_Audio"] = add_heat_feature(
        doc,
        heat_sources,
        "Heat_Audio",
        Part.makeCompound((
            box(50.0, 30.0, 10.0, (-270.0, 390.0, 38.0)),
            box(50.0, 30.0, 10.0, (220.0, 390.0, 38.0)),
        )),
    )
    physical["Heat_Radar_ALS"] = add_heat_feature(
        doc, heat_sources, "Heat_Radar_ALS", box(24.0, 20.0, 6.0, (-12.0, 458.0, 36.0))
    )
    physical["Heat_Front_Lighting"] = add_heat_feature(
        doc,
        heat_sources,
        "Heat_Front_Lighting",
        Part.makeCompound((
            box(45.0, 20.0, 5.0, (-145.0, 440.0, 28.0)),
            box(45.0, 20.0, 5.0, (100.0, 440.0, 28.0)),
        )),
    )

    air_shape = rear_cavity.fuse(lower_vent).fuse(upper_vent).removeSplitter()
    for obj in physical.values():
        if air_shape.common(obj.Shape).Volume > 1e-7:
            air_shape = air_shape.cut(obj.Shape).removeSplitter()
    air = doc.addObject("Part::Feature", "Internal_Air_Volume")
    air.Label = "Internal Air Volume"
    air.Shape = air_shape.removeSplitter()
    air.addProperty("App::PropertyString", "Classification", "Thermal")
    air.Classification = "FluidRegion"
    air.addProperty("App::PropertyString", "MaterialIntent", "Thermal")
    air.MaterialIntent = parameters.MATERIAL_INTENT["Internal_Air_Volume"]
    air.addProperty("App::PropertyString", "Units", "Thermal")
    air.Units = "mm"
    fluid_regions.addObject(air)

    add_boundary(doc, boundary_references, "Inlet_Opening_Lower_Rear", LOWER_VENT_Y)
    add_boundary(doc, boundary_references, "Outlet_Opening_Upper_Rear", UPPER_VENT_Y)
    add_metadata(doc, thermal_metadata)
    doc.recompute()
    verify_document(doc)
    return publish_atomically(doc, Path(output_path))


if __name__ == "__main__":
    build_document()
    print("HINOKI_THERMAL_BUILD_OK {}".format(OUTPUT_PATH))
