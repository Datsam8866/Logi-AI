"""Stand, base, and kinematic-extrema geometry for Hinoki LOD 3.

Task 6 (2026-09-07): builds the desktop stand under group
06_Stand_Base_Kinematics and the motion-envelope references under
08_Reference_Datums_Keepouts. Nominal posture is neutral
(height=571 mm, tilt=0 deg, swivel=0 deg). Extreme postures are
validated by transforming the head + moving stand parts via
``apply_posture`` and re-running the collision matrix; see
``review_hinoki_lod3.py`` for the eight-posture gate.

Coordinate convention (mirrors the head-only build):
    - X: display width (0..742 mm), 0 is left edge
    - Y: display height (0..492 mm), 0 is head bottom edge
    - Z: display depth (0..62 mm), 0 is front glass, +Z is rear
The stand sits BELOW head bottom (Y<0) and BEHIND head rear (Z>62 for
the column). Base plate footprint is projected onto a desktop plane
below the head at Y = -HEAD_TO_DESK_MM.

LOD 3 stand is an inferred engineering prototype (not manufacturing
release). All dimensions are engineering assumptions ratified against
STAND / BASE contract values in ``hinoki_lod3_parameters.py``.
"""

from __future__ import annotations

import math

import Part
import FreeCAD as App

import hinoki_lod3_parameters as p
from hinoki_lod3_common import (
    add_dimension,
    add_property,
    semantic_part,
    set_external_standard,
    vector,
)


HEAD_TO_DESK_MM = 25.0
BASE_TOP_Y = -HEAD_TO_DESK_MM
BASE_PLATE_THICKNESS = p.BASE["structural_plate_thickness"]
BASE_OUTER_W = p.BASE["width"]
BASE_OUTER_D = p.BASE["depth"]
BASE_INNER_W = p.BASE["structural_plate_width"]
BASE_INNER_D = p.BASE["structural_plate_depth"]
BASE_COVER_HEIGHT = 30.0
BASE_FOOT_RADIUS = 12.0
BASE_FOOT_HEIGHT = 4.0

COLUMN_OD = 60.0
COLUMN_WALL = 3.0
COLUMN_TOP_Y_NOMINAL = 320.0
COLUMN_Z_CENTRE = 130.0

LIFT_CARRIAGE_W = 80.0
LIFT_CARRIAGE_H = 100.0
LIFT_CARRIAGE_D = 80.0
LIFT_TRAVEL = p.STAND["height_travel"]

ASSIST_GAS_SPRING_OD = 20.0
ASSIST_GAS_SPRING_LEN = 180.0

DUAL_GUIDE_WIDTH = 8.0
DUAL_GUIDE_DEPTH = 8.0
DUAL_GUIDE_LENGTH = LIFT_TRAVEL + 40.0
DUAL_GUIDE_OFFSET_X = 22.0

YOKE_W = 120.0
YOKE_H = 60.0
YOKE_D = 70.0

VESA_MOUNT_PLATE_W = p.BASE["vesa_plate_width"]
VESA_MOUNT_PLATE_H = p.BASE["vesa_plate_height"]
VESA_MOUNT_PLATE_T = p.BASE["vesa_plate_thickness"]

# Nominal posture (mid-lift, no tilt/swivel).
NOMINAL_LIFT_OFFSET_MM = 0.0
NOMINAL_TILT_DEG = 0.0
NOMINAL_SWIVEL_DEG = 0.0

# Static-margin CoM assumption (LOD 3): treat head as uniform mass 8 kg
# and stand column/base as heavy 12 kg concentrated at column axis.
HEAD_MASS_KG = 8.0
STAND_MASS_KG = 12.0
HEAD_COM_LOCAL = (p.HEAD["width"] / 2.0, p.HEAD["height"] / 2.0, p.HEAD["depth"] / 2.0)
STAND_COM_LOCAL = (p.HEAD["width"] / 2.0, -HEAD_TO_DESK_MM - BASE_PLATE_THICKNESS / 2.0, COLUMN_Z_CENTRE)

# Fixed vs moving parts (used by apply_posture).
STAND_FIXED_PART_NAMES = (
    "Base_Cover",
    "Base_Steel_Plate",
    "Base_Feet",
    "Column_Tube",
    "Column_Base_Bezel",
)
STAND_MOVING_PART_NAMES = (
    "Lift_Carriage",
    "Dual_Guide_Rails",
    "Assist_Gas_Spring",
    "Yoke_Arm",
    "VESA_Mount_Plate",
)


def _column_x():
    return p.HEAD["width"] / 2.0


def _stand_metadata(part_id, name, material, source_class="EngineeringAssumption",
                    source_reference=None, external_standard_id=""):
    return p.part_metadata(
        part_id=part_id,
        part_name=name,
        parent_assembly="06_Stand_Base_Kinematics",
        material_intent=material,
        source_class=source_class,
        source_reference=source_reference or (
            "Task 6 stand/base LOD 3 engineering assumption; not "
            "Dixie-derived (Dixie 65-inch is wall-mount + AV bar not a "
            "desktop stand). Kinematic contract per STAND/BASE frozen "
            "values in hinoki_lod3_parameters.py."
        ),
        confidence="Medium",
        thermal_disposition="Suppress",
        external_standard_id=external_standard_id,
    )


def _reference_metadata(part_id, name, source_reference):
    return p.part_metadata(
        part_id=part_id,
        part_name=name,
        parent_assembly="08_Reference_Datums_Keepouts",
        material_intent="Motion envelope reference",
        source_class="EngineeringAssumption",
        source_reference=source_reference,
        confidence="Medium",
        thermal_disposition="Suppress",
    )


def build_stand(doc, groups):
    """Build nominal-posture stand parts + motion-envelope references.

    Returns the list of semantic-part objects added. Kinematic transforms
    live in ``apply_posture`` (below); the nominal build uses lift=0,
    tilt=0, swivel=0.
    """
    stand_group = groups["06_Stand_Base_Kinematics"]
    reference_group = groups["08_Reference_Datums_Keepouts"]
    parts = []

    col_x = _column_x()
    col_top_y = COLUMN_TOP_Y_NOMINAL
    col_bottom_y = BASE_TOP_Y

    # Base cover: 520 x 225 mm plastic housing 30 mm tall, sitting on the
    # desk plane at Y = BASE_TOP_Y - BASE_COVER_HEIGHT.
    base_cover_shape = Part.makeBox(
        BASE_OUTER_W, BASE_COVER_HEIGHT, BASE_OUTER_D,
        vector(
            _column_x() - BASE_OUTER_W / 2.0,
            BASE_TOP_Y - BASE_COVER_HEIGHT,
            COLUMN_Z_CENTRE - BASE_OUTER_D / 2.0,
        ),
    )
    base_cover = semantic_part(
        doc, stand_group,
        "Base_Cover", "Base Cover (Plastic Housing)",
        base_cover_shape,
        _stand_metadata(
            "HNK-ST-001", "Base_Cover", p.MATERIAL_INTENTS["Housing_Polymer"]
        ),
    )
    add_dimension(base_cover, "OuterWidth", BASE_OUTER_W)
    add_dimension(base_cover, "OuterDepth", BASE_OUTER_D)
    add_property(base_cover, "App::PropertyStringList",
                 "AuthorizedContactTargets", ["Base_Steel_Plate"])
    parts.append(base_cover)

    # Steel structural plate: 500 x 205 mm, 6 mm thick, buried inside the
    # base cover for stiffness.
    steel_plate_shape = Part.makeBox(
        BASE_INNER_W, BASE_PLATE_THICKNESS, BASE_INNER_D,
        vector(
            col_x - BASE_INNER_W / 2.0,
            BASE_TOP_Y - BASE_COVER_HEIGHT + 12.0,
            COLUMN_Z_CENTRE - BASE_INNER_D / 2.0,
        ),
    )
    steel_plate = semantic_part(
        doc, stand_group,
        "Base_Steel_Plate", "Base Steel Structural Plate",
        steel_plate_shape,
        _stand_metadata(
            "HNK-ST-002", "Base_Steel_Plate", p.MATERIAL_INTENTS["Stand_Structure"]
        ),
    )
    add_dimension(steel_plate, "Thickness", BASE_PLATE_THICKNESS)
    add_property(steel_plate, "App::PropertyStringList",
                 "AuthorizedContactTargets", ["Base_Cover"])
    parts.append(steel_plate)

    # Four rubber feet arranged near base cover corners.
    foot_positions = (
        (col_x - BASE_OUTER_W / 2.0 + BASE_FOOT_RADIUS + 5.0,
         COLUMN_Z_CENTRE - BASE_OUTER_D / 2.0 + BASE_FOOT_RADIUS + 5.0),
        (col_x + BASE_OUTER_W / 2.0 - BASE_FOOT_RADIUS - 5.0,
         COLUMN_Z_CENTRE - BASE_OUTER_D / 2.0 + BASE_FOOT_RADIUS + 5.0),
        (col_x - BASE_OUTER_W / 2.0 + BASE_FOOT_RADIUS + 5.0,
         COLUMN_Z_CENTRE + BASE_OUTER_D / 2.0 - BASE_FOOT_RADIUS - 5.0),
        (col_x + BASE_OUTER_W / 2.0 - BASE_FOOT_RADIUS - 5.0,
         COLUMN_Z_CENTRE + BASE_OUTER_D / 2.0 - BASE_FOOT_RADIUS - 5.0),
    )
    foot_shapes = []
    for fx, fz in foot_positions:
        foot_cyl = Part.makeCylinder(
            BASE_FOOT_RADIUS, BASE_FOOT_HEIGHT,
            vector(fx, BASE_TOP_Y - BASE_COVER_HEIGHT - BASE_FOOT_HEIGHT, fz),
            vector(0.0, 1.0, 0.0),
        )
        foot_shapes.append(foot_cyl)
    feet_compound = Part.makeCompound(foot_shapes)
    base_feet = semantic_part(
        doc, stand_group,
        "Base_Feet", "Base Rubber Feet (x4)",
        feet_compound,
        _stand_metadata(
            "HNK-ST-003", "Base_Feet", "Molded rubber; Shore A 70 equivalent"
        ),
    )
    add_dimension(base_feet, "FootDiameter", BASE_FOOT_RADIUS * 2.0)
    parts.append(base_feet)

    # Column tube: hollow steel tube rising from base cover top to
    # nominal column-top height.
    column_len = col_top_y - col_bottom_y
    column_outer = Part.makeCylinder(
        COLUMN_OD / 2.0, column_len,
        vector(col_x, col_bottom_y, COLUMN_Z_CENTRE),
        vector(0.0, 1.0, 0.0),
    )
    column_inner = Part.makeCylinder(
        COLUMN_OD / 2.0 - COLUMN_WALL, column_len + 0.2,
        vector(col_x, col_bottom_y - 0.1, COLUMN_Z_CENTRE),
        vector(0.0, 1.0, 0.0),
    )
    column_shape = column_outer.cut(column_inner)
    column = semantic_part(
        doc, stand_group,
        "Column_Tube", "Column Tube (Steel)",
        column_shape,
        _stand_metadata(
            "HNK-ST-004", "Column_Tube", p.MATERIAL_INTENTS["Stand_Structure"]
        ),
    )
    add_dimension(column, "OuterDiameter", COLUMN_OD)
    add_dimension(column, "WallThickness", COLUMN_WALL)
    parts.append(column)

    # Decorative base bezel between column tube and base cover.
    bezel_shape = Part.makeCylinder(
        COLUMN_OD / 2.0 + 8.0, 20.0,
        vector(col_x, col_bottom_y, COLUMN_Z_CENTRE),
        vector(0.0, 1.0, 0.0),
    ).cut(Part.makeCylinder(
        COLUMN_OD / 2.0 + 0.5, 20.4,
        vector(col_x, col_bottom_y - 0.1, COLUMN_Z_CENTRE),
        vector(0.0, 1.0, 0.0),
    ))
    bezel = semantic_part(
        doc, stand_group,
        "Column_Base_Bezel", "Column Base Bezel (Trim Ring)",
        bezel_shape,
        _stand_metadata(
            "HNK-ST-005", "Column_Base_Bezel", p.MATERIAL_INTENTS["Housing_Polymer"]
        ),
    )
    parts.append(bezel)

    # Lift carriage: sleeve wrapping the column at nominal mid-height.
    lift_y_nominal = (col_top_y - LIFT_CARRIAGE_H / 2.0
                      - LIFT_TRAVEL / 2.0)
    carriage_outer = Part.makeBox(
        LIFT_CARRIAGE_W, LIFT_CARRIAGE_H, LIFT_CARRIAGE_D,
        vector(col_x - LIFT_CARRIAGE_W / 2.0, lift_y_nominal,
               COLUMN_Z_CENTRE - LIFT_CARRIAGE_D / 2.0),
    )
    carriage_bore = Part.makeCylinder(
        COLUMN_OD / 2.0 + 1.0, LIFT_CARRIAGE_H + 0.4,
        vector(col_x, lift_y_nominal - 0.2, COLUMN_Z_CENTRE),
        vector(0.0, 1.0, 0.0),
    )
    lift_shape = carriage_outer.cut(carriage_bore)
    lift = semantic_part(
        doc, stand_group,
        "Lift_Carriage", "Lift Carriage (Height-Adjust Sleeve)",
        lift_shape,
        _stand_metadata(
            "HNK-ST-006", "Lift_Carriage", p.MATERIAL_INTENTS["Die_Cast_Joint"]
        ),
    )
    add_dimension(lift, "TravelRange", LIFT_TRAVEL)
    add_property(lift, "App::PropertyStringList",
                 "AuthorizedContactTargets", ["Yoke_Arm"])
    parts.append(lift)

    # Dual guide rails: two vertical rectangular rails inside the column,
    # constrain the lift carriage against rotation and side load.
    guide_shapes = []
    for offset_sign in (-1.0, +1.0):
        guide_shapes.append(Part.makeBox(
            DUAL_GUIDE_WIDTH, DUAL_GUIDE_LENGTH, DUAL_GUIDE_DEPTH,
            vector(
                col_x + offset_sign * DUAL_GUIDE_OFFSET_X - DUAL_GUIDE_WIDTH / 2.0,
                col_bottom_y + 30.0,
                COLUMN_Z_CENTRE - DUAL_GUIDE_DEPTH / 2.0,
            ),
        ))
    guides = semantic_part(
        doc, stand_group,
        "Dual_Guide_Rails", "Dual Vertical Guide Rails",
        Part.makeCompound(guide_shapes),
        _stand_metadata(
            "HNK-ST-007", "Dual_Guide_Rails", p.MATERIAL_INTENTS["Stand_Structure"]
        ),
    )
    add_dimension(guides, "GuideLength", DUAL_GUIDE_LENGTH)
    parts.append(guides)

    # Assist gas spring (proxy solid) inside the column cavity, providing
    # lift assist over the travel range.
    assist_shape = Part.makeCylinder(
        ASSIST_GAS_SPRING_OD / 2.0, ASSIST_GAS_SPRING_LEN,
        vector(col_x, col_bottom_y + 40.0, COLUMN_Z_CENTRE),
        vector(0.0, 1.0, 0.0),
    )
    assist = semantic_part(
        doc, stand_group,
        "Assist_Gas_Spring", "Assist Gas Spring (Proxy)",
        assist_shape,
        _stand_metadata(
            "HNK-ST-008", "Assist_Gas_Spring", "Nitrogen gas spring proxy",
            external_standard_id="Suspa 16-4 200N class (representative)",
        ),
    )
    parts.append(assist)

    # Yoke arm: bridges lift carriage top face to the VESA mount plate at
    # head rear.
    yoke_y = lift_y_nominal + LIFT_CARRIAGE_H - YOKE_H / 2.0 - 5.0
    yoke_z_front = 62.0 + VESA_MOUNT_PLATE_T
    yoke_z_back = COLUMN_Z_CENTRE - COLUMN_OD / 2.0 - 5.0
    yoke_shape = Part.makeBox(
        YOKE_W, YOKE_H, yoke_z_back - yoke_z_front,
        vector(col_x - YOKE_W / 2.0, yoke_y, yoke_z_front),
    )
    yoke = semantic_part(
        doc, stand_group,
        "Yoke_Arm", "Yoke Arm (Tilt Pivot)",
        yoke_shape,
        _stand_metadata(
            "HNK-ST-009", "Yoke_Arm", p.MATERIAL_INTENTS["Die_Cast_Joint"]
        ),
    )
    add_dimension(yoke, "TiltRangeDeg",
                  p.STAND["tilt_max"] - p.STAND["tilt_min"])
    add_property(yoke, "App::PropertyStringList",
                 "AuthorizedContactTargets", ["Lift_Carriage"])
    parts.append(yoke)

    # VESA mount plate 140x140x4 mm; the four VESA_Boss cylinders on the
    # head rear (already in the head build) engage this plate. Position
    # the plate flush with head rear face (Z=62) at VESA cluster centre.
    vesa_center_x = sum(v[0] for v in p.VESA_MOUNT_POINTS) / 4.0
    vesa_center_y = sum(v[1] for v in p.VESA_MOUNT_POINTS) / 4.0
    vesa_plate_shape = Part.makeBox(
        VESA_MOUNT_PLATE_W, VESA_MOUNT_PLATE_H, VESA_MOUNT_PLATE_T,
        vector(
            vesa_center_x - VESA_MOUNT_PLATE_W / 2.0,
            vesa_center_y - VESA_MOUNT_PLATE_H / 2.0,
            p.HEAD["depth"],
        ),
    )
    vesa_plate = semantic_part(
        doc, stand_group,
        "VESA_Mount_Plate", "VESA Mount Plate (140x140x4)",
        vesa_plate_shape,
        _stand_metadata(
            "HNK-ST-010", "VESA_Mount_Plate",
            p.MATERIAL_INTENTS["Sheet_Bracket_Shield"],
            external_standard_id=(
                "VESA MIS-D 100 (100x100 mm) mating plate; 140x140 mm "
                "footprint per Hinoki STAND contract"
            ),
        ),
    )
    add_dimension(vesa_plate, "PlateThickness", VESA_MOUNT_PLATE_T)
    # Head-to-stand structural continuity is provided by the 4 M4 VESA
    # fasteners clamping the plate + rear cover + VESA_Boss stack.
    # Plate rests plane-flush on rear cover outer face at z=62; no
    # volumetric overlap is declared (fasteners already cover the load
    # path via fastener_engagement gate).
    add_property(vesa_plate, "App::PropertyString", "MatingFace",
                 "Rear_Enclosure outer @ z=62; clamped by M4 VESA fasteners")
    parts.append(vesa_plate)

    # ---- Motion envelope references (08_Reference_Datums_Keepouts) ----
    _add_motion_references(doc, reference_group, col_x, col_top_y)

    return parts


def _add_motion_references(doc, reference_group, col_x, col_top_y):
    """Add three swept motion envelopes as reference-only bodies."""
    # Height travel envelope: swept volume of VESA mount plate over 100
    # mm of vertical travel.
    height_env = Part.makeBox(
        VESA_MOUNT_PLATE_W + 20.0, LIFT_TRAVEL + VESA_MOUNT_PLATE_H,
        VESA_MOUNT_PLATE_T + 10.0,
        vector(
            col_x - (VESA_MOUNT_PLATE_W + 20.0) / 2.0,
            (col_top_y - LIFT_TRAVEL) - VESA_MOUNT_PLATE_H / 2.0,
            p.HEAD["depth"] - 3.0,
        ),
    )
    height_env_obj = semantic_part(
        doc, reference_group,
        "Height_Travel_Envelope", "Height Travel Envelope (100 mm)",
        height_env,
        _reference_metadata(
            "HNK-KO-301", "Height_Travel_Envelope",
            "Design section 6.6 stand height_travel = 100 mm [A-LOD3-ST-001]",
        ),
    )
    add_property(height_env_obj, "App::PropertyBool",
                 "PhysicalCollision", False)
    add_property(height_env_obj, "App::PropertyString",
                 "GeometryRole", "MotionStateReference")

    # Tilt envelope: fan-shaped keepout around VESA plate rotation axis.
    tilt_range = p.STAND["tilt_max"] - p.STAND["tilt_min"]
    tilt_env = Part.makeBox(
        VESA_MOUNT_PLATE_W + 20.0,
        VESA_MOUNT_PLATE_H + 40.0,
        VESA_MOUNT_PLATE_T + 40.0,
        vector(
            col_x - (VESA_MOUNT_PLATE_W + 20.0) / 2.0,
            col_top_y - LIFT_TRAVEL / 2.0 - (VESA_MOUNT_PLATE_H + 40.0) / 2.0,
            p.HEAD["depth"] - 20.0,
        ),
    )
    tilt_env_obj = semantic_part(
        doc, reference_group,
        "Tilt_Motion_Envelope", "Tilt Motion Envelope (+/-10 deg)",
        tilt_env,
        _reference_metadata(
            "HNK-KO-302", "Tilt_Motion_Envelope",
            "Design section 6.6 stand tilt = {}..{} deg [A-LOD3-ST-002]".format(
                p.STAND["tilt_min"], p.STAND["tilt_max"]
            ),
        ),
    )
    add_property(tilt_env_obj, "App::PropertyBool",
                 "PhysicalCollision", False)
    add_property(tilt_env_obj, "App::PropertyString",
                 "GeometryRole", "MotionStateReference")
    add_dimension(tilt_env_obj, "TiltRangeDeg", tilt_range)

    # Swivel envelope: horizontal fan below column top capturing +/-20 deg.
    swivel_range = p.STAND["swivel_max"] - p.STAND["swivel_min"]
    swivel_r = 250.0
    swivel_env = Part.makeCylinder(
        swivel_r, 10.0,
        vector(col_x, BASE_TOP_Y - 5.0, COLUMN_Z_CENTRE),
        vector(0.0, 1.0, 0.0),
    )
    swivel_env_obj = semantic_part(
        doc, reference_group,
        "Swivel_Motion_Envelope", "Swivel Motion Envelope (+/-20 deg)",
        swivel_env,
        _reference_metadata(
            "HNK-KO-303", "Swivel_Motion_Envelope",
            "Design section 6.6 stand swivel = {}..{} deg [A-LOD3-ST-003]".format(
                p.STAND["swivel_min"], p.STAND["swivel_max"]
            ),
        ),
    )
    add_property(swivel_env_obj, "App::PropertyBool",
                 "PhysicalCollision", False)
    add_property(swivel_env_obj, "App::PropertyString",
                 "GeometryRole", "MotionStateReference")
    add_dimension(swivel_env_obj, "SwivelRangeDeg", swivel_range)


# ------------------------------------------------------------------
# Kinematic transforms and posture validation
# ------------------------------------------------------------------

# Head + VESA plate + yoke + lift + assist all move together (up/down for
# height, rotate around tilt/swivel axes). Column, base cover, steel
# plate, feet, bezel stay fixed.


def _head_semantic_names(doc):
    """Names of every physical semantic part attached to the head (i.e.
    everything NOT in the stand fixed set and NOT a reference-only
    object). These are the bodies that move with a posture change."""
    excluded_assemblies = {"06_Stand_Base_Kinematics", "08_Reference_Datums_Keepouts"}
    return [
        obj.Name for obj in doc.Objects
        if getattr(obj, "IsSemanticPart", False)
        and getattr(obj, "ParentAssembly", "") not in excluded_assemblies
    ]


def _moving_names(doc):
    """Head parts + stand moving parts under posture transform."""
    return list(_head_semantic_names(doc)) + list(STAND_MOVING_PART_NAMES)


def apply_posture(doc, height_offset_mm, tilt_deg, swivel_deg):
    """Apply a posture transform to every moving body in-place.

    ``height_offset_mm`` is the signed offset from nominal mid-lift
    (+50 mm = raised, -50 mm = lowered). ``tilt_deg`` rotates the head
    stack around the horizontal X axis through the VESA plate mount
    centre (Y at column top - LIFT_TRAVEL/2, Z at head rear). ``swivel_deg``
    rotates the entire moving assembly around the vertical Y axis
    passing through the column centre at the base plane.

    Returns the Placement objects assigned so callers can inspect.
    """
    lift_pivot_y = COLUMN_TOP_Y_NOMINAL - LIFT_TRAVEL / 2.0
    tilt_axis_point = App.Vector(_column_x(),
                                 lift_pivot_y,
                                 p.HEAD["depth"])
    tilt_axis_dir = App.Vector(1.0, 0.0, 0.0)
    swivel_axis_point = App.Vector(_column_x(), BASE_TOP_Y, COLUMN_Z_CENTRE)
    swivel_axis_dir = App.Vector(0.0, 1.0, 0.0)

    tilt_rot = App.Rotation(tilt_axis_dir, tilt_deg)
    swivel_rot = App.Rotation(swivel_axis_dir, swivel_deg)

    tilt_placement = App.Placement(tilt_axis_point, tilt_rot,
                                   App.Vector(0, 0, 0))
    # Reduce tilt to a Placement centred at origin then reapplied around
    # the tilt axis point via translate.
    tilt_placement = App.Placement()
    tilt_placement.Rotation = tilt_rot
    tilt_placement.Base = tilt_axis_point - tilt_rot.multVec(tilt_axis_point)

    swivel_placement = App.Placement()
    swivel_placement.Rotation = swivel_rot
    swivel_placement.Base = swivel_axis_point - swivel_rot.multVec(swivel_axis_point)

    height_placement = App.Placement()
    height_placement.Base = App.Vector(0, height_offset_mm, 0)

    # Combined posture transform for head + top-of-stand moving parts:
    # first apply tilt (about VESA mount), then swivel (about base column
    # vertical), then height translation.
    posture = swivel_placement.multiply(height_placement.multiply(tilt_placement))

    placements = {}
    for name in _moving_names(doc):
        obj = doc.getObject(name)
        if obj is None:
            continue
        obj.Placement = posture
        placements[name] = obj.Placement
    doc.recompute()
    return placements


def restore_nominal(doc):
    """Reset every moving body to identity Placement."""
    identity = App.Placement()
    for name in _moving_names(doc):
        obj = doc.getObject(name)
        if obj is not None:
            obj.Placement = identity
    doc.recompute()


def head_overall_height_mm(doc):
    """Head top edge Y after current posture; used for 521..621 mm gate.

    Overall height = distance from desk plane (Y = BASE_TOP_Y -
    BASE_COVER_HEIGHT - BASE_FOOT_HEIGHT) to head top edge Y_max.
    """
    top_y = None
    for name in _head_semantic_names(doc):
        obj = doc.getObject(name)
        if obj is None or obj.Shape is None or obj.Shape.isNull():
            continue
        y_max = float(obj.Shape.BoundBox.YMax)
        if top_y is None or y_max > top_y:
            top_y = y_max
    if top_y is None:
        return 0.0
    desk_y = BASE_TOP_Y - BASE_COVER_HEIGHT - BASE_FOOT_HEIGHT
    return top_y - desk_y


def projected_com_support_margin_mm(doc):
    """Return the smaller of X/Z projected CoM support margins in mm.

    CoM is a mass-weighted combination of the head shape centres and the
    stand column centre. Support polygon is the base cover XZ footprint.
    """
    head_cx = HEAD_COM_LOCAL[0]
    head_cy = HEAD_COM_LOCAL[1]
    head_cz = HEAD_COM_LOCAL[2]
    stand_cx = STAND_COM_LOCAL[0]
    stand_cz = STAND_COM_LOCAL[2]

    # Sample head COM after current posture: use bbox mid of a physical
    # head part (Rear_Enclosure is a good proxy for centroid).
    rear = doc.getObject("Rear_Enclosure")
    if rear is not None and rear.Shape is not None:
        bb = rear.Shape.BoundBox
        head_cx = (bb.XMin + bb.XMax) / 2.0
        head_cz = (bb.ZMin + bb.ZMax) / 2.0

    total_mass = HEAD_MASS_KG + STAND_MASS_KG
    com_x = (HEAD_MASS_KG * head_cx + STAND_MASS_KG * stand_cx) / total_mass
    com_z = (HEAD_MASS_KG * head_cz + STAND_MASS_KG * stand_cz) / total_mass

    col_x = _column_x()
    base_x_min = col_x - BASE_OUTER_W / 2.0
    base_x_max = col_x + BASE_OUTER_W / 2.0
    base_z_min = COLUMN_Z_CENTRE - BASE_OUTER_D / 2.0
    base_z_max = COLUMN_Z_CENTRE + BASE_OUTER_D / 2.0

    margin_x = min(com_x - base_x_min, base_x_max - com_x)
    margin_z = min(com_z - base_z_min, base_z_max - com_z)
    return min(margin_x, margin_z)


def posture_extrema():
    """Eight-corner (min/max)^3 posture combinations."""
    return [
        (h, t, s)
        for h in (-LIFT_TRAVEL / 2.0, +LIFT_TRAVEL / 2.0)
        for t in (p.STAND["tilt_min"], p.STAND["tilt_max"])
        for s in (p.STAND["swivel_min"], p.STAND["swivel_max"])
    ]
