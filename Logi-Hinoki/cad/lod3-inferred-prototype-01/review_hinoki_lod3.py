"""Validate the head-only Hinoki LOD 3 Task 8 quality-remediation checkpoint.

New in Task 8 remediation (Q-01/Q-02/Q-03):
    - Enclosure mating check: continuous perimeter z-coverage from
      Front_Bezel + Metal_Mid_Frame + Rear_Enclosure over 0..62 mm with no
      undesigned side opening (Q-01).
    - Rib host attachment check: ribs are fused features of Rear_Enclosure
      (via RibFeatureCount and RibFeatureIds properties) rather than
      floating semantic parts (Q-03).
    - Fastener engagement check: every M3/M4 fastener bbox spans from
      inside its target boss to at least the rear cover outer face (Q-03).
    - Unique heat-source mapping and budget conservation: each HeatSourceID
      appears exactly once and the total budget equals the frozen 57 W
      (Q-02 requires the split of the historic 20 W BLU into four sources
      without duplicating or losing budget).
    - Semantic-part contract updated from 97/79 to 94/76; 10 heat sources
      updated to 13 (Panel Module: BLU_LED, BLU_Driver, TCON,
      Panel_Gate_Source).
"""

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
    # AV/lighting sensor bonds
    ("Camera_Module", "Heat_Camera"),
    ("Front_Light_Left", "Heat_Front_Lighting"),
    ("Front_Light_Right", "Heat_Front_Lighting"),
    # Structural root engagements (corner and VESA bosses -> mid-frame)
    ("Metal_Mid_Frame", "Primary_Boss_01"),
    ("Metal_Mid_Frame", "Primary_Boss_02"),
    ("Metal_Mid_Frame", "Primary_Boss_03"),
    ("Metal_Mid_Frame", "Primary_Boss_04"),
    ("Metal_Mid_Frame", "VESA_Boss_01"),
    ("Metal_Mid_Frame", "VESA_Boss_02"),
    ("Metal_Mid_Frame", "VESA_Boss_03"),
    ("Metal_Mid_Frame", "VESA_Boss_04"),
    # QC7790 die-to-rear-cover thermal conduction chain
    ("Heat_QC7790", "TIM_QC7790"),
    ("Copper_Spreader", "TIM_QC7790"),
    ("Copper_Spreader", "Heat_Pipe_Left"),
    ("Copper_Spreader", "Heat_Pipe_Right"),
    ("Aluminum_Interface", "Heat_Pipe_Left"),
    ("Aluminum_Interface", "Heat_Pipe_Right"),
    ("Aluminum_Interface", "Aluminum_Riser"),
    ("Aluminum_Riser", "Rear_Hatch_TIM"),
    ("Rear_Hatch_TIM", "Rear_IO_Cover"),
    # Task 6 stand structural connections
    ("Base_Cover", "Base_Steel_Plate"),
    ("Lift_Carriage", "Yoke_Arm"),
)
DEFERRED_GATES = ()

STAND_KINEMATIC_KEYS = (
    "overall_height_min", "overall_height_max",
    "height_travel", "tilt_min", "tilt_max",
    "swivel_min", "swivel_max", "depth_envelope",
    "static_margin_min",
)

FASTENER_TARGET_HOSTS = {
    "M3_Fastener_01": "Primary_Boss_01",
    "M3_Fastener_02": "Primary_Boss_02",
    "M3_Fastener_03": "Primary_Boss_03",
    "M3_Fastener_04": "Primary_Boss_04",
    "M4_VESA_Fastener_01": "VESA_Boss_01",
    "M4_VESA_Fastener_02": "VESA_Boss_02",
    "M4_VESA_Fastener_03": "VESA_Boss_03",
    "M4_VESA_Fastener_04": "VESA_Boss_04",
}


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
        if value is None:
            record[key] = None
            continue
        if key in ("HeatLoadW", "ThermalConductivityWmK"):
            record[key] = float(value)
            continue
        if hasattr(value, "Value"):
            record[key] = float(value.Value)
            continue
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
        "ExternalSourceStatus",
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

    rear = doc.getObject("Rear_Enclosure")
    rib_feature_ids = []
    if rear is not None:
        raw = tuple(getattr(rear, "RibFeatureIds", ()))
        rib_feature_ids = [str(name) for name in raw]

    return {
        "wall": [
            name
            for name in ("Rear_Enclosure", "Metal_Mid_Frame")
            if doc.getObject(name) is not None
            and float(getattr(doc.getObject(name), "WallThickness", 0.0)) > 0.0
            or (
                name == "Metal_Mid_Frame"
                and doc.getObject(name) is not None
                and float(getattr(doc.getObject(name), "PerimeterWallThickness", 0.0)) > 0.0
            )
        ],
        "rib": rib_feature_ids,
        "boss": [
            obj.Name
            for obj in doc.Objects
            if (
                obj.Name.startswith("Primary_Boss_")
                or obj.Name.startswith("VESA_Boss_")
            )
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
            obj.Name
            for obj in doc.Objects
            if obj.Name.startswith("M3_Fastener_")
            or obj.Name.startswith("M4_VESA_Fastener_")
        ],
        "vent": vent_evidence,
        "thermal_contact": [
            name
            for name in ("TIM_QC7790", "Rear_Hatch_TIM")
            if doc.getObject(name) is not None
        ],
    }


STAND_ASSEMBLY = "06_Stand_Base_Kinematics"


def _head_only_parts(physical_parts):
    return [
        obj for obj in physical_parts
        if getattr(obj, "ParentAssembly", "") != STAND_ASSEMBLY
    ]


def _stand_only_parts(physical_parts):
    return [
        obj for obj in physical_parts
        if getattr(obj, "ParentAssembly", "") == STAND_ASSEMBLY
    ]


def _head_envelope(physical_parts):
    expected = [p.HEAD["width"], p.HEAD["height"], p.HEAD["depth"]]
    head_parts = _head_only_parts(physical_parts)
    if not head_parts:
        return {
            "actual_mm": [0.0, 0.0, 0.0],
            "expected_mm": expected,
            "tolerance_mm": 0.1,
            "within_tolerance": False,
        }
    bounds = [_shape_bbox(obj.Shape) for obj in head_parts]
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


def _stand_envelope(physical_parts):
    """Full-assembly envelope including stand. Contract: overall depth
    <= STAND.depth_envelope (225 mm) + head depth headroom."""
    stand_parts = _stand_only_parts(physical_parts)
    if not stand_parts:
        return {
            "present": False,
            "actual_depth_mm": 0.0,
            "max_depth_mm": p.STAND["depth_envelope"] + 1.0,
            "within_tolerance": True,
        }
    bounds = [_shape_bbox(obj.Shape) for obj in stand_parts]
    z_min = min(item[2] for item in bounds)
    z_max = max(item[5] for item in bounds)
    actual_depth = z_max - z_min
    return {
        "present": True,
        "actual_depth_mm": actual_depth,
        "max_depth_mm": p.STAND["depth_envelope"] + 1.0,
        "within_tolerance": actual_depth <= p.STAND["depth_envelope"] + 1.0,
        "stand_bbox_mm": [
            min(item[0] for item in bounds),
            min(item[1] for item in bounds),
            z_min,
            max(item[3] for item in bounds),
            max(item[4] for item in bounds),
            z_max,
        ],
    }


def _enclosure_mating_evidence(doc):
    """Verify continuous perimeter z-coverage from front bezel through mid
    frame to rear cover, and record the historic remedied gap."""
    front = doc.getObject("Front_Bezel")
    mid = doc.getObject("Metal_Mid_Frame")
    rear = doc.getObject("Rear_Enclosure")
    parts_present = all(obj is not None for obj in (front, mid, rear))
    if not parts_present:
        return {
            "parts_present": False,
            "front_bezel_z": None,
            "mid_frame_z": None,
            "rear_cover_z": None,
            "z_coverage_continuous": False,
            "front_seam_z": None,
            "rear_seam_z": None,
            "historic_gap_mm": 15.8,
            "remedied_gap_mm": None,
        }
    fb = _shape_bbox(front.Shape)
    mb = _shape_bbox(mid.Shape)
    rb = _shape_bbox(rear.Shape)
    z_tol = 0.05
    front_seam_gap = mb[2] - fb[5]
    rear_seam_gap = rb[2] - mb[5]
    continuous = (
        abs(front_seam_gap) <= z_tol
        and rear_seam_gap <= z_tol  # lap allows negative gap (overlap in z)
        and fb[2] <= z_tol
        and rb[5] >= p.HEAD["depth"] - z_tol
    )
    remedied_gap = max(0.0, front_seam_gap) + max(0.0, rear_seam_gap)
    return {
        "parts_present": True,
        "front_bezel_z": [fb[2], fb[5]],
        "mid_frame_z": [mb[2], mb[5]],
        "rear_cover_z": [rb[2], rb[5]],
        "front_seam_z": mb[2],
        "rear_seam_z": rb[2],
        "z_coverage_continuous": continuous,
        "historic_gap_mm": 15.8,
        "remedied_gap_mm": remedied_gap,
    }


def _rib_host_evidence(doc):
    rear = doc.getObject("Rear_Enclosure")
    if rear is None:
        return {
            "host_present": False,
            "rib_feature_count": 0,
            "rib_feature_ids": [],
            "rib_host_part": None,
            "ok": False,
        }
    ids = [str(name) for name in tuple(getattr(rear, "RibFeatureIds", ()))]
    count = int(getattr(rear, "RibFeatureCount", 0))
    host = str(getattr(rear, "RibHostPart", ""))
    ok = count >= 4 and count == len(ids) and host == "Rear_Enclosure"
    return {
        "host_present": True,
        "rib_feature_count": count,
        "rib_feature_ids": ids,
        "rib_host_part": host,
        "ok": ok,
    }


def _fastener_engagement_evidence(doc):
    entries = []
    ok = True
    z_tol = 0.05
    rear_depth = p.HEAD["depth"]
    rear = doc.getObject("Rear_Enclosure")
    rear_bbox = _shape_bbox(rear.Shape) if rear is not None else None
    for fastener_name, target_name in FASTENER_TARGET_HOSTS.items():
        fastener = doc.getObject(fastener_name)
        target = doc.getObject(target_name)
        if fastener is None or target is None:
            entries.append(
                {
                    "fastener": fastener_name,
                    "target": target_name,
                    "engaged": False,
                    "reason": "missing_part",
                }
            )
            ok = False
            continue
        fb = _shape_bbox(fastener.Shape)
        tb = _shape_bbox(target.Shape)
        # Fastener must enter the target boss in Z and reach at least the
        # rear cover outer face (z >= HEAD depth - z_tol).
        z_into_target = fb[2] <= tb[5] and fb[5] >= tb[2]
        reaches_rear = fb[5] >= rear_depth - z_tol
        # Fastener XY must be within target XY footprint.
        xy_within_target = (
            fb[0] >= tb[0] - 0.5
            and fb[3] <= tb[3] + 0.5
            and fb[1] >= tb[1] - 0.5
            and fb[4] <= tb[4] + 0.5
        )
        # Fastener must pass THROUGH the rear cover (z span crosses rear
        # cover's z range).
        passes_rear_cover = False
        if rear_bbox is not None:
            passes_rear_cover = (
                fb[2] <= rear_bbox[5] and fb[5] >= rear_bbox[5] - z_tol
            )
        engaged = (
            z_into_target
            and reaches_rear
            and xy_within_target
            and passes_rear_cover
        )
        entries.append(
            {
                "fastener": fastener_name,
                "target": target_name,
                "engaged": engaged,
                "z_into_target": z_into_target,
                "reaches_rear": reaches_rear,
                "xy_within_target": xy_within_target,
                "passes_rear_cover": passes_rear_cover,
                "fastener_z": [fb[2], fb[5]],
                "target_z": [tb[2], tb[5]],
            }
        )
        if not engaged:
            ok = False
    return {"entries": entries, "ok": ok}


def _heat_source_evidence(doc):
    """Every HeatSourceID appears exactly once and total = TOTAL_BUDGET_W."""
    per_source = {}
    duplicates = []
    unknown = []
    for obj in doc.Objects:
        source_id = str(getattr(obj, "HeatSourceID", "") or "")
        if not source_id:
            continue
        load = float(getattr(obj, "HeatLoadW", 0.0) or 0.0)
        if source_id in per_source:
            duplicates.append(source_id)
        per_source.setdefault(source_id, []).append(
            {"host": obj.Name, "load_w": load}
        )
        if source_id not in p.HEAT_LOADS_W:
            unknown.append(source_id)
    total = sum(entry["load_w"] for hosts in per_source.values() for entry in hosts)
    expected_ids = set(p.HEAT_LOADS_W)
    actual_ids = set(per_source)
    missing = sorted(expected_ids - actual_ids)
    extra = sorted(actual_ids - expected_ids)
    ok = (
        not duplicates
        and not missing
        and not extra
        and not unknown
        and abs(total - p.TOTAL_BUDGET_W) < 1e-6
    )
    return {
        "per_source": {name: hosts for name, hosts in sorted(per_source.items())},
        "duplicates": sorted(set(duplicates)),
        "missing_expected_ids": missing,
        "extra_ids": extra,
        "total_w": total,
        "expected_total_w": p.TOTAL_BUDGET_W,
        "ok": ok,
    }


def _budget_group_evidence(doc, heat_evidence):
    per_source = heat_evidence["per_source"]
    groups = {}
    for group_name, ids in p.HEAT_BUDGET_GROUPS.items():
        group_sum = 0.0
        for source_id in ids:
            for entry in per_source.get(source_id, []):
                group_sum += entry["load_w"]
        groups[group_name] = group_sum
    panel_ok = abs(groups.get("Panel_Module", 0.0) - p.PANEL_MODULE_BUDGET_W) < 1e-6
    return {"groups": groups, "panel_module_ok": panel_ok}


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
    enclosure_mating = _enclosure_mating_evidence(doc)
    rib_host = _rib_host_evidence(doc)
    fastener_engagement = _fastener_engagement_evidence(doc)
    heat_sources = _heat_source_evidence(doc)
    budget_groups = _budget_group_evidence(doc, heat_sources)
    stand_envelope = _stand_envelope(physical_parts)
    stand_kinematics = _stand_kinematics_contract()

    semantic_count_expected = p.EXPECTED_SEMANTIC_PART_COUNT
    physical_count_expected = p.EXPECTED_PHYSICAL_PART_COUNT
    hard_gates = {
        "semantic_part_count": (
            len(semantic_parts) == semantic_count_expected
            and len(names) == len(set(names))
        ),
        "physical_part_count": physical_geometry["part_count"] == physical_count_expected,
        "eight_group_ownership": not group_ownership["failures"],
        "valid_positive_physical_geometry": not physical_geometry["failures"],
        "complete_metadata": not incomplete_parts and not manufacturing_failures,
        "exact_authorized_contact_matrix": exact_contacts,
        "no_forbidden_overlaps": not forbidden,
        "required_feature_evidence": all(feature_evidence.values()),
        "head_envelope": head_envelope["within_tolerance"],
        "enclosure_mating_continuous": enclosure_mating["z_coverage_continuous"],
        "rib_host_attachment": rib_host["ok"],
        "fastener_engagement": fastener_engagement["ok"],
        "unique_heat_source_mapping_and_budget": heat_sources["ok"],
        "panel_module_budget_conserved": budget_groups["panel_module_ok"],
        "stand_envelope": stand_envelope["within_tolerance"],
        "stand_kinematics_contract": stand_kinematics["ok"],
    }
    overall = "Pass" if all(hard_gates.values()) else "Fail"
    return {
        "status": overall,
        "overall": overall,
        "scope": "HeadOnlyTask8QualityRemediation",
        "limitations": p.PROTOTYPE_LIMITATION,
        "hard_gates": hard_gates,
        "deferred_gates": list(DEFERRED_GATES),
        "overlap_threshold_mm3": OVERLAP_THRESHOLD_MM3,
        "expected_counts": {
            "semantic_parts": semantic_count_expected,
            "physical_parts": physical_count_expected,
            "heat_sources": len(p.HEAT_LOADS_W),
            "total_budget_w": p.TOTAL_BUDGET_W,
        },
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
        "enclosure_mating": enclosure_mating,
        "rib_host": rib_host,
        "fastener_engagement": fastener_engagement,
        "heat_sources": heat_sources,
        "budget_groups": budget_groups,
        "stand_envelope": stand_envelope,
        "stand_kinematics": stand_kinematics,
    }


def _stand_kinematics_contract():
    """Frozen STAND parameter values are the kinematic contract."""
    entries = {key: float(p.STAND[key]) for key in STAND_KINEMATIC_KEYS}
    ok = (
        entries["overall_height_min"] < entries["overall_height_max"]
        and entries["height_travel"] > 0.0
        and entries["tilt_max"] > entries["tilt_min"]
        and entries["swivel_max"] > entries["swivel_min"]
        and entries["depth_envelope"] > 0.0
        and entries["static_margin_min"] > 0.0
        and abs(
            (entries["overall_height_max"] - entries["overall_height_min"])
            - entries["height_travel"]
        ) <= 0.5
    )
    return {"parameters": entries, "ok": ok}


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
