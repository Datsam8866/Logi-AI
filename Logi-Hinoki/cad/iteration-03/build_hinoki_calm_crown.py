"""Build the Hinoki Calm Crown Iteration 03 front architecture.

This is external concept-review geometry, not manufacturing geometry.
Coordinate system: X left/right, Y vertical, Z rearward.
"""

import os
import sys
from pathlib import Path

import FreeCAD as App
import Part


SCRIPT_PATH = Path(
    globals().get(
        "__file__",
        Path.cwd() / "cad" / "iteration-03" / "build_hinoki_calm_crown.py",
    )
)
if str(SCRIPT_PATH.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT_PATH.parent))

import hinoki_calm_crown_parameters as parameters


OUTPUT_PATH = Path(
    os.environ.get(
        "HINOKI_CALM_CROWN_OUTPUT_PATH",
        SCRIPT_PATH.with_name("Hinoki_CalmCrown_Concept.FCStd"),
    )
)

HEAD_WIDTH = parameters.HEAD["width"]
HEAD_HEIGHT = parameters.HEAD["height"]
HEAD_DEPTH = parameters.HEAD["depth"]
HEAD_RADIUS = parameters.HEAD["corner_radius"]
HEAD_BOTTOM_Y = parameters.HEAD_BOTTOM_Y
CROWN_HEIGHT = parameters.CROWN_HEIGHT

COLORS = {
    "glass": (0.055, 0.065, 0.075),
    "mask": (0.025, 0.028, 0.032),
    "crown": (0.205, 0.195, 0.185),
    "speaker": (0.135, 0.130, 0.125),
    "camera": (0.075, 0.078, 0.082),
    "lens": (0.025, 0.035, 0.045),
    "shutter": (0.225, 0.220, 0.210),
    "light": (0.850, 0.830, 0.720),
    "sensor": (0.080, 0.095, 0.100),
}


def rounded_prism_xy(width, height, depth, radius, origin):
    """Return a rounded-rectangle prism lying in XY and extruded along +Z."""
    if min(width, height, depth, radius) <= 0:
        raise ValueError("Rounded prism dimensions and radius must be positive")
    if 2 * radius > min(width, height):
        raise ValueError("Radius cannot exceed half of the smaller XY dimension")

    x, y, z = origin
    shape = None
    if width - 2 * radius > 1e-9:
        shape = Part.makeBox(
            width - 2 * radius,
            height,
            depth,
            App.Vector(x + radius, y, z),
        )
    if height - 2 * radius > 1e-9:
        core_v = Part.makeBox(
            width,
            height - 2 * radius,
            depth,
            App.Vector(x, y + radius, z),
        )
        shape = core_v if shape is None else shape.fuse(core_v)
    for cx in (x + radius, x + width - radius):
        for cy in (y + radius, y + height - radius):
            corner = Part.makeCylinder(radius, depth, App.Vector(cx, cy, z))
            shape = corner if shape is None else shape.fuse(corner)
    return shape.removeSplitter()


def add_feature(
    doc,
    group,
    name,
    label,
    shape,
    color,
    classification,
    requirement_ids,
    assumption_ids="",
):
    """Add one traceable physical concept part to a document group."""
    obj = doc.addObject("Part::Feature", name)
    obj.Label = label
    obj.Shape = shape
    if obj.ViewObject is not None:
        obj.ViewObject.ShapeColor = color
    obj.addProperty("App::PropertyString", "Classification", "Traceability")
    obj.Classification = classification
    obj.addProperty("App::PropertyString", "RequirementIDs", "Traceability")
    obj.RequirementIDs = requirement_ids
    obj.addProperty("App::PropertyString", "AssumptionIDs", "Traceability")
    obj.AssumptionIDs = assumption_ids
    group.addObject(obj)
    return obj


def add_group(doc, name, label):
    group = doc.addObject("App::DocumentObjectGroup", name)
    group.Label = label
    return group


def build_document():
    doc = App.newDocument("Hinoki_CalmCrown_Concept")

    visible = add_group(doc, "Visible_ID_Surfaces", "Visible ID Surfaces")
    add_group(doc, "Structure", "Structure")
    add_group(doc, "Internal_Space_Claims", "Internal Space Claims")
    add_group(doc, "Datums_and_Motion", "Datums and Motion")
    metadata_group = add_group(doc, "Review_Metadata", "Review Metadata")

    metadata = doc.addObject("App::FeaturePython", "Model_Parameters")
    metadata.Label = "Calm Crown Controlled Model Parameters"
    metadata.addProperty("App::PropertyString", "CoordinateSystem", "Datums")
    metadata.CoordinateSystem = "X left/right; Y vertical; Z rearward"
    metadata.addProperty("App::PropertyLength", "HeadBottomY", "Datums")
    metadata.HeadBottomY = HEAD_BOTTOM_Y
    metadata.addProperty("App::PropertyLength", "HeadWidth", "Head")
    metadata.HeadWidth = HEAD_WIDTH
    metadata.addProperty("App::PropertyLength", "HeadHeight", "Head")
    metadata.HeadHeight = HEAD_HEIGHT
    metadata.addProperty("App::PropertyLength", "HeadDepth", "Head")
    metadata.HeadDepth = HEAD_DEPTH
    metadata.addProperty("App::PropertyLength", "CrownHeight", "Head")
    metadata.CrownHeight = CROWN_HEIGHT
    metadata.addProperty("App::PropertyString", "Maturity", "Review")
    metadata.Maturity = "External concept-review geometry; not manufacturing geometry"
    metadata_group.addObject(metadata)

    head_x = -HEAD_WIDTH / 2.0
    crown_y = HEAD_BOTTOM_Y + HEAD_HEIGHT - CROWN_HEIGHT

    front_glass = add_feature(
        doc,
        visible,
        "Front_Glass",
        "Front Cover Glass — {} × {} mm".format(HEAD_WIDTH, HEAD_HEIGHT),
        rounded_prism_xy(
            HEAD_WIDTH,
            HEAD_HEIGHT,
            1.8,
            HEAD_RADIUS,
            (head_x, HEAD_BOTTOM_Y, 0.0),
        ),
        COLORS["glass"],
        "Proposed visible product part",
        "32-inch 4K capacitive-touch display; single soft-rectangle front",
        "A-041; A-042",
    )
    if front_glass.ViewObject is not None:
        front_glass.ViewObject.Transparency = 18

    mask_outer = rounded_prism_xy(722.0, 407.0, 0.45, 12.0, (-361.0, 122.0, 2.10))
    active_opening = rounded_prism_xy(
        parameters.ACTIVE_AREA["width"],
        parameters.ACTIVE_AREA["height"],
        0.45,
        8.0,
        (-354.2, 126.25, 2.10),
    )
    add_feature(
        doc,
        visible,
        "Display_Mask",
        "Printed Display Mask / Active-Area Boundary",
        mask_outer.cut(active_opening).removeSplitter(),
        COLORS["mask"],
        "Proposed visible product part",
        "Display mask, active-area boundary and controlled side/bottom bezel",
        "A-041; A-043",
    )

    add_feature(
        doc,
        visible,
        "Crown_Shell",
        "Balanced AV Crown Shell",
        rounded_prism_xy(728.0, 62.0, 3.0, 15.0, (-364.0, crown_y + 5.0, 4.60)),
        COLORS["crown"],
        "Proposed visible product part",
        "Integrated 72 mm upper AV/acoustic crown",
        "A-043",
    )

    add_feature(
        doc,
        visible,
        "Speaker_Insert_Left",
        "Left Acoustic Insert",
        rounded_prism_xy(170.0, 48.0, 0.45, 12.0, (-350.0, crown_y + 12.0, 3.80)),
        COLORS["speaker"],
        "Proposed visible product part",
        "Independent upper-left speaker zone",
        "A-017; A-043",
    )
    add_feature(
        doc,
        visible,
        "Speaker_Insert_Right",
        "Right Acoustic Insert",
        rounded_prism_xy(170.0, 48.0, 0.45, 12.0, (180.0, crown_y + 12.0, 3.80)),
        COLORS["speaker"],
        "Proposed visible product part",
        "Independent upper-right speaker zone",
        "A-017; A-043",
    )

    add_feature(
        doc,
        visible,
        "Camera_Pill",
        "Camera and Captive-Shutter Pill",
        rounded_prism_xy(120.0, 44.0, 0.55, 22.0, (-60.0, crown_y + 14.0, 3.05)),
        COLORS["camera"],
        "Proposed visible product part",
        "Centred 4K camera package and manual captive shutter",
        "A-016; A-043",
    )
    add_feature(
        doc,
        visible,
        "Camera_Lens_Window",
        "4K Camera Lens Window",
        rounded_prism_xy(22.0, 22.0, 0.28, 11.0, (-11.0, crown_y + 25.0, 2.62)),
        COLORS["lens"],
        "Proposed visible product part",
        "Top-centre 4K camera; 134–140 degree horizontal FOV",
        "A-016",
    )
    add_feature(
        doc,
        visible,
        "Shutter_Rail",
        "Captive Privacy-Shutter Rail",
        rounded_prism_xy(50.0, 6.0, 0.22, 3.0, (-25.0, crown_y + 52.0, 2.32)),
        COLORS["shutter"],
        "Proposed visible product part",
        "Manual captive privacy shutter with positive end positions",
        "A-016",
    )
    add_feature(
        doc,
        visible,
        "Shutter_Tab_Open",
        "Privacy-Shutter Tab — Open Position",
        rounded_prism_xy(16.0, 12.0, 0.20, 6.0, (18.0, crown_y + 49.0, 2.02)),
        COLORS["shutter"],
        "Proposed visible product part",
        "Visible open state for manual captive privacy shutter",
        "A-016",
    )

    for name, label, x in (
        ("Fill_Light_Left", "Left Front-Fill Light Window", -130.0),
        ("Fill_Light_Right", "Right Front-Fill Light Window", 82.0),
    ):
        add_feature(
            doc,
            visible,
            name,
            label,
            rounded_prism_xy(48.0, 10.0, 0.25, 5.0, (x, crown_y + 31.0, 2.70)),
            COLORS["light"],
            "Proposed visible product part",
            "Narrow front-fill light window",
            "A-018; A-043",
        )

    add_feature(
        doc,
        visible,
        "Radar_Window",
        "Radar Presence-Sensor Window",
        rounded_prism_xy(22.0, 10.0, 0.24, 5.0, (-166.0, crown_y + 31.0, 2.66)),
        COLORS["sensor"],
        "Proposed visible product part",
        "Front radar-presence sensing provision",
        "A-023; A-043",
    )
    add_feature(
        doc,
        visible,
        "ALS_Window",
        "Ambient-Light-Sensor Window",
        rounded_prism_xy(12.0, 10.0, 0.23, 5.0, (154.0, crown_y + 31.0, 2.64)),
        COLORS["sensor"],
        "Proposed visible product part",
        "Ambient-light-sensor provision",
        "A-007; A-043",
    )

    built_front_object_names = tuple(obj.Name for obj in visible.Group)
    if built_front_object_names != parameters.FRONT_ARCHITECTURE_OBJECTS:
        raise RuntimeError(
            "Front architecture does not match controlled manifest: {}".format(
                ", ".join(parameters.FRONT_ARCHITECTURE_OBJECTS)
            )
        )

    doc.recompute()
    if OUTPUT_PATH.exists():
        OUTPUT_PATH.unlink()
    doc.saveAs(str(OUTPUT_PATH))
    return doc


if __name__ == "__main__":
    build_document()
    print("Hinoki Calm Crown front architecture generated: {}".format(OUTPUT_PATH))
