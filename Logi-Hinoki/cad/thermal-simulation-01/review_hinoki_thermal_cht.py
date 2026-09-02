"""Generate evidence for the Hinoki FLOEFD CHT handoff model."""

import json
import os
import sys
import uuid
from pathlib import Path

import FreeCAD as App
import Part


SCRIPT_PATH = Path(
    globals().get("__file__", sys._getframe().f_code.co_filename)
).resolve()
if str(SCRIPT_PATH.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT_PATH.parent))

import hinoki_thermal_parameters as parameters


MODEL_PATH = Path(
    os.environ.get(
        "HINOKI_THERMAL_MODEL_PATH",
        SCRIPT_PATH.with_name(parameters.MODEL_FILE),
    )
)
SETUP_PATH = Path(
    os.environ.get(
        "HINOKI_THERMAL_SETUP_PATH",
        SCRIPT_PATH.with_name(parameters.SETUP_JSON),
    )
)
REVIEW_PATH = Path(
    os.environ.get(
        "HINOKI_THERMAL_REVIEW_PATH",
        SCRIPT_PATH.with_name(parameters.REVIEW_JSON),
    )
)

EXPECTED_BBOX = (-parameters.HEAD["width"] / 2.0, 0.0, 0.0,
                parameters.HEAD["width"] / 2.0,
                parameters.HEAD["height"], parameters.HEAD["depth"])


def _write_json_temp(path, payload):
    """Write one complete JSON payload to a same-directory temporary file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(".{}.{}.tmp".format(path.name, uuid.uuid4().hex))
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return temporary


def _restore_path(path, original_bytes):
    """Restore a pre-existing path during a two-file publish rollback."""
    if original_bytes is None:
        if path.exists():
            path.unlink()
        return
    temporary = path.with_name(".{}.{}.rollback".format(path.name, uuid.uuid4().hex))
    try:
        temporary.write_bytes(original_bytes)
        os.replace(str(temporary), str(path))
    finally:
        if temporary.exists():
            temporary.unlink()


def _publish_evidence_pair(setup_payload, review_payload):
    """Stage both evidence files, then publish them as a rollback-safe pair."""
    original_setup = SETUP_PATH.read_bytes() if SETUP_PATH.exists() else None
    original_review = REVIEW_PATH.read_bytes() if REVIEW_PATH.exists() else None
    setup_temp = _write_json_temp(SETUP_PATH, setup_payload)
    review_temp = None
    try:
        review_temp = _write_json_temp(REVIEW_PATH, review_payload)
        if review_payload.get("status") != "Pass":
            raise RuntimeError("review status is not Pass")
        os.replace(str(setup_temp), str(SETUP_PATH))
        try:
            os.replace(str(review_temp), str(REVIEW_PATH))
        except Exception:
            _restore_path(SETUP_PATH, original_setup)
            raise
    finally:
        if setup_temp.exists():
            setup_temp.unlink()
        if review_temp is not None and review_temp.exists():
            review_temp.unlink()


def build_setup_payload():
    """Build the FLOEFD setup map from the immutable thermal parameters."""
    vent_openings = {
        "Inlet_Opening_Lower_Rear": {
            "role": "inlet",
            "width_mm": parameters.VENT["width"],
            "height_mm": parameters.VENT["height"],
            "area_mm2": parameters.VENT["area"],
        },
        "Outlet_Opening_Upper_Rear": {
            "role": "outlet",
            "width_mm": parameters.VENT["width"],
            "height_mm": parameters.VENT["height"],
            "area_mm2": parameters.VENT["area"],
        },
    }
    return {
        "solver": "Simcenter FLOEFD",
        "analysis_type": "ConjugateHeatTransfer",
        "units": "mm, W, degC",
        "ambient_c": parameters.AMBIENT_C,
        "cooling_mode": parameters.COOLING_MODE,
        "fan_present": False,
        "gravity_mm_s2": list(parameters.GRAVITY_MM_S2),
        "heat_loads_w": dict(parameters.HEAT_LOADS_W),
        "material_intent": dict(parameters.MATERIAL_INTENT),
        "solid_bodies": list(parameters.SOLID_BODIES),
        "fluid_bodies": list(parameters.FLUID_BODIES),
        "boundary_faces": list(parameters.BOUNDARY_FACES),
        "vent_openings": vent_openings,
        "external_domain": "Create in FLOEFD",
        "assumption_status": "Preliminary concept inputs",
        "model_file": parameters.MODEL_FILE,
    }


def _bbox_tuple(shape):
    bounds = shape.BoundBox
    return (
        bounds.XMin, bounds.YMin, bounds.ZMin,
        bounds.XMax, bounds.YMax, bounds.ZMax,
    )


def _within_bbox(actual, expected, tolerance=0.1):
    return all(abs(left - right) <= tolerance for left, right in zip(actual, expected))


def _leaf_geometry(shape):
    leaves = shape.Solids
    return bool(leaves) and all(
        leaf.isValid() and leaf.isClosed() and leaf.Volume > 0.0
        for leaf in leaves
    )


def _vent_channels():
    width = parameters.VENT["width"]
    height = parameters.VENT["height"]
    wall = parameters.REAR_WALL
    depth = parameters.HEAD["depth"]
    lower_y = 20.0
    upper_y = parameters.HEAD["height"] - lower_y - height
    return tuple(
        Part.makeBox(
            width,
            height,
            wall,
            App.Vector(-width / 2.0, y_origin, depth - wall),
        )
        for y_origin in (lower_y, upper_y)
    )


def review_document(model_path):
    """Return machine-readable hard-gate evidence for one native FCStd."""
    doc = App.open(str(model_path))
    required = list(
        parameters.SOLID_BODIES
        + parameters.FLUID_BODIES
        + parameters.BOUNDARY_FACES
    )
    try:
        present = all(doc.getObject(name) is not None for name in required)
        physical = {
            name: doc.getObject(name)
            for name in parameters.SOLID_BODIES
            if doc.getObject(name) is not None
        }
        air = doc.getObject("Internal_Air_Volume")
        boundaries = {
            name: doc.getObject(name)
            for name in parameters.BOUNDARY_FACES
            if doc.getObject(name) is not None
        }

        solid_geometry = {
            name: {
                "shape_type": obj.Shape.ShapeType,
                "leaf_solids": len(obj.Shape.Solids),
                "valid_closed_positive": _leaf_geometry(obj.Shape),
                "volume_mm3": obj.Shape.Volume,
                "bbox_mm": _bbox_tuple(obj.Shape),
            }
            for name, obj in physical.items()
        }
        valid_closed_positive = (
            len(physical) == len(parameters.SOLID_BODIES)
            and all(item["valid_closed_positive"] for item in solid_geometry.values())
        )

        if physical:
            actual_bbox = (
                min(obj.Shape.BoundBox.XMin for obj in physical.values()),
                min(obj.Shape.BoundBox.YMin for obj in physical.values()),
                min(obj.Shape.BoundBox.ZMin for obj in physical.values()),
                max(obj.Shape.BoundBox.XMax for obj in physical.values()),
                max(obj.Shape.BoundBox.YMax for obj in physical.values()),
                max(obj.Shape.BoundBox.ZMax for obj in physical.values()),
            )
        else:
            actual_bbox = (0.0,) * 6
        bbox_gate = _within_bbox(actual_bbox, EXPECTED_BBOX)

        vent_evidence = {}
        rear = doc.getObject("Rear_Enclosure")
        for name, boundary in boundaries.items():
            area = boundary.Shape.Area
            air_connection = (
                air.Shape.common(boundary.Shape).Area if air is not None else 0.0
            )
            rear_cut = (
                rear.Shape.common(boundary.Shape).Area if rear is not None else 0.0
            )
            vent_evidence[name] = {
                "area_mm2": area,
                "expected_area_mm2": parameters.VENT["area"],
                "normal_z": boundary.Shape.normalAt(0.0, 0.0).z,
                "air_connection_area_mm2": air_connection,
                "rear_intersection_area_mm2": rear_cut,
                "area_within_one_percent": abs(area - parameters.VENT["area"])
                <= parameters.VENT["area"] * 0.01,
                "opens_to_air": air_connection > parameters.VENT["area"] - 0.1,
                "cut_through_rear": rear_cut <= 0.01,
            }
        vent_area_gate = (
            len(vent_evidence) == len(parameters.BOUNDARY_FACES)
            and all(item["area_within_one_percent"] for item in vent_evidence.values())
        )
        air_connection_gate = (
            len(vent_evidence) == len(parameters.BOUNDARY_FACES)
            and all(
                item["opens_to_air"] and item["cut_through_rear"]
                for item in vent_evidence.values()
            )
        )

        air_valid = bool(
            air is not None
            and air.Shape.isValid()
            and air.Shape.Volume > 0.0
            and len(air.Shape.Solids) == 1
            and _leaf_geometry(air.Shape)
            and air.MaterialIntent == parameters.MATERIAL_INTENT["Internal_Air_Volume"]
        )
        air_solid_overlaps = {
            name: air.Shape.common(obj.Shape).Volume
            for name, obj in physical.items()
        } if air is not None else {}
        air_disjoint_gate = (
            len(air_solid_overlaps) == len(parameters.SOLID_BODIES)
            and all(value <= 0.01 for value in air_solid_overlaps.values())
        )
        connected_air_gate = air_valid and air_disjoint_gate

        vent_channels = _vent_channels()
        heat_containment = {}
        vent_obstructions = []
        for name, expected_load in parameters.HEAT_LOADS_W.items():
            obj = doc.getObject(name)
            if obj is None:
                heat_containment[name] = {"inside_head": False, "heat_load_w": None}
                continue
            bounds = obj.Shape.BoundBox
            inside = (
                bounds.XMin >= EXPECTED_BBOX[0] - 0.01
                and bounds.XMax <= EXPECTED_BBOX[3] + 0.01
                and bounds.YMin >= EXPECTED_BBOX[1] - 0.01
                and bounds.YMax <= EXPECTED_BBOX[4] + 0.01
                and bounds.ZMin >= EXPECTED_BBOX[2] - 0.01
                and bounds.ZMax <= EXPECTED_BBOX[5] + 0.01
            )
            heat_containment[name] = {
                "inside_head": inside,
                "bbox_mm": _bbox_tuple(obj.Shape),
                "heat_load_w": getattr(obj, "HeatLoadW", None),
                "expected_heat_load_w": expected_load,
            }
            for index, channel in enumerate(vent_channels):
                volume = obj.Shape.common(channel).Volume
                if volume > 0.01:
                    vent_obstructions.append(
                        {"body": name, "channel": index, "volume_mm3": volume}
                    )
        heat_containment_gate = (
            len(heat_containment) == len(parameters.HEAT_LOADS_W)
            and all(item["inside_head"] for item in heat_containment.values())
        )
        vents_unobstructed_gate = not vent_obstructions

        overlaps = []
        names = tuple(physical)
        for index, left in enumerate(names):
            for right in names[index + 1:]:
                volume = physical[left].Shape.common(physical[right].Shape).Volume
                if volume > 0.01:
                    overlaps.append({
                        "left": left,
                        "right": right,
                        "volume_mm3": volume,
                    })

        stack = ("Mid_Frame", "Heat_Spreader", "TIM_QC7790", "Heat_QC7790", "Carrier_PCB")
        stack_interfaces = []
        for lower, upper in zip(stack, stack[1:]):
            if lower not in physical or upper not in physical:
                stack_interfaces.append({"lower": lower, "upper": upper, "touches": False})
                continue
            lower_shape = physical[lower].Shape
            upper_shape = physical[upper].Shape
            stack_interfaces.append({
                "lower": lower,
                "upper": upper,
                "common_volume_mm3": lower_shape.common(upper_shape).Volume,
                "z_gap_mm": upper_shape.BoundBox.ZMin - lower_shape.BoundBox.ZMax,
                "touches": (
                    lower_shape.common(upper_shape).Volume < 1e-7
                    and abs(upper_shape.BoundBox.ZMin - lower_shape.BoundBox.ZMax) < 1e-6
                ),
            })
        stack_contact_gate = len(stack_interfaces) == len(stack) - 1 and all(
            item["touches"] for item in stack_interfaces
        )

        observed_heat = sum(
            item["heat_load_w"]
            for item in heat_containment.values()
            if isinstance(item["heat_load_w"], (int, float))
        )
        exact_heat_gate = (
            len(heat_containment) == len(parameters.HEAT_LOADS_W)
            and all(
                abs(item["heat_load_w"] - item["expected_heat_load_w"]) < 1e-6
                for item in heat_containment.values()
                if isinstance(item["heat_load_w"], (int, float))
            )
            and observed_heat == 57.0
        )

        material_metadata = {
            name: (
                physical[name].MaterialIntent
                if name in physical else None
            )
            for name in parameters.SOLID_BODIES
        }
        material_metadata_gate = (
            len(material_metadata) == len(parameters.SOLID_BODIES)
            and all(
                material_metadata[name] == parameters.MATERIAL_INTENT[name]
                for name in parameters.SOLID_BODIES
            )
        )
        metadata = doc.getObject("Thermal_Model_Metadata")
        metadata_gate = bool(
            metadata is not None
            and abs(metadata.AmbientC - parameters.AMBIENT_C) < 1e-6
            and tuple(metadata.GravityMmS2) == parameters.GRAVITY_MM_S2
            and abs(metadata.TotalHeatW - 57.0) < 1e-6
            and metadata.CoolingMode == parameters.COOLING_MODE
        )

        hard_gates = {
            "required_objects": present,
            "valid_closed_positive": valid_closed_positive,
            "head_bbox": bbox_gate,
            "vent_areas": vent_area_gate,
            "connected_internal_air": connected_air_gate,
            "air_boundary_connection": air_connection_gate,
            "heat_containment": heat_containment_gate,
            "vents_unobstructed": vents_unobstructed_gate,
            "no_unauthorized_overlaps": not overlaps,
            "conduction_stack_contacts": stack_contact_gate,
            "exact_total_heat": exact_heat_gate,
            "material_metadata": material_metadata_gate,
            "thermal_metadata": metadata_gate,
        }
        return {
            "status": "Pass" if all(hard_gates.values()) else "Fail",
            "hard_gates": hard_gates,
            "required_objects": required,
            "solid_geometry": solid_geometry,
            "overall_bbox_mm": actual_bbox,
            "expected_bbox_mm": EXPECTED_BBOX,
            "vent_openings": vent_evidence,
            "internal_air": {
                "valid_closed_positive": air_valid,
                "connected_solid_count": len(air.Shape.Solids) if air else 0,
                "volume_mm3": air.Shape.Volume if air else 0.0,
                "solid_overlaps_mm3": air_solid_overlaps,
            },
            "heat_sources": heat_containment,
            "vent_obstructions": vent_obstructions,
            "unauthorized_overlaps": overlaps,
            "conduction_stack_interfaces": stack_interfaces,
            "total_heat_w": observed_heat,
            "material_intent": material_metadata,
            "thermal_metadata": {
                "ambient_c": metadata.AmbientC if metadata else None,
                "cooling_mode": metadata.CoolingMode if metadata else None,
                "gravity_mm_s2": list(metadata.GravityMmS2) if metadata else None,
                "total_heat_w": metadata.TotalHeatW if metadata else None,
            },
        }
    finally:
        App.closeDocument(doc.Name)


def generate_evidence():
    """Review first, then atomically publish setup and review evidence together."""
    setup = build_setup_payload()
    review = review_document(MODEL_PATH)
    if review["status"] != "Pass":
        raise RuntimeError("review status is not Pass")
    _publish_evidence_pair(setup, review)
    return review


def main():
    """Run review generation with an unambiguous success/failure sentinel."""
    try:
        evidence = generate_evidence()
    except Exception as error:
        print("HINOKI_THERMAL_REVIEW_FAIL {}".format(error))
        return 1
    if evidence["status"] != "Pass":
        print("HINOKI_THERMAL_REVIEW_FAIL review status is not Pass")
        return 1
    print("HINOKI_THERMAL_REVIEW_OK {}".format(REVIEW_PATH))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
