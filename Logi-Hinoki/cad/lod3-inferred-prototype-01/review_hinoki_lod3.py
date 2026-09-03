"""Validate the head-only Hinoki LOD 3 Task 5 checkpoint."""

from itertools import combinations
import json
import os
from pathlib import Path
import sys
import uuid

import FreeCAD as App


SCRIPT_PATH = Path(
    globals().get("__file__", sys._getframe().f_code.co_filename)
).resolve()
PACKAGE_DIR = SCRIPT_PATH.parent
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

import hinoki_lod3_parameters as p


MODEL_PATH = Path(
    os.environ.get(
        "HINOKI_LOD3_MODEL_PATH",
        str(PACKAGE_DIR / p.OUTPUT_FILES["master_fcstd"]),
    )
).resolve()
REVIEW_PATH = Path(
    os.environ.get(
        "HINOKI_LOD3_REVIEW_OUT",
        str(PACKAGE_DIR / p.OUTPUT_FILES["validation_json"]),
    )
).resolve()

OVERLAP_THRESHOLD_MM3 = 0.01
REFERENCE_ASSEMBLY = "08_Reference_Datums_Keepouts"
EXPECTED_AUTHORIZED_CONTACTS = (
    ("Camera_Module", "Heat_Camera"),
    ("Front_Light_Left", "Heat_Front_Lighting"),
    ("Front_Light_Right", "Heat_Front_Lighting"),
)
DEFERRED_GATES = (
    "stand_envelope",
    "stand_motion",
    "stand_interference",
)


def _shape_bbox(shape):
    box = shape.BoundBox
    return [
        float(box.XMin),
        float(box.YMin),
        float(box.ZMin),
        float(box.XMax),
        float(box.YMax),
        float(box.ZMax),
    ]


def _metadata_record(obj):
    record = {}
    for key in p.METADATA_KEYS:
        value = getattr(obj, key, None)
        if key == "HeatLoadW" and value is not None:
            value = float(value)
        record[key] = value
    return record


def _metadata_complete(record):
    required_strings = (
        "PartID",
        "PartName",
        "ParentAssembly",
        "MaterialIntent",
        "SourceClass",
        "SourceReference",
        "Confidence",
        "ThermalDisposition",
        "Revision",
    )
    return (
        all(isinstance(record[key], str) and record[key].strip() for key in required_strings)
        and record["SourceClass"] in p.SOURCE_CLASSES
        and record["ThermalDisposition"] in p.THERMAL_DISPOSITIONS
        and record["ManufacturingAuthority"] is False
        and isinstance(record["HeatLoadW"], (int, float))
    )


def _physical_semantic_parts(semantic_parts):
    return [
        obj
        for obj in semantic_parts
        if getattr(obj, "ParentAssembly", "") != REFERENCE_ASSEMBLY
        and getattr(obj, "PhysicalCollision", True)
    ]


def _group_evidence(doc, semantic_parts):
    groups = [
        obj
        for obj in doc.Objects
        if obj.TypeId == "App::DocumentObjectGroup"
    ]
    actual_groups = [group.Label for group in groups]
    groups_by_label = {group.Label: group for group in groups}
    failures = []
    if actual_groups != list(p.REQUIRED_TOP_GROUPS):
        failures.append(
            {
                "reason": "required_group_sequence",
                "actual_groups": actual_groups,
            }
        )
    for obj in semantic_parts:
        parent = getattr(obj, "ParentAssembly", "")
        group = groups_by_label.get(parent)
        child_names = {
            child.Name for child in tuple(getattr(group, "Group", ()))
        } if group is not None else set()
        if group is None or obj.Name not in child_names:
            failures.append(
                {
                    "part": obj.Name,
                    "parent_assembly": parent,
                    "reason": "missing_or_incorrect_group_ownership",
                }
            )
    return {
        "required_groups": list(p.REQUIRED_TOP_GROUPS),
        "actual_groups": actual_groups,
        "failures": failures,
    }


def _geometry_evidence(physical_parts):
    failures = []
    parts = []
    for obj in physical_parts:
        shape = getattr(obj, "Shape", None)
        valid = bool(
            shape is not None
            and not shape.isNull()
            and shape.isValid()
            and float(shape.Volume) > 0.0
        )
        volume = float(shape.Volume) if shape is not None and not shape.isNull() else 0.0
        parts.append(
            {
                "name": obj.Name,
                "valid_positive": valid,
                "volume_mm3": volume,
            }
        )
        if not valid:
            failures.append(obj.Name)
    return {
        "part_count": len(physical_parts),
        "parts": parts,
        "failures": failures,
    }


def _contact_evidence(physical_parts):
    by_name = {obj.Name: obj for obj in physical_parts}
    declared = set()
    asymmetric = []
    for obj in physical_parts:
        for target in tuple(getattr(obj, "AuthorizedContactTargets", ())):
            pair = tuple(sorted((obj.Name, target)))
            declared.add(pair)
            other = by_name.get(target)
            if other is None or obj.Name not in tuple(
                getattr(other, "AuthorizedContactTargets", ())
            ):
                asymmetric.append([obj.Name, target])

    expected = {tuple(sorted(pair)) for pair in EXPECTED_AUTHORIZED_CONTACTS}
    contacts = []
    missing_geometry = []
    for pair in EXPECTED_AUTHORIZED_CONTACTS:
        left = by_name.get(pair[0])
        right = by_name.get(pair[1])
        overlap = 0.0
        if left is None or right is None:
            missing_geometry.append(list(pair))
        else:
            overlap = float(left.Shape.common(right.Shape).Volume)
            if overlap <= OVERLAP_THRESHOLD_MM3:
                missing_geometry.append(list(pair))
        contacts.append({"parts": list(pair), "overlap_mm3": overlap})

    checked_forbidden_pairs = 0
    forbidden = []
    for left, right in combinations(physical_parts, 2):
        pair = tuple(sorted((left.Name, right.Name)))
        if pair in expected:
            continue
        checked_forbidden_pairs += 1
        overlap = float(left.Shape.common(right.Shape).Volume)
        if overlap > OVERLAP_THRESHOLD_MM3:
            forbidden.append(
                {
                    "parts": [left.Name, right.Name],
                    "overlap_mm3": overlap,
                }
            )

    exact_matrix = declared == expected and not asymmetric and not missing_geometry
    return contacts, forbidden, exact_matrix, {
        "declared_pairs": [list(pair) for pair in sorted(declared)],
        "expected_pairs": [list(pair) for pair in sorted(expected)],
        "asymmetric_declarations": asymmetric,
        "missing_contact_geometry": missing_geometry,
        "checked_forbidden_pair_count": checked_forbidden_pairs,
    }


def _feature_evidence(doc):
    boards_with_holes = []
    for name in (
        "Carrier_PCB",
        "Compute_SOM_PCB",
        "Power_PCB",
        "IO_PCB",
        "WiFi_BLE_Module",
    ):
        obj = doc.getObject(name)
        if obj is None or obj.Shape.isNull():
            continue
        box = obj.Shape.BoundBox
        box_volume = float(box.XLength * box.YLength * box.ZLength)
        if float(obj.Shape.Volume) < box_volume - OVERLAP_THRESHOLD_MM3:
            boards_with_holes.append(name)

    vent_evidence = []
    for name, parameter_name in (
        ("Inlet_Vent_Field", "Inlet_Lower_Rear"),
        ("Outlet_Vent_Field", "Outlet_Upper_Rear"),
    ):
        obj = doc.getObject(name)
        if (
            obj is not None
            and float(getattr(obj, "OpenArea", 0.0))
            >= p.VENTS[parameter_name]["minimum_open_area"]
        ):
            vent_evidence.append(name)

    return {
        "wall": [
            name
            for name in ("Rear_Enclosure",)
            if doc.getObject(name) is not None
            and float(getattr(doc.getObject(name), "WallThickness", 0.0)) > 0.0
        ],
        "rib": [
            obj.Name
            for obj in doc.Objects
            if obj.Name.startswith("Structural_Rib_")
            and float(getattr(obj, "RibThickness", 0.0)) > 0.0
        ],
        "boss": [
            obj.Name
            for obj in doc.Objects
            if obj.Name.startswith("Primary_Boss_")
            and float(getattr(obj, "BossOuterDiameter", 0.0)) > 0.0
        ],
        "bend": [
            name
            for name in ("SOM_Shield_Can", "Power_Shield_Can", "IO_Shield_Can")
            if doc.getObject(name) is not None
        ],
        "hole": boards_with_holes,
        "hatch": [
            name
            for name in ("Rear_IO_Cover", "Rear_Hatch_TIM")
            if doc.getObject(name) is not None
        ],
        "fastener": [
            obj.Name for obj in doc.Objects if obj.Name.startswith("M3_Fastener_")
        ],
        "vent": vent_evidence,
        "thermal_contact": [
            name
            for name in ("TIM_QC7790", "Rear_Hatch_TIM")
            if doc.getObject(name) is not None
        ],
    }


def _head_envelope(physical_parts):
    expected = [p.HEAD["width"], p.HEAD["height"], p.HEAD["depth"]]
    if not physical_parts:
        return {
            "actual_mm": [0.0, 0.0, 0.0],
            "expected_mm": expected,
            "tolerance_mm": 0.1,
            "within_tolerance": False,
        }
    bounds = [_shape_bbox(obj.Shape) for obj in physical_parts]
    aggregate = [
        min(item[0] for item in bounds),
        min(item[1] for item in bounds),
        min(item[2] for item in bounds),
        max(item[3] for item in bounds),
        max(item[4] for item in bounds),
        max(item[5] for item in bounds),
    ]
    actual = [
        aggregate[3] - aggregate[0],
        aggregate[4] - aggregate[1],
        aggregate[5] - aggregate[2],
    ]
    return {
        "bbox_mm": aggregate,
        "actual_mm": actual,
        "expected_mm": expected,
        "tolerance_mm": 0.1,
        "within_tolerance": all(
            abs(actual_value - expected_value) <= 0.1
            for actual_value, expected_value in zip(actual, expected)
        ),
    }


def validate_master(doc):
    """Return machine-readable evidence for active head-only hard gates."""
    semantic_parts = [
        obj for obj in doc.Objects if getattr(obj, "IsSemanticPart", False)
    ]
    physical_parts = _physical_semantic_parts(semantic_parts)
    names = [obj.Name for obj in semantic_parts]
    group_ownership = _group_evidence(doc, semantic_parts)
    physical_geometry = _geometry_evidence(physical_parts)

    metadata_parts = [_metadata_record(obj) for obj in semantic_parts]
    incomplete_parts = [
        obj.Name
        for obj, record in zip(semantic_parts, metadata_parts)
        if not _metadata_complete(record)
    ]
    manufacturing_failures = [
        obj.Name
        for obj, record in zip(semantic_parts, metadata_parts)
        if record["ManufacturingAuthority"] is not False
    ]
    source_class_counts = {
        source_class: sum(
            1 for record in metadata_parts if record["SourceClass"] == source_class
        )
        for source_class in p.SOURCE_CLASSES
    }

    contacts, forbidden, exact_contacts, contact_matrix = _contact_evidence(
        physical_parts
    )
    feature_evidence = _feature_evidence(doc)
    head_envelope = _head_envelope(physical_parts)
    hard_gates = {
        "semantic_part_count": 80 <= len(semantic_parts) <= 120
        and len(names) == len(set(names)),
        "eight_group_ownership": not group_ownership["failures"],
        "valid_positive_physical_geometry": not physical_geometry["failures"],
        "complete_metadata": not incomplete_parts and not manufacturing_failures,
        "exact_authorized_contact_matrix": exact_contacts,
        "no_forbidden_overlaps": not forbidden,
        "required_feature_evidence": all(feature_evidence.values()),
        "head_envelope": head_envelope["within_tolerance"],
    }
    overall = "Pass" if all(hard_gates.values()) else "Fail"
    return {
        "status": overall,
        "overall": overall,
        "scope": "HeadOnlyTask5Checkpoint",
        "limitations": p.PROTOTYPE_LIMITATION,
        "hard_gates": hard_gates,
        "deferred_gates": list(DEFERRED_GATES),
        "overlap_threshold_mm3": OVERLAP_THRESHOLD_MM3,
        "semantic_parts": {
            "count": len(semantic_parts),
            "names_unique": len(names) == len(set(names)),
            "names": names,
        },
        "group_ownership": group_ownership,
        "physical_geometry": physical_geometry,
        "metadata": {
            "required_keys": list(p.METADATA_KEYS),
            "incomplete_parts": incomplete_parts,
            "manufacturing_authority_failures": manufacturing_failures,
            "source_class_counts": source_class_counts,
            "parts": metadata_parts,
        },
        "authorized_contacts": contacts,
        "authorized_contact_matrix": contact_matrix,
        "forbidden_overlaps": forbidden,
        "feature_evidence": feature_evidence,
        "head_envelope": head_envelope,
    }


def validate_model(model_path):
    """Open, validate, and close one native FCStd model."""
    doc = App.open(str(model_path))
    try:
        return validate_master(doc)
    finally:
        App.closeDocument(doc.Name)


def publish_report(path, report):
    """Publish a passing validation report atomically."""
    if report.get("status") != "Pass":
        raise RuntimeError("LOD 3 master validation failed")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(".{}.{}.tmp".format(path.name, uuid.uuid4().hex))
    try:
        temporary.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(str(temporary), str(path))
    finally:
        if temporary.exists():
            temporary.unlink()


def main():
    """Validate and publish with mutually exclusive result sentinels."""
    try:
        report = validate_model(MODEL_PATH)
        publish_report(REVIEW_PATH, report)
    except Exception as error:
        print("HINOKI_LOD3_REVIEW_FAIL {}".format(error))
        return 1
    print("HINOKI_LOD3_REVIEW_OK {}".format(REVIEW_PATH))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
