"""Stand, base, and kinematic-extrema geometry for Hinoki LOD 3.

Iter 8 (2026-09-07): stand-to-screen interface redesign per Ateam
Round 1 findings. Reference: Apple Studio Display column-integrated
pattern + Cisco Desk Pro yoke-wrap-column geometry. Fixes iter 7's
"floating yoke", "misaligned tilt axis", "sticker VESA plate" and
"bare cylindrical column" complaints.

Changes vs iter 7:
    - Column moved forward Z 130 -> 106 (front face just touches VESA
      plate back z=66) and enlarged D60 -> D80 for 32-inch visual
      balance (Apple Studio Display column class).
    - Yoke redesigned from 120x60x40 dead cube into a 160x140x44
      U-bracket that spans the full VESA plate height (Y 176..316,
      centred on VESA cluster mid Y=246 -- fixes iter 7's 69 mm tilt-
      axis offset) and wraps the column front half via boolean cut.
      Boolean fusion eliminates the iter 7 5 mm floating gap.
    - New Tilt_Trunnion (visible D25 x 140 mm cylinder along the X
      tilt axis through yoke and VESA plate mid) makes the +/-10 deg
      pivot mechanically obvious.
    - Base deepened 225 -> 280 mm for 32-inch stability envelope
      (Apple Studio Display base ~260 mm depth reference).
    - Cable_Channel (28 x 12 x 320 mm rectangular slot proxy) fused
      into the column rear face representing cable pass-through from
      head bottom I/O to base rear exit.

Coordinate convention (mirrors the head-only build):
    - X: display width (0..742 mm), 0 is left edge
    - Y: display height (0..492 mm), 0 is head bottom edge
    - Z: display depth (0..62 mm), 0 is front glass, +Z is rear

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
BASE_COVER_HEIGHT = 32.0
BASE_FOOT_RADIUS = 12.0
BASE_FOOT_HEIGHT = 4.0

# Iter 8: column moved forward + enlarged; base deepened.
COLUMN_OD = 80.0
COLUMN_WALL = 3.0
COLUMN_TOP_Y_NOMINAL = 320.0
COLUMN_Z_CENTRE = 106.0

LIFT_SLEEVE_OD = 88.0
LIFT_SLEEVE_ID = 82.0
LIFT_CARRIAGE_H = 100.0
LIFT_CARRIAGE_Y_NOMINAL_BOTTOM = 76.0
LIFT_TRAVEL = p.STAND["height_travel"]

ASSIST_GAS_SPRING_OD = 20.0
ASSIST_GAS_SPRING_LEN = 180.0

DUAL_GUIDE_WIDTH = 8.0
DUAL_GUIDE_DEPTH = 8.0
DUAL_GUIDE_LENGTH = LIFT_TRAVEL + 40.0
DUAL_GUIDE_OFFSET_X = 28.0

# Iter 8: yoke wraps column front and centres on VESA cluster Y.
YOKE_W = 160.0
YOKE_H = 140.0
YOKE_D_FRONT_Z = 66.0
YOKE_D_BACK_Z = 148.0
YOKE_WALL = 12.0
YOKE_COLUMN_HOLE_CLEAR = 1.0

VESA_MOUNT_PLATE_W = p.BASE["vesa_plate_width"]
VESA_MOUNT_PLATE_H = p.BASE["vesa_plate_height"]
VESA_MOUNT_PLATE_T = p.BASE["vesa_plate_thickness"]

# Iter 8: visible tilt trunnion along X axis through yoke, aligned to
# VESA cluster mid Y = 246.
TILT_TRUNNION_OD = 25.0
TILT_TRUNNION_LEN = 148.0
TILT_TRUNNION_Y = 246.0
TILT_TRUNNION_Z = 106.0

# Iter 8: cable channel rectangular slot on column rear face.
CABLE_CHANNEL_W = 24.0
CABLE_CHANNEL_H = 300.0
CABLE_CHANNEL_D = 10.0

NOMINAL_LIFT_OFFSET_MM = 0.0
NOMINAL_TILT_DEG = 0.0
NOMINAL_SWIVEL_DEG = 0.0

HEAD_MASS_KG = 8.0
STAND_MASS_KG = 12.0
HEAD_COM_LOCAL = (p.HEAD["width"] / 2.0, p.HEAD["height"] / 2.0, p.HEAD["depth"] / 2.0)
STAND_COM_LOCAL = (p.HEAD["width"] / 2.0, -HEAD_TO_DESK_MM - BASE_PLATE_THICKNESS / 2.0, COLUMN_Z_CENTRE)

STAND_FIXED_PART_NAMES = (
    "Base_Cover",
    "Base_Steel_Plate",
    "Base_Feet",
    "Column_Tube",
    "Column_Base_Bezel",
    "Cable_Channel",
)
STAND_MOVING_PART_NAMES = (
    "Lift_Carriage",
    "Dual_Guide_Rails",
    "Assist_Gas_Spring",
    "Yoke_Bracket",
    "Tilt_Trunnion",
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
            "Task 6 stand/base LOD 3 engineering assumption; iter 8 "
            "column-integrated pattern per Apple Studio Display + Cisco "
            "Desk Pro market reference (Ateam Round 1)."
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


def _yoke_shape(col_x):
    """Build the iter 8 U-bracket yoke that wraps the column front half.

    Outer envelope 160 x 140 x 82 mm at (col_x - 80, 176, 66)..
    (col_x + 80, 316, 148). Inner column cavity is a cylinder along Y
    at the column axis with radius COLUMN_OD/2 + clearance so the yoke
    can slide onto the column tube.
    """
    outer = Part.makeBox(
        YOKE_W, YOKE_H, YOKE_D_BACK_Z - YOKE_D_FRONT_Z,
        vector(col_x - YOKE_W / 2.0, 176.0, YOKE_D_FRONT_Z),
    )
    column_cavity = Part.makeCylinder(
        COLUMN_OD / 2.0 + YOKE_COLUMN_HOLE_CLEAR,
        YOKE_H + 4.0,
        vector(col_x, 174.0, COLUMN_Z_CENTRE),
        vector(0.0, 1.0, 0.0),
    )
    hollow = Part.makeBox(
        YOKE_W - 2.0 * YOKE_WALL,
        YOKE_H - 2.0 * YOKE_WALL,
        YOKE_D_BACK_Z - YOKE_D_FRONT_Z - 2.0 * YOKE_WALL,
        vector(
            col_x - YOKE_W / 2.0 + YOKE_WALL,
            176.0 + YOKE_WALL,
            YOKE_D_FRONT_Z + YOKE_WALL,
        ),
    )
    trunnion_hole = Part.makeCylinder(
        TILT_TRUNNION_OD / 2.0 + 0.4,
        TILT_TRUNNION_LEN + 4.0,
        vector(col_x - (TILT_TRUNNION_LEN + 4.0) / 2.0,
               TILT_TRUNNION_Y, TILT_TRUNNION_Z),
        vector(1.0, 0.0, 0.0),
    )
    return outer.cut(column_cavity).cut(hollow).cut(trunnion_hole)


def build_stand(doc, groups):
    """Iter 8 stand: column-integrated, yoke wraps column, visible
    tilt trunnion, deepened base."""
    stand_group = groups["06_Stand_Base_Kinematics"]
    reference_group = groups["08_Reference_Datums_Keepouts"]
    parts = []

    col_x = _column_x()
    col_top_y = COLUMN_TOP_Y_NOMINAL
    col_bottom_y = BASE_TOP_Y

    base_cover_shape = Part.makeBox(
        BASE_OUTER_W, BASE_COVER_HEIGHT, BASE_OUTER_D,
        vector(
            col_x - BASE_OUTER_W / 2.0,
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

    foot_positions = (
        (col_x - BASE_OUTER_W / 2.0 + BASE_FOOT_RADIUS + 6.0,
         COLUMN_Z_CENTRE - BASE_OUTER_D / 2.0 + BASE_FOOT_RADIUS + 6.0),
        (col_x + BASE_OUTER_W / 2.0 - BASE_FOOT_RADIUS - 6.0,
         COLUMN_Z_CENTRE - BASE_OUTER_D / 2.0 + BASE_FOOT_RADIUS + 6.0),
        (col_x - BASE_OUTER_W / 2.0 + BASE_FOOT_RADIUS + 6.0,
         COLUMN_Z_CENTRE + BASE_OUTER_D / 2.0 - BASE_FOOT_RADIUS - 6.0),
        (col_x + BASE_OUTER_W / 2.0 - BASE_FOOT_RADIUS - 6.0,
         COLUMN_Z_CENTRE + BASE_OUTER_D / 2.0 - BASE_FOOT_RADIUS - 6.0),
    )
    foot_shapes = [
        Part.makeCylinder(
            BASE_FOOT_RADIUS, BASE_FOOT_HEIGHT,
            vector(fx, BASE_TOP_Y - BASE_COVER_HEIGHT - BASE_FOOT_HEIGHT, fz),
            vector(0.0, 1.0, 0.0),
        )
        for fx, fz in foot_positions
    ]
    base_feet = semantic_part(
        doc, stand_group,
        "Base_Feet", "Base Rubber Feet (x4)",
        Part.makeCompound(foot_shapes),
        _stand_metadata(
            "HNK-ST-003", "Base_Feet", "Molded rubber; Shore A 70 equivalent"
        ),
    )
    add_dimension(base_feet, "FootDiameter", BASE_FOOT_RADIUS * 2.0)
    parts.append(base_feet)

    # Column tube (iter 8 D80, moved forward Z=106).
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

    bezel_shape = Part.makeCylinder(
        COLUMN_OD / 2.0 + 10.0, 22.0,
        vector(col_x, col_bottom_y, COLUMN_Z_CENTRE),
        vector(0.0, 1.0, 0.0),
    ).cut(Part.makeCylinder(
        COLUMN_OD / 2.0 + 0.5, 22.4,
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

    # Lift carriage (iter 8 cylindrical sleeve OD96/ID82 around D80
    # column). Positioned BELOW yoke Y range so the two moving parts
    # do not collide even after kinematic transforms.
    lift_y_nominal = LIFT_CARRIAGE_Y_NOMINAL_BOTTOM
    carriage_outer = Part.makeCylinder(
        LIFT_SLEEVE_OD / 2.0, LIFT_CARRIAGE_H,
        vector(col_x, lift_y_nominal, COLUMN_Z_CENTRE),
        vector(0.0, 1.0, 0.0),
    )
    carriage_bore = Part.makeCylinder(
        LIFT_SLEEVE_ID / 2.0, LIFT_CARRIAGE_H + 0.4,
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
    # Lift sleeve slides on column with 1 mm radial clearance; contact
    # is with guide rails inside column (LOD 3 abstract, not declared).
    parts.append(lift)

    # Dual guide rails (unchanged concept, inside column).
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

    # Iter 8: Yoke_Bracket (replaces iter 7 Yoke_Arm dead cube).
    yoke_shape = _yoke_shape(col_x)
    yoke = semantic_part(
        doc, stand_group,
        "Yoke_Bracket", "Yoke Bracket (U-Wrap Tilt Cradle)",
        yoke_shape,
        _stand_metadata(
            "HNK-ST-009", "Yoke_Bracket", p.MATERIAL_INTENTS["Die_Cast_Joint"],
            external_standard_id=(
                "Column-integrated cradle per Apple Studio Display; "
                "wraps column front half, tilt-axis through Trunnion"
            ),
        ),
    )
    add_dimension(yoke, "TiltRangeDeg",
                  p.STAND["tilt_max"] - p.STAND["tilt_min"])
    add_dimension(yoke, "WrapWallThickness", YOKE_WALL)
    # Yoke uses clearance fit around column and trunnion; structural
    # continuity is via bolts (LOD 3 proxy fasteners not modelled).
    # No volumetric authorized-contact declarations for these joints.
    parts.append(yoke)

    # Iter 8: Tilt_Trunnion visible pivot cylinder along X axis.
    # Split into two side stubs to avoid intersecting the column tube;
    # the visible pivot axis is the same line but material only exists
    # outside the column diameter, as a compound of two cylinders.
    trunnion_stub_len = (TILT_TRUNNION_LEN - COLUMN_OD) / 2.0
    trunnion_left = Part.makeCylinder(
        TILT_TRUNNION_OD / 2.0, trunnion_stub_len,
        vector(col_x - COLUMN_OD / 2.0 - trunnion_stub_len,
               TILT_TRUNNION_Y, TILT_TRUNNION_Z),
        vector(1.0, 0.0, 0.0),
    )
    trunnion_right = Part.makeCylinder(
        TILT_TRUNNION_OD / 2.0, trunnion_stub_len,
        vector(col_x + COLUMN_OD / 2.0,
               TILT_TRUNNION_Y, TILT_TRUNNION_Z),
        vector(1.0, 0.0, 0.0),
    )
    trunnion_shape = Part.makeCompound([trunnion_left, trunnion_right])
    trunnion = semantic_part(
        doc, stand_group,
        "Tilt_Trunnion", "Tilt Trunnion (Pivot Shaft)",
        trunnion_shape,
        _stand_metadata(
            "HNK-ST-010", "Tilt_Trunnion", p.MATERIAL_INTENTS["Stand_Structure"],
            external_standard_id="Chromed steel shaft, D25 mm class"
        ),
    )
    add_dimension(trunnion, "TrunnionDiameter", TILT_TRUNNION_OD)
    add_dimension(trunnion, "TrunnionLength", TILT_TRUNNION_LEN)
    # Trunnion clearance fit inside yoke bores; no volumetric contact.
    parts.append(trunnion)

    # VESA mount plate (unchanged 140x140x4 at head rear z=62..66).
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
            "HNK-ST-011", "VESA_Mount_Plate",
            p.MATERIAL_INTENTS["Sheet_Bracket_Shield"],
            external_standard_id=(
                "VESA MIS-D 100 (100x100 mm) mating plate; 140x140 mm "
                "footprint per Hinoki STAND contract"
            ),
        ),
    )
    add_dimension(vesa_plate, "PlateThickness", VESA_MOUNT_PLATE_T)
    add_property(vesa_plate, "App::PropertyString", "MatingFace",
                 "Rear_Enclosure outer @ z=62; clamped by M4 VESA fasteners")
    parts.append(vesa_plate)

    # Iter 8: Cable_Channel rear rectangular slot positioned BELOW lift
    # travel zone so it does not clash with the lift sleeve or column
    # base bezel; represents cable pass-through from head bottom I/O
    # down through the column back rail to base rear exit.
    cable_channel_shape = Part.makeBox(
        CABLE_CHANNEL_W, CABLE_CHANNEL_H, CABLE_CHANNEL_D,
        vector(
            col_x - CABLE_CHANNEL_W / 2.0,
            col_bottom_y + BASE_COVER_HEIGHT + 20.0,
            COLUMN_Z_CENTRE + LIFT_SLEEVE_OD / 2.0 + 3.0,
        ),
    )
    cable_channel = semantic_part(
        doc, stand_group,
        "Cable_Channel", "Cable Channel (Rear Column Slot)",
        cable_channel_shape,
        _stand_metadata(
            "HNK-ST-012", "Cable_Channel", p.MATERIAL_INTENTS["Housing_Polymer"],
            external_standard_id="Cable routing proxy per Cisco Desk Pro pattern",
        ),
    )
    add_dimension(cable_channel, "ChannelWidth", CABLE_CHANNEL_W)
    add_dimension(cable_channel, "ChannelHeight", CABLE_CHANNEL_H)
    parts.append(cable_channel)

    _add_motion_references(doc, reference_group, col_x, col_top_y)
    return parts


def _add_motion_references(doc, reference_group, col_x, col_top_y):
    """Add three swept motion envelopes as reference-only bodies."""
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

    swivel_range = p.STAND["swivel_max"] - p.STAND["swivel_min"]
    swivel_r = 260.0
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
# Kinematic transforms
# ------------------------------------------------------------------


def _head_semantic_names(doc):
    excluded_assemblies = {"06_Stand_Base_Kinematics", "08_Reference_Datums_Keepouts"}
    return [
        obj.Name for obj in doc.Objects
        if getattr(obj, "IsSemanticPart", False)
        and getattr(obj, "ParentAssembly", "") not in excluded_assemblies
    ]


def _moving_names(doc):
    return list(_head_semantic_names(doc)) + list(STAND_MOVING_PART_NAMES)


def apply_posture(doc, height_offset_mm, tilt_deg, swivel_deg):
    lift_pivot_y = COLUMN_TOP_Y_NOMINAL - LIFT_TRAVEL / 2.0
    tilt_axis_point = App.Vector(_column_x(),
                                 lift_pivot_y,
                                 p.HEAD["depth"])
    tilt_axis_dir = App.Vector(1.0, 0.0, 0.0)
    swivel_axis_point = App.Vector(_column_x(), BASE_TOP_Y, COLUMN_Z_CENTRE)
    swivel_axis_dir = App.Vector(0.0, 1.0, 0.0)

    tilt_rot = App.Rotation(tilt_axis_dir, tilt_deg)
    swivel_rot = App.Rotation(swivel_axis_dir, swivel_deg)

    tilt_placement = App.Placement()
    tilt_placement.Rotation = tilt_rot
    tilt_placement.Base = tilt_axis_point - tilt_rot.multVec(tilt_axis_point)

    swivel_placement = App.Placement()
    swivel_placement.Rotation = swivel_rot
    swivel_placement.Base = swivel_axis_point - swivel_rot.multVec(swivel_axis_point)

    height_placement = App.Placement()
    height_placement.Base = App.Vector(0, height_offset_mm, 0)

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
    identity = App.Placement()
    for name in _moving_names(doc):
        obj = doc.getObject(name)
        if obj is not None:
            obj.Placement = identity
    doc.recompute()


def head_overall_height_mm(doc):
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
    head_cx = HEAD_COM_LOCAL[0]
    head_cy = HEAD_COM_LOCAL[1]
    head_cz = HEAD_COM_LOCAL[2]
    stand_cx = STAND_COM_LOCAL[0]
    stand_cz = STAND_COM_LOCAL[2]

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
    return [
        (h, t, s)
        for h in (-LIFT_TRAVEL / 2.0, +LIFT_TRAVEL / 2.0)
        for t in (p.STAND["tilt_min"], p.STAND["tilt_max"])
        for s in (p.STAND["swivel_min"], p.STAND["swivel_max"])
    ]
