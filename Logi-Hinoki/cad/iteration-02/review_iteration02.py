"""Geometry and traceability checks for the Iteration 02 review CAD."""

from pathlib import Path
import json
import sys

import FreeCAD as App


SCRIPT_PATH = Path(
    globals().get(
        "__file__",
        Path.cwd() / "cad" / "iteration-02" / "review_iteration02.py",
    )
)
CAD_FILE = SCRIPT_PATH.with_name("Hinoki_Concept_CAD_Iteration02_Review.FCStd")
REPORT_FILE = SCRIPT_PATH.with_name("Hinoki_Iteration02_CAD_Review.json")

OPEN_RISKS = [
    "Integrated display proxy must be decomposed into bare panel/touch/electronics packages.",
    "Privacy shutter travel and optical obscuration remain assumed.",
    "Custom stand geometry, centre of gravity, cable motion and tip stability remain open.",
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


def main():
    if not CAD_FILE.exists():
        raise FileNotFoundError("Iteration 02 CAD file is missing: {}".format(CAD_FILE))

    doc = App.open(str(CAD_FILE))
    head = doc.getObject("Head_Envelope").Shape.BoundBox
    display_obj = doc.getObject("OWT_LM3237_Display_Proxy")
    camera_obj = doc.getObject("LI_IMX477_140H_Camera")
    display = display_obj.Shape.BoundBox
    camera = camera_obj.Shape.BoundBox
    params = doc.getObject("Review_Parameters")
    stand = doc.getObject("Ergotron_HX_Mechanism_Benchmark")

    containment_failures = []
    for name, candidate in [
        ("OWT_LM3237_Display_Proxy", display),
        ("LI_IMX477_140H_Camera", camera),
    ]:
        if not is_contained(candidate, head):
            containment_failures.append(name)

    fov_value = camera_obj.HorizontalFOV.Value
    fov_pass = 134.0 <= fov_value <= 140.0
    source_status_pass = (
        display_obj.Classification == "Verified review proxy"
        and camera_obj.Classification == "Verified component envelope"
        and stand.Classification == "Verified mechanism benchmark"
    )

    side_margin = (params.HeadWidth.Value - params.DisplayWidth.Value) / 2.0
    top_reserve = params.HeadHeight.Value - params.DisplayHeight.Value
    depth_reserve = params.HeadDepth.Value - params.DisplayDepth.Value
    mass_headroom = params.StandCapacityMax.Value - params.DisplayProxyMass.Value

    geometry_pass = (
        not containment_failures
        and side_margin >= 0
        and top_reserve >= 0
        and depth_reserve >= 0
        and fov_pass
        and source_status_pass
        and mass_headroom > 0
    )
    status = "PassWithOpenRisks" if geometry_pass and OPEN_RISKS else "Fail"

    review = {
        "cad_file": str(CAD_FILE),
        "review_scope": "Preliminary market-envelope fit; not release geometry",
        "head_envelope_mm": [
            params.HeadWidth.Value,
            params.HeadDepth.Value,
            params.HeadHeight.Value,
        ],
        "containment_failures": containment_failures,
        "display_proxy": {
            "part_number": display_obj.SourcePartNumber,
            "classification": display_obj.Classification,
            "envelope_mm": [
                params.DisplayWidth.Value,
                params.DisplayDepth.Value,
                params.DisplayHeight.Value,
            ],
            "side_margin_each_mm": round(side_margin, 3),
            "top_reserve_mm": round(top_reserve, 3),
            "depth_reserve_mm": round(depth_reserve, 3),
            "architecture_note": "Integrated commercial display review proxy; not a bare panel/touch stack.",
        },
        "camera": {
            "part_number": camera_obj.SourcePartNumber,
            "classification": camera_obj.Classification,
            "envelope_mm": [
                params.CameraWidth.Value,
                params.CameraDepth.Value,
                params.CameraHeight.Value,
            ],
            "horizontal_fov_deg": fov_value,
            "fov_result": "Pass" if fov_pass else "Fail",
            "integration_note": camera_obj.ISPStatus,
        },
        "stand_benchmark": {
            "part_number": stand.SourcePartNumber,
            "classification": stand.Classification,
            "capacity_range_kg": [stand.CapacityMin.Value, stand.CapacityMax.Value],
            "published_lift_mm": stand.PublishedLift.Value,
            "pre_av_compute_headroom_kg": round(mass_headroom, 3),
            "geometry_note": stand.GeometryStatus,
        },
        "vesa_pattern_mm": doc.getObject("VESA_200x200_Interface").PatternSize.Value,
        "source_status_result": "Pass" if source_status_pass else "Fail",
        "open_risks": OPEN_RISKS,
        "cad_review_status": status,
        "step_export_status": "ConceptReviewOnly",
    }
    REPORT_FILE.write_text(json.dumps(review, indent=2), encoding="utf-8")
    print(json.dumps(review, indent=2))
    if status == "Fail":
        sys.exit(1)


if __name__ == "__main__":
    main()
