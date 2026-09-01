"""Build the Hinoki Iteration 02 preliminary review CAD.

The model combines source-backed market envelopes with explicitly marked
assumptions. It is a review baseline, not release geometry or a STEP source.
Coordinate system: X left/right, Y front/rear (rear positive), Z upward.
"""

from pathlib import Path

import FreeCAD as App
import Part


SCRIPT_PATH = Path(
    globals().get(
        "__file__",
        Path.cwd() / "cad" / "iteration-02" / "build_hinoki_iteration02.py",
    )
)
OUTPUT_PATH = SCRIPT_PATH.with_name("Hinoki_Concept_CAD_Iteration02_Review.FCStd")

COLORS = {
    "envelope": (0.72, 0.75, 0.78),
    "verified_display": (0.06, 0.18, 0.28),
    "verified_camera": (0.08, 0.08, 0.08),
    "assumption": (0.95, 0.65, 0.12),
    "interface": (0.28, 0.48, 0.78),
    "benchmark": (0.26, 0.58, 0.42),
    "base": (0.14, 0.16, 0.18),
    "motion_low": (0.25, 0.70, 0.95),
    "motion_high": (0.90, 0.40, 0.25),
}

OWT_SOURCE = "https://oneworldtouch.com/wp-content/mediafiles/2025/02/LM-3237-26B-4K-Data-Sheet.pdf"
LEOPARD_SOURCE = "https://leopardimaging.com/wp-content/uploads/2024/04/LI-IMX477-MIPI-140H_Datasheet.pdf"
ERGOTRON_SOURCE = "https://www.ergotron.com/en-ca/products/product-details/45-475"


def add_traceability(
    obj,
    classification,
    requirement,
    source_part_number="",
    source_url="",
    assumption_id="",
):
    obj.addProperty("App::PropertyString", "Classification", "Traceability")
    obj.Classification = classification
    obj.addProperty("App::PropertyString", "Requirement", "Traceability")
    obj.Requirement = requirement
    obj.addProperty("App::PropertyString", "SourcePartNumber", "Traceability")
    obj.SourcePartNumber = source_part_number
    obj.addProperty("App::PropertyString", "SourceURL", "Traceability")
    obj.SourceURL = source_url
    obj.addProperty("App::PropertyString", "AssumptionID", "Traceability")
    obj.AssumptionID = assumption_id


def add_group(doc, name, label, parent=None):
    group = doc.addObject("App::DocumentObjectGroup", name)
    group.Label = label
    if parent:
        parent.addObject(group)
    return group


def add_box(
    doc,
    group,
    name,
    label,
    origin,
    size,
    color,
    classification,
    requirement,
    source_part_number="",
    source_url="",
    assumption_id="",
    transparency=0,
):
    obj = doc.addObject("Part::Feature", name)
    obj.Label = label
    obj.Shape = Part.makeBox(
        size[0],
        size[1],
        size[2],
        App.Vector(origin[0], origin[1], origin[2]),
    )
    if obj.ViewObject is not None:
        obj.ViewObject.ShapeColor = color
        obj.ViewObject.Transparency = transparency
    add_traceability(
        obj,
        classification,
        requirement,
        source_part_number,
        source_url,
        assumption_id,
    )
    group.addObject(obj)
    return obj


def add_rotated_head_envelope(doc, group, name, label, pivot_z, tilt_deg, color):
    shape = Part.makeBox(760, 80, 540, App.Vector(-380, -40, pivot_z - 270))
    shape.rotate(App.Vector(0, 0, pivot_z), App.Vector(1, 0, 0), tilt_deg)
    obj = doc.addObject("Part::Feature", name)
    obj.Label = label
    obj.Shape = shape
    if obj.ViewObject is not None:
        obj.ViewObject.ShapeColor = color
        obj.ViewObject.Transparency = 86
    add_traceability(
        obj,
        "Assumed",
        "Height / tilt motion envelope carried from Iteration 01",
        assumption_id="A-035; A-036",
    )
    group.addObject(obj)
    return obj


def add_camera_fov(doc, group):
    fov = doc.addObject("Part::Feature", "Camera_FOV_KeepOut")
    fov.Label = "LI-IMX477 140° HFOV review keep-out"
    fov.Shape = Part.makeCone(
        4,
        275,
        110,
        App.Vector(0, -40, 650),
        App.Vector(0, -1, 0),
    )
    if fov.ViewObject is not None:
        fov.ViewObject.ShapeColor = COLORS["motion_low"]
        fov.ViewObject.Transparency = 90
    fov.addProperty("App::PropertyAngle", "HorizontalFOV", "Camera")
    fov.HorizontalFOV = 140.0
    fov.addProperty("App::PropertyString", "ClearanceStatus", "Camera")
    fov.ClearanceStatus = "Envelope review only — lens ray clearance remains open"
    add_traceability(
        fov,
        "Verified FOV value; conceptual keep-out",
        "134–140° camera horizontal FOV",
        "LI-IMX477-MIPI-140H",
        LEOPARD_SOURCE,
    )
    group.addObject(fov)
    return fov


def add_vesa_interface(doc, group):
    plate = add_box(
        doc,
        group,
        "VESA_200x200_Interface",
        "Review VESA Interface — 200 × 200 mm",
        (-115, 28, 271.35),
        (230, 12, 230),
        COLORS["interface"],
        "Verified display and stand interface benchmark",
        "Match LM-3237 proxy and Ergotron HX 200 × 200 mm interface",
        "LM-3237-26B-4K / 45-475-224",
        OWT_SOURCE + " | " + ERGOTRON_SOURCE,
        transparency=38,
    )
    plate.addProperty("App::PropertyLength", "PatternSize", "VESA")
    plate.PatternSize = 200.0
    plate.addProperty("App::PropertyString", "FastenerStatus", "VESA")
    plate.FastenerStatus = "Review pattern only — fastener stack and thread engagement open"
    return plate


def build_document():
    doc = App.newDocument("Hinoki_Concept_CAD_Iteration02_Review")

    metadata = doc.addObject("App::FeaturePython", "Iteration02_Metadata")
    metadata.Label = "Iteration 02 Preliminary Review Metadata"
    metadata.addProperty("App::PropertyString", "Status", "Iteration")
    metadata.Status = "Preliminary CAD review baseline — no release geometry or STEP export"
    metadata.addProperty("App::PropertyString", "Scope", "Iteration")
    metadata.Scope = "Panel/touch proxy, camera module, shutter assumption and stand/VESA benchmark"
    metadata.addProperty("App::PropertyString", "SourceAccessDate", "Iteration")
    metadata.SourceAccessDate = "2026-09-01"

    parameters = doc.addObject("App::FeaturePython", "Review_Parameters")
    parameters.Label = "Iteration 02 Review Parameters — verified and assumed"
    parameter_values = [
        ("HeadWidth", "App::PropertyLength", 760.0),
        ("HeadDepth", "App::PropertyLength", 80.0),
        ("HeadHeight", "App::PropertyLength", 540.0),
        ("DisplayWidth", "App::PropertyLength", 750.4),
        ("DisplayDepth", "App::PropertyLength", 56.5),
        ("DisplayHeight", "App::PropertyLength", 452.7),
        ("DisplayProxyMass", "App::PropertyMass", 14.0),
        ("CameraWidth", "App::PropertyLength", 38.0),
        ("CameraDepth", "App::PropertyLength", 25.78),
        ("CameraHeight", "App::PropertyLength", 38.0),
        ("CameraHFOV", "App::PropertyAngle", 140.0),
        ("VESAPattern", "App::PropertyLength", 200.0),
        ("StandCapacityMax", "App::PropertyMass", 19.1),
        ("StandLift", "App::PropertyLength", 292.0),
        ("PivotLow", "App::PropertyLength", 370.0),
        ("PivotNeutral", "App::PropertyLength", 430.0),
        ("PivotHigh", "App::PropertyLength", 490.0),
        ("TiltForward", "App::PropertyAngle", -5.0),
        ("TiltRearward", "App::PropertyAngle", 20.0),
    ]
    for name, property_type, value in parameter_values:
        parameters.addProperty(property_type, name, "Iteration 02 Review")
        setattr(parameters, name, value)
    add_traceability(
        parameters,
        "Mixed verified and assumed controls",
        "Central review parameter table; inspect each object traceability before use",
        "LM-3237-26B-4K / LI-IMX477-MIPI-140H / 45-475-224",
        OWT_SOURCE + " | " + LEOPARD_SOURCE + " | " + ERGOTRON_SOURCE,
        "A-013; A-016; A-035; A-036; A-039",
    )

    neutral = add_group(doc, "Neutral_Review_Assembly", "Neutral Review Assembly — 430 mm / 0°")
    motion = add_group(doc, "Motion_Envelopes", "Motion Envelopes — carried assumptions")
    head = add_group(doc, "Head_Review_Architecture", "Head Review Architecture", neutral)
    av = add_group(doc, "Upper_AV_Review_Architecture", "Upper AV Review Architecture", neutral)
    stand = add_group(doc, "Stand_Review_Architecture", "Stand / VESA Review Architecture", neutral)

    add_box(
        doc,
        head,
        "Head_Envelope",
        "Head Concept Envelope — 760 × 80 × 540 mm",
        (-380, -40, 160),
        (760, 80, 540),
        COLORS["envelope"],
        "Assumed",
        "Iteration 01 head envelope retained for market-component fit review",
        assumption_id="A-013",
        transparency=88,
    )
    add_box(
        doc,
        head,
        "OWT_LM3237_Display_Proxy",
        "One World Touch LM-3237 — verified external review proxy",
        (-375.2, -40, 160),
        (750.4, 56.5, 452.7),
        COLORS["verified_display"],
        "Verified review proxy",
        "32-inch 4K PCAP external envelope; not a bare panel module",
        "LM-3237-26B-4K",
        OWT_SOURCE,
    )
    add_box(
        doc,
        av,
        "Upper_AV_Reserve",
        "Upper AV Reserve — 760 × 80 × 87.3 mm",
        (-380, -40, 612.7),
        (760, 80, 87.3),
        COLORS["assumption"],
        "Assumed",
        "Residual upper zone for camera, shutter, audio and sensing",
        assumption_id="A-015; A-017; A-026",
        transparency=78,
    )
    camera = add_box(
        doc,
        av,
        "LI_IMX477_140H_Camera",
        "Leopard Imaging LI-IMX477-MIPI-140H",
        (-19, -40, 631),
        (38, 25.78, 38),
        COLORS["verified_camera"],
        "Verified component envelope",
        "12.3 MP camera module; 140° horizontal FOV; MIPI CSI-2",
        "LI-IMX477-MIPI-140H",
        LEOPARD_SOURCE,
    )
    camera.addProperty("App::PropertyAngle", "HorizontalFOV", "Camera")
    camera.HorizontalFOV = 140.0
    camera.addProperty("App::PropertyString", "ISPStatus", "Camera")
    camera.ISPStatus = "No ISP included — integration open"
    add_box(
        doc,
        av,
        "Privacy_Shutter_Assumption",
        "Manual Captive Privacy Shutter — assumption package",
        (-26, -40, 635),
        (52, 4, 30),
        COLORS["assumption"],
        "Assumed",
        "Manual shutter travel, retention and optical obscuration",
        assumption_id="A-016",
        transparency=18,
    )
    add_camera_fov(doc, motion)
    add_vesa_interface(doc, stand)

    add_box(
        doc,
        stand,
        "Desktop_Base_Assumption",
        "Hinoki Desktop Base — retained assumption",
        (-250, -140, 0),
        (500, 340, 90),
        COLORS["base"],
        "Assumed",
        "Integrated base, ballast, power and cable storage",
        assumption_id="A-039",
        transparency=28,
    )
    benchmark = add_box(
        doc,
        stand,
        "Ergotron_HX_Mechanism_Benchmark",
        "Ergotron HX mechanism benchmark — not vendor industrial design",
        (-22, 0, 90),
        (44, 44, 292),
        COLORS["benchmark"],
        "Verified mechanism benchmark",
        "19.1 kg maximum capacity, 292 mm lift, −5°/+70° tilt class",
        "45-475-224",
        ERGOTRON_SOURCE,
        transparency=44,
    )
    benchmark.addProperty("App::PropertyMass", "CapacityMin", "Mechanism")
    benchmark.CapacityMin = 9.1
    benchmark.addProperty("App::PropertyMass", "CapacityMax", "Mechanism")
    benchmark.CapacityMax = 19.1
    benchmark.addProperty("App::PropertyLength", "PublishedLift", "Mechanism")
    benchmark.PublishedLift = 292.0
    benchmark.addProperty("App::PropertyString", "GeometryStatus", "Mechanism")
    benchmark.GeometryStatus = "Simplified benchmark envelope; official arm geometry not reproduced"

    add_rotated_head_envelope(
        doc,
        motion,
        "Low_Forward_Envelope",
        "Low / Forward Review Envelope — 370 mm / −5°",
        370,
        -5,
        COLORS["motion_low"],
    )
    add_rotated_head_envelope(
        doc,
        motion,
        "High_Rearward_Envelope",
        "High / Rearward Review Envelope — 490 mm / +20°",
        490,
        20,
        COLORS["motion_high"],
    )

    doc.recompute()
    try:
        import FreeCADGui as Gui

        Gui.activeDocument().activeView().viewAxonometric()
        Gui.activeDocument().activeView().fitAll()
    except Exception:
        pass
    doc.recompute()
    if OUTPUT_PATH.exists():
        OUTPUT_PATH.unlink()
    doc.saveAs(str(OUTPUT_PATH))
    return doc


if __name__ == "__main__":
    build_document()
    print("Hinoki Iteration 02 preliminary review CAD generated: {}".format(OUTPUT_PATH))
