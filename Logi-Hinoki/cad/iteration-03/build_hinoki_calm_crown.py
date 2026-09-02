"""Build the Hinoki Calm Crown Iteration 03 front architecture.

This is external concept-review geometry, not manufacturing geometry.
Coordinate system: X left/right, Y vertical, Z rearward.
"""

import os
import sys
import zipfile
from html import escape
from pathlib import Path

import FreeCAD as App
import Part


# `freecadcmd -c` does not set __file__, but compile() retains the absolute script
# filename supplied by the caller.
SCRIPT_PATH = Path(
    globals().get("__file__", sys._getframe().f_code.co_filename)
).resolve()
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
    "rear": (0.160, 0.155, 0.148),
    "service": (0.120, 0.118, 0.112),
    "vent": (0.065, 0.070, 0.068),
    "io": (0.045, 0.050, 0.055),
    "claim": (0.300, 0.550, 0.700),
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
    obj.addProperty("App::PropertyString", "ExportPolicy", "Traceability")
    obj.ExportPolicy = "ProductGeometry"
    obj.addProperty("App::PropertyString", "Source", "Traceability")
    obj.Source = "Calm Crown Iteration 03 controlled concept"
    obj.addProperty("App::PropertyString", "ReviewStatus", "Traceability")
    obj.ReviewStatus = "Concept-review geometry"
    group.addObject(obj)
    return obj


def add_group(doc, name, label):
    group = doc.addObject("App::DocumentObjectGroup", name)
    group.Label = label
    return group


def add_reference_claim(
    doc,
    group,
    name,
    label,
    shape,
    requirement_ids,
    assumption_ids,
):
    """Add a transparent, non-exported internal allocation volume."""
    claim = add_feature(
        doc,
        group,
        name,
        label,
        shape,
        COLORS["claim"],
        "Reference-only internal space claim",
        requirement_ids,
        assumption_ids,
    )
    claim.ExportPolicy = "ReferenceOnly"
    claim.Source = "Calm Crown Iteration 03 internal architecture allocation"
    claim.ReviewStatus = "Assumed reference space; not manufacturing geometry"
    # FreeCADCmd has no GUI view provider. Persist the native visibility state;
    # persist_gui_view_state() writes the GUI transparency counterpart.
    claim.Visibility = False
    if claim.ViewObject is not None:
        claim.ViewObject.Transparency = 82
        claim.ViewObject.Visibility = False
    return claim


def persist_gui_view_state(doc, output_path):
    """Add the GUI view-provider states omitted by FreeCADCmd saves.

    FreeCADCmd writes Document.xml only. The GUI restores visual properties from
    GuiDocument.xml, so this formal FCStd entry keeps reference claims hidden and
    transparent when the native file is subsequently opened in FreeCAD GUI.
    """
    claim_names = set(parameters.REQUIRED_INTERNAL_CLAIMS)
    providers = []
    for obj in doc.Objects:
        hidden = obj.Name in claim_names
        properties = [
            '<Property name="Visibility" type="App::PropertyBool">'
            '<Bool value="{}"/></Property>'.format(str(not hidden).lower())
        ]
        if hidden:
            properties.insert(
                0,
                '<Property name="Transparency" type="App::PropertyInteger">'
                '<Integer value="82"/></Property>',
            )
        providers.append(
            '<ViewProvider name="{}" expanded="0" treeRank="0">'
            '<Properties Count="{}">{}</Properties></ViewProvider>'.format(
                escape(obj.Name), len(properties), "".join(properties)
            )
        )
    gui_document = (
        "<?xml version='1.0' encoding='utf-8'?>"
        "<Document SchemaVersion=\"1\"><ViewProviderData Count=\"{}\">{}"
        "</ViewProviderData><Camera settings=\"\"/></Document>"
    ).format(len(providers), "".join(providers))

    temporary_path = output_path.with_suffix(output_path.suffix + ".gui.tmp")
    with zipfile.ZipFile(output_path, "r") as source, zipfile.ZipFile(
        temporary_path, "w", zipfile.ZIP_DEFLATED
    ) as target:
        for entry in source.infolist():
            if entry.filename != "GuiDocument.xml":
                target.writestr(entry, source.read(entry.filename))
        target.writestr("GuiDocument.xml", gui_document.encode("utf-8"))
    os.replace(str(temporary_path), str(output_path))


def build_document():
    doc = App.newDocument("Hinoki_CalmCrown_Concept")

    visible = add_group(doc, "Visible_ID_Surfaces", "Visible ID Surfaces")
    structure = add_group(doc, "Structure", "Structure")
    internal_claims = add_group(doc, "Internal_Space_Claims", "Internal Space Claims")
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
        (-parameters.ACTIVE_AREA["width"] / 2.0, 126.25, 2.10),
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
        "Integrated {} mm upper AV/acoustic crown".format(CROWN_HEIGHT),
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

    # Rear pillow: shallow perimeter plus a fuller central service island.
    rear_perimeter = rounded_prism_xy(
        HEAD_WIDTH, HEAD_HEIGHT, 42.0, HEAD_RADIUS, (head_x, HEAD_BOTTOM_Y, 9.0)
    )
    rear_island_raw = rounded_prism_xy(
        460.0, 330.0, 8.0, 42.0, (-230.0, 196.0, 54.0)
    )
    rear_island_top_edges = [
        edge
        for edge in rear_island_raw.Edges
        if abs(edge.BoundBox.ZMin - HEAD_DEPTH) < 1e-6
        and abs(edge.BoundBox.ZMax - HEAD_DEPTH) < 1e-6
    ]
    rear_island = rear_island_raw.makeFillet(5.0, rear_island_top_edges)
    service_well = rounded_prism_xy(
        276.0, 236.0, 8.0, 16.0, (-138.0, 243.0, 55.0)
    )
    vent_well = rounded_prism_xy(
        486.0, 38.0, 7.0, 12.0, (-243.0, 128.0, 45.0)
    )
    io_well = rounded_prism_xy(
        142.0, 70.0, 9.0, 10.0, (96.0, 180.0, 54.0)
    )
    cable_well = rounded_prism_xy(
        68.0, 30.0, 7.0, 10.0, (-34.0, 155.0, 45.0)
    )
    rear_shell_shape = (
        rear_perimeter.fuse(rear_island)
        .cut(service_well)
        .cut(vent_well)
        .cut(io_well)
        .cut(cable_well)
        .removeSplitter()
    )
    add_feature(
        doc,
        structure,
        "Rear_Shell",
        "Rounded Rear Pillow Shell — shallow perimeter / full centre",
        rear_shell_shape,
        COLORS["rear"],
        "Proposed visible product part",
        "Rear pillow enclosure with stepped central service island",
        "A-043; A-045",
    )

    add_feature(
        doc,
        structure,
        "Rear_Service_Cover",
        "Rear Service Cover — 260 × 220 mm",
        rounded_prism_xy(260.0, 220.0, 3.0, 12.0, (-130.0, 251.0, 58.0)),
        COLORS["service"],
        "Proposed visible product part",
        "Central rear service access cover; 260 × 220 mm controlled envelope",
        "A-045",
    )
    add_feature(
        doc,
        structure,
        "Vent_Insert_Lower",
        "Lower Rear Vent Insert",
        rounded_prism_xy(470.0, 26.0, 3.0, 10.0, (-235.0, 134.0, 47.0)),
        COLORS["vent"],
        "Proposed visible product part",
        "Lower rear thermal exhaust/intake insert",
        "A-021; A-045",
    )
    add_feature(
        doc,
        structure,
        "IO_Recess",
        "Recessed Rear I/O Bay",
        rounded_prism_xy(126.0, 54.0, 3.0, 8.0, (104.0, 188.0, 56.0)),
        COLORS["io"],
        "Proposed visible product part",
        "Recessed rear service I/O bay",
        "A-045; A-046",
    )
    add_feature(
        doc,
        structure,
        "Cable_Exit_Feature",
        "Rear Cable Exit Feature",
        rounded_prism_xy(52.0, 20.0, 3.0, 8.0, (-26.0, 160.0, 47.0)),
        COLORS["io"],
        "Proposed service feature",
        "Cable exit provision below rear service island",
        "A-045; A-046",
    )

    add_reference_claim(
        doc, internal_claims, "Panel_Touch_Claim", "Panel / Touch Reference Space",
        rounded_prism_xy(708.4, 398.5, 8.0, 8.0, (-354.2, 126.25, 12.0)),
        "32-inch 4K touch display allocation", "A-041; A-042",
    )
    for name, x in (("Speaker_Claim_Left", -350.0), ("Speaker_Claim_Right", 180.0)):
        add_reference_claim(
            doc, internal_claims, name, name.replace("_", " "),
            rounded_prism_xy(170.0, 48.0, 16.0, 12.0, (x, crown_y + 12.0, 14.0)),
            "Upper speaker volume allocation", "A-017; A-043",
        )
    add_reference_claim(
        doc, internal_claims, "Camera_ISP_Claim", "Camera / ISP Reference Space",
        rounded_prism_xy(120.0, 44.0, 16.0, 16.0, (-60.0, crown_y + 14.0, 14.0)),
        "Top-centre camera and ISP allocation", "A-016; A-043",
    )
    add_reference_claim(
        doc, internal_claims, "QC7790_Claim", "QC7790 Compute Reference Space",
        rounded_prism_xy(150.0, 100.0, 20.0, 12.0, (-75.0, 300.0, 28.0)),
        "Qualcomm QC7790 compute allocation", "A-044",
    )
    add_reference_claim(
        doc, internal_claims, "Heat_Spreader_Claim", "Heat Spreader Reference Space",
        rounded_prism_xy(300.0, 150.0, 5.0, 12.0, (-150.0, 275.0, 49.0)),
        "Thermal spreader allocation behind display", "A-021; A-044",
    )
    add_reference_claim(
        doc, internal_claims, "USB_C_Interface_Claim", "USB-C Interface Reference Space",
        rounded_prism_xy(24.0, 14.0, 10.0, 4.0, (148.0, 208.0, 52.0)),
        "USB-C service interface allocation", "A-046",
    )
    add_reference_claim(
        doc, internal_claims, "Rear_IO_Board_Claim", "Rear I/O Board Reference Space",
        rounded_prism_xy(120.0, 54.0, 8.0, 8.0, (107.0, 188.0, 50.0)),
        "Rear I/O board allocation behind recessed bay", "A-045; A-046",
    )
    vesa_claim = add_reference_claim(
        doc, internal_claims, "VESA_Reinforcement_Claim", "VESA Reinforcement — 100 mm Pattern",
        rounded_prism_xy(140.0, 140.0, 6.0, 12.0, (-70.0, 291.0, 52.0)),
        "100 mm VESA reinforcement allocation", "A-045",
    )
    vesa_claim.addProperty("App::PropertyLength", "VESAPattern", "Traceability")
    vesa_claim.VESAPattern = parameters.VESA_PATTERN
    add_reference_claim(
        doc, internal_claims, "Base_Power_PD_Claim", "Base Power / PD Reference Space",
        rounded_prism_xy(360.0, 240.0, 45.0, 16.0, (-180.0, -285.0, 0.0)),
        "Base power and PD allocation only; no Task 3 base solid", "A-047",
    )
    add_reference_claim(
        doc, internal_claims, "Ballast_Claim", "Ballast Reference Space",
        rounded_prism_xy(380.0, 250.0, 8.0, 16.0, (-190.0, -290.0, 48.0)),
        "Base ballast allocation only; no Task 3 base solid", "A-047",
    )
    cable_loop_outer = rounded_prism_xy(92.0, 52.0, 5.0, 20.0, (-46.0, 175.0, 48.0))
    cable_loop_inner = rounded_prism_xy(72.0, 32.0, 7.0, 12.0, (-36.0, 185.0, 47.0))
    add_reference_claim(
        doc, internal_claims, "Cable_Loop_Claim", "Cable Loop Reference Space",
        cable_loop_outer.cut(cable_loop_inner).removeSplitter(),
        "Service cable loop and bend-space allocation", "A-045; A-046",
    )

    doc.recompute()
    if OUTPUT_PATH.exists():
        OUTPUT_PATH.unlink()
    doc.saveAs(str(OUTPUT_PATH))
    persist_gui_view_state(doc, OUTPUT_PATH)
    return doc


if __name__ == "__main__":
    build_document()
    print("Hinoki Calm Crown architecture generated: {}".format(OUTPUT_PATH))
