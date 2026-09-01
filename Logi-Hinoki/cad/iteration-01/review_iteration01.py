"""Geometry checks for the Hinoki Concept CAD Iteration 01 assembly."""

from pathlib import Path
import json
import sys

import FreeCAD as App


SCRIPT_PATH = Path(globals().get("__file__", Path.cwd() / "cad" / "iteration-01" / "review_iteration01.py"))
CAD_FILE = SCRIPT_PATH.with_name("Hinoki_Concept_CAD_Iteration01.FCStd")
REPORT_FILE = SCRIPT_PATH.with_name("Hinoki_Iteration01_CAD_Review.json")


HEAD_PACKAGES = [
    "Display_Touch_Stack",
    "Camera_Manual_Shutter",
    "Speaker_Left",
    "Speaker_Right",
    "Front_Light_Left",
    "Front_Light_Right",
    "Radar_KeepOut",
    "Ambient_Light_Provision",
    "Compute_Thermal_Module",
    "USB_C_PD_Interface",
    "Rear_IO_Bay",
    "VESA_Reinforcement",
]

HARD_PACKAGES = [
    "Display_Touch_Stack",
    "Camera_Manual_Shutter",
    "Speaker_Left",
    "Speaker_Right",
    "Front_Light_Left",
    "Front_Light_Right",
    "Radar_KeepOut",
    "Ambient_Light_Provision",
    "Compute_Thermal_Module",
    "USB_C_PD_Interface",
    "Rear_IO_Bay",
    "VESA_Reinforcement",
]


def is_contained(inner, outer, tolerance=0.01):
    return (
        inner.XMin >= outer.XMin - tolerance
        and inner.XMax <= outer.XMax + tolerance
        and inner.YMin >= outer.YMin - tolerance
        and inner.YMax <= outer.YMax + tolerance
        and inner.ZMin >= outer.ZMin - tolerance
        and inner.ZMax <= outer.ZMax + tolerance
    )


def strictly_intersects(a, b, tolerance=0.01):
    return (
        a.XMin < b.XMax - tolerance
        and a.XMax > b.XMin + tolerance
        and a.YMin < b.YMax - tolerance
        and a.YMax > b.YMin + tolerance
        and a.ZMin < b.ZMax - tolerance
        and a.ZMax > b.ZMin + tolerance
    )


def main():
    if not CAD_FILE.exists():
        raise FileNotFoundError("Iteration 01 CAD file is missing: {}".format(CAD_FILE))
    doc = App.open(str(CAD_FILE))
    head = doc.getObject("Head_Envelope").Shape.BoundBox
    containment_failures = []
    for name in HEAD_PACKAGES:
        candidate = doc.getObject(name)
        if candidate is None or not is_contained(candidate.Shape.BoundBox, head):
            containment_failures.append(name)

    collision_pairs = []
    for index, first_name in enumerate(HARD_PACKAGES):
        first_box = doc.getObject(first_name).Shape.BoundBox
        for second_name in HARD_PACKAGES[index + 1:]:
            second_box = doc.getObject(second_name).Shape.BoundBox
            if strictly_intersects(first_box, second_box):
                collision_pairs.append([first_name, second_name])

    parameters = doc.getObject("Master_Parameters")
    display = doc.getObject("Display_Touch_Stack").Shape.BoundBox
    av_bar = doc.getObject("Upper_AV_Bar").Shape.BoundBox
    camera_fov = doc.getObject("Camera_FOV_KeepOut")
    panel_geometry = {
        "left_bezel_mm": display.XMin - head.XMin,
        "right_bezel_mm": head.XMax - display.XMax,
        "bottom_bezel_mm": display.ZMin - head.ZMin,
        "display_to_av_bar_gap_mm": av_bar.ZMin - display.ZMax,
    }
    fov_pass = 134.0 <= camera_fov.HorizontalFOV.Value <= 140.0 and camera_fov.ClearanceStatus.startswith("Concept pass")
    review = {
        "cad_file": str(CAD_FILE),
        "head_envelope_mm": [parameters.HeadWidth.Value, parameters.HeadDepth.Value, parameters.HeadHeight.Value],
        "motion_states": {
            "low_forward": {"pivot_mm": parameters.PivotLow.Value, "tilt_deg": parameters.TiltForward.Value},
            "neutral": {"pivot_mm": parameters.PivotNeutral.Value, "tilt_deg": 0.0},
            "high_rearward": {"pivot_mm": parameters.PivotHigh.Value, "tilt_deg": parameters.TiltRearward.Value},
        },
        "head_containment_failures": containment_failures,
        "unintended_hard_package_collisions": collision_pairs,
        "panel_geometry_mm": panel_geometry,
        "camera_fov": {
            "horizontal_fov_deg": camera_fov.HorizontalFOV.Value,
            "clearance_status": camera_fov.ClearanceStatus,
            "result": "Pass" if fov_pass else "Fail",
        },
        "cad_review_status": "Pass" if not containment_failures and not collision_pairs and fov_pass else "Fail",
        "limitations": [
            "FOV ray clearance, shutter motion, I/O insertion sweep, cable bend radius and real component mass properties remain CAD review items.",
            "All A-013 through A-040 controlled concept values remain Assumed and are not release dimensions.",
        ],
    }
    REPORT_FILE.write_text(json.dumps(review, indent=2), encoding="utf-8")
    print(json.dumps(review, indent=2))
    if review["cad_review_status"] != "Pass":
        sys.exit(1)


if __name__ == "__main__":
    main()
