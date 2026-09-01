"""Build the Hinoki Concept CAD Iteration 01 space-claim assembly.

This is deliberately a concept CAD model. Values marked Assumed in the
parameter table remain editable controls, not release geometry.
Coordinate system: X left/right, Y front/rear (rear positive), Z upward.
"""

from pathlib import Path

import FreeCAD as App
import Part


SCRIPT_PATH = Path(globals().get("__file__", Path.cwd() / "cad" / "iteration-01" / "build_hinoki_iteration01.py"))
OUTPUT_PATH = SCRIPT_PATH.with_name("Hinoki_Concept_CAD_Iteration01.FCStd")

COLORS = {
    "envelope": (0.72, 0.75, 0.78),
    "display": (0.08, 0.12, 0.16),
    "av_bar": (0.16, 0.18, 0.20),
    "camera": (0.10, 0.10, 0.10),
    "speaker": (0.18, 0.20, 0.22),
    "light": (1.00, 0.82, 0.25),
    "sensor": (0.30, 0.80, 0.60),
    "compute": (0.75, 0.30, 0.18),
    "io": (0.20, 0.45, 0.82),
    "structure": (0.42, 0.45, 0.50),
    "base": (0.12, 0.14, 0.16),
    "power": (0.58, 0.22, 0.20),
    "motion_low": (0.25, 0.70, 0.95),
    "motion_high": (0.90, 0.40, 0.25),
}


def add_traceability(obj, assumption_id, requirement, classification="Assumed"):
    obj.addProperty("App::PropertyString", "AssumptionID", "Traceability")
    obj.AssumptionID = assumption_id
    obj.addProperty("App::PropertyString", "Requirement", "Traceability")
    obj.Requirement = requirement
    obj.addProperty("App::PropertyString", "Classification", "Traceability")
    obj.Classification = classification


def add_group(doc, name, label, parent=None):
    group = doc.addObject("App::DocumentObjectGroup", name)
    group.Label = label
    if parent:
        parent.addObject(group)
    return group


def add_box(doc, group, name, label, origin, size, color, assumption_id, requirement, transparency=0):
    obj = doc.addObject("Part::Feature", name)
    obj.Label = label
    obj.Shape = Part.makeBox(size[0], size[1], size[2], App.Vector(origin[0], origin[1], origin[2]))
    if obj.ViewObject is not None:
        obj.ViewObject.ShapeColor = color
        obj.ViewObject.Transparency = transparency
    add_traceability(obj, assumption_id, requirement)
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
        obj.ViewObject.Transparency = 82
    add_traceability(obj, "A-035; A-036", "Height / tilt motion envelope")
    group.addObject(obj)
    return obj


def add_fov_cone(doc, group):
    obj = doc.addObject("Part::Feature", "Camera_FOV_KeepOut")
    obj.Label = "Camera FOV Keep-out — 137° nominal horizontal concept"
    obj.Shape = Part.makeCone(4, 252, 100, App.Vector(0, -40, 657.5), App.Vector(0, -1, 0))
    if obj.ViewObject is not None:
        obj.ViewObject.ShapeColor = COLORS["motion_low"]
        obj.ViewObject.Transparency = 88
    obj.addProperty("App::PropertyAngle", "HorizontalFOV", "Camera")
    obj.HorizontalFOV = 137.0
    obj.addProperty("App::PropertyString", "ClearanceStatus", "Camera")
    obj.ClearanceStatus = "Concept pass — front hardware remains behind camera front datum"
    add_traceability(obj, "A-016", "134–140° camera FOV keep-out; nominal set to 137°")
    group.addObject(obj)
    return obj


def build_document():
    doc = App.newDocument("Hinoki_Concept_CAD_Iteration01")
    doc.addObject("App::FeaturePython", "Iteration_Metadata")
    metadata = doc.getObject("Iteration_Metadata")
    metadata.Label = "Iteration 01 Concept Metadata"
    metadata.addProperty("App::PropertyString", "Status", "Iteration")
    metadata.Status = "Concept CAD only — no release geometry or STEP export"
    metadata.addProperty("App::PropertyString", "Scope", "Iteration")
    metadata.Scope = "Neutral assembly plus low/forward and high/rearward motion envelopes"

    parameters = doc.addObject("App::FeaturePython", "Master_Parameters")
    parameters.Label = "Iteration 01 Master Parameters (Assumed unless stated)"
    parameter_values = [
        ("HeadWidth", "App::PropertyLength", 760.0),
        ("HeadHeight", "App::PropertyLength", 540.0),
        ("HeadDepth", "App::PropertyLength", 80.0),
        ("PivotLow", "App::PropertyLength", 370.0),
        ("PivotNeutral", "App::PropertyLength", 430.0),
        ("PivotHigh", "App::PropertyLength", 490.0),
        ("TiltForward", "App::PropertyAngle", -5.0),
        ("TiltRearward", "App::PropertyAngle", 20.0),
        ("BaseWidth", "App::PropertyLength", 500.0),
        ("BaseDepth", "App::PropertyLength", 340.0),
        ("BaseHeight", "App::PropertyLength", 90.0),
    ]
    for name, property_type, value in parameter_values:
        parameters.addProperty(property_type, name, "Iteration 01")
        setattr(parameters, name, value)
    add_traceability(parameters, "A-013 to A-040", "Controlled concept CAD parameters")

    neutral = add_group(doc, "Neutral_Assembly", "Neutral Assembly — 430 mm pivot / 0° tilt")
    motion = add_group(doc, "Motion_Envelopes", "Motion Envelopes — review geometry")
    head = add_group(doc, "Head_Architecture", "Head Architecture", neutral)
    av = add_group(doc, "Upper_AV_Architecture", "Upper AV / Acoustic Bar", neutral)
    rear = add_group(doc, "Rear_Equipment_Architecture", "Rear Compute / I-O / VESA", neutral)
    stand = add_group(doc, "Desktop_Stand_Architecture", "Desktop Stand / Base", neutral)

    add_box(doc, head, "Head_Envelope", "Head Concept Envelope — 760 × 80 × 540", (-380, -40, 160), (760, 80, 540), COLORS["envelope"], "A-013", "Overall 32-inch desktop head envelope", 86)
    add_box(doc, head, "Display_Touch_Stack", "32-inch Display + Capacitive Touch", (-365, -40, 195), (730, 18, 420), COLORS["display"], "A-014", "32-inch 4K capacitive-touch display")
    add_box(doc, head, "Lower_Port_Reach_Zone", "Lower User I/O Reach Zone", (245, -40, 170), (100, 30, 80), COLORS["io"], "A-031", "User-accessible USB-C BYOD and USB-A reach zone", 35)

    add_box(doc, av, "Upper_AV_Bar", "Upper AV / Acoustic Bar", (-380, -40, 615), (760, 80, 85), COLORS["av_bar"], "A-015", "Upper-mounted speakers, camera, lights and microphones", 38)
    add_box(doc, av, "Speaker_Left", "Upper Left Speaker Enclosure", (-350, -40, 630), (170, 40, 55), COLORS["speaker"], "A-017", "Integrated upper left speaker")
    add_box(doc, av, "Speaker_Right", "Upper Right Speaker Enclosure", (180, -40, 630), (170, 40, 55), COLORS["speaker"], "A-017", "Integrated upper right speaker")
    add_box(doc, av, "Camera_Manual_Shutter", "4K Camera + Manual Captive Shutter", (-60, -40, 630), (120, 42, 55), COLORS["camera"], "A-016", "Integrated 4K camera; 134–140° FOV; manual non-removable shutter")
    add_box(doc, av, "Privacy_Shutter_Closed", "Manual Shutter Closed Position", (-28, -43, 640), (56, 4, 28), COLORS["structure"], "A-016", "Manual captive shutter obscures camera optical opening")
    add_box(doc, av, "Front_Light_Left", "Front Light — Left", (-130, -40, 655), (55, 12, 15), COLORS["light"], "A-018", "Front lighting provision")
    add_box(doc, av, "Front_Light_Right", "Front Light — Right", (75, -40, 655), (55, 12, 15), COLORS["light"], "A-018", "Front lighting provision")
    add_box(doc, av, "Microphone_Left", "Microphone Aperture Zone — Left", (-270, -44, 642), (24, 8, 12), COLORS["sensor"], "A-026", "Integrated microphones")
    add_box(doc, av, "Microphone_Right", "Microphone Aperture Zone — Right", (246, -44, 642), (24, 8, 12), COLORS["sensor"], "A-026", "Integrated microphones")
    add_box(doc, av, "Radar_KeepOut", "Radar Presence Sensor Keep-out", (130, -40, 618), (40, 15, 20), COLORS["sensor"], "A-023", "Radar presence sensing")
    add_box(doc, av, "Ambient_Light_Provision", "Ambient-Light Sensor Provision", (145, -40, 660), (12, 10, 12), COLORS["sensor"], "A-007", "Conditional ambient-light sensor provision", 20)
    add_fov_cone(doc, motion)

    add_box(doc, rear, "Compute_Thermal_Module", "QC7790 SOM + Heat Spreader", (-100, -10, 355), (200, 32, 120), COLORS["compute"], "A-019", "QC7790 SOM; separated rear thermal zone")
    add_box(doc, rear, "USB_C_PD_Interface", "Head USB-C Interface / Protection", (245, 5, 175), (100, 24, 75), COLORS["io"], "A-020", "USB-C BYOD interface; bulk PD remains in base")
    add_box(doc, rear, "Rear_IO_Bay", "Rear HDMI / Ethernet / Audio / Service I-O", (-110, -10, 175), (220, 24, 60), COLORS["io"], "A-021", "HDMI input, Ethernet, 3.5 mm audio, USB service I/O")
    add_box(doc, rear, "VESA_Reinforcement", "VESA Reinforcement / Stand Interface", (-90, 22, 340), (180, 18, 180), COLORS["structure"], "A-010", "VESA and adjustable stand structural interface")
    add_box(doc, rear, "Rear_Vent_KeepOut", "Rear Compute Vent Keep-out", (-140, 30, 525), (280, 10, 60), COLORS["sensor"], "A-029", "Direct rear vent path for compute thermal zone", 55)

    add_box(doc, stand, "Desktop_Base", "Desktop Base — 500 × 340 × 90", (-250, -140, 0), (500, 340, 90), COLORS["base"], "A-039", "Desktop base; contains power, ballast and cable storage", 25)
    add_box(doc, stand, "ACDC_BulkPD_Ballast", "AC/DC + Bulk PD + Ballast Package", (-180, -100, 0), (360, 260, 90), COLORS["power"], "A-030; A-039", "Base power architecture and ballast", 52)
    add_box(doc, stand, "Height_Column", "Height-Adjustment Column Sweep", (-50, -40, 90), (100, 80, 400), COLORS["structure"], "A-035", "120 mm VESA pivot travel; 370–490 mm", 28)
    add_box(doc, stand, "VESA_Pivot_Carrier", "VESA Pivot Carrier", (-110, -40, 320), (220, 80, 220), COLORS["structure"], "A-035; A-036", "Tilt pivot and head structural carrier", 52)
    add_box(doc, stand, "Cable_Motion_KeepOut", "DC Trunk / Motion Cable Keep-out", (185, -20, 90), (50, 40, 420), COLORS["sensor"], "A-035; A-039", "Protected DC trunk and flex routing", 74)

    add_rotated_head_envelope(doc, motion, "Low_Forward_Envelope", "Low Height / Forward Tilt Envelope — 370 mm / −5°", 370, -5, COLORS["motion_low"])
    add_rotated_head_envelope(doc, motion, "High_Rearward_Envelope", "High Height / Rearward Tilt Envelope — 490 mm / +20°", 490, 20, COLORS["motion_high"])

    doc.recompute()
    try:
        import FreeCADGui as Gui
        Gui.activeDocument().activeView().viewAxonometric()
        Gui.activeDocument().activeView().fitAll()
    except Exception:
        pass
    doc.recompute()
    doc.saveAs(str(OUTPUT_PATH))
    return doc


if __name__ == "__main__":
    build_document()
    print("Hinoki Concept CAD Iteration 01 generated: {}".format(OUTPUT_PATH))
