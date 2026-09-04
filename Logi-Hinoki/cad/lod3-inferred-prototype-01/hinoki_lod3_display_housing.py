"""Display-stack and enclosure geometry for the Hinoki LOD 3 master.

Design intent (Task 8 quality remediation, 2026-09-04):

Enclosure mating (Q-01): the front bezel, metal mid-frame, and rear cover
form three semantic parts with continuous perimeter sidewalls. The mid-frame
sidewall bridges the historic 15.8 mm gap between front and rear. Rear cover
overlaps the mid-frame with a 3 mm stepped lap and 0.3 mm nominal design
clearance per side. Rear I/O cover is a separate removable service part.

Panel construction (Q-02): the flat Backlight_Unit box is replaced by an
edge-lit backplate + LGP + optical films stack with a discrete LED bar. IC
solids for BLU driver, T-CON, and panel gate/source driver are added; heat
mapping is defined in hinoki_lod3_electronics_thermal.py.

Rib architecture (Q-03): the six historic floating ribs are removed as
independent semantic parts and re-realised as continuous internal features
fused into the Rear_Enclosure solid. Feature evidence is exposed via the
RibFeatureCount / RibFeatureIds properties on Rear_Enclosure. VESA
reinforcement is fused into Metal_Mid_Frame. Corner and VESA bosses remain
separate semantic parts and are rooted on Metal_Mid_Frame; fasteners are
sized to actually engage those bosses through the rear cover.
"""

import Part

import hinoki_lod3_parameters as p
from hinoki_lod3_common import (
    add_area,
    add_dimension,
    add_property,
    centred_offset,
    semantic_part,
    set_external_standard,
    vector,
)


DISPLAY_SOURCE = "Approved LOD 3 design section 5.1"
PANEL_SOURCE = "Task 8 panel remediation; edge-lit engineering assumption"
HOUSING_SOURCE = "Dixie DFM-informed Hinoki assumption; design section 5.1"
MID_FRAME_SOURCE = (
    "Dixie metal-frame architecture; Hinoki structural spine with "
    "integrated perimeter sidewall, transverse plate, and VESA "
    "reinforcement"
)
VENT_SOURCE = "Approved lower/rear-lower inlet and upper-rear outlet topology"
RIB_SOURCE = "Fused internal ribs on rear cover for VESA and long-edge support"


# Fused rib layout: 4 VESA-support ribs plus 2 long-edge anti-flex ribs.
# All rib feet sit continuously on the rear cover inner face (z=59.2) and
# extend forward to z=44.0 (15.2 mm tall) so they do not collide with PCBs
# at z=27..32. Each rib is a 1.7 mm thick wall aligned with the rear cover.
REAR_RIB_LAYOUT = (
    # (rib_id, x, y, width_x, depth_y, height, orientation).
    # VESA vertical ribs are placed OUTBOARD of the VESA boss cluster
    # (bosses centred at x=321 and x=421, boss radius 4.5) to avoid
    # collision with the boss cylinders that pass through z=25..59.2.
    ("VESA_Rib_H_T", 275.0, 178.0, 192.0, 1.7, 15.2, "horizontal"),
    ("VESA_Rib_H_B", 275.0, 312.3, 192.0, 1.7, 15.2, "horizontal"),
    ("VESA_Rib_V_L", 304.0, 178.0, 1.7, 136.0, 15.2, "vertical"),
    ("VESA_Rib_V_R", 436.3, 178.0, 1.7, 136.0, 15.2, "vertical"),
    ("AntiFlex_Rib_Bottom", 90.0, 96.0, 560.0, 1.7, 15.2, "horizontal"),
    ("AntiFlex_Rib_Top", 90.0, 394.3, 560.0, 1.7, 15.2, "horizontal"),
)


def metadata(
    part_id,
    part_name,
    parent,
    material,
    source_class,
    source_reference,
    thermal_disposition="Keep",
):
    return p.part_metadata(
        part_id=part_id,
        part_name=part_name,
        parent_assembly=parent,
        material_intent=material,
        source_class=source_class,
        source_reference=source_reference,
        confidence="High" if source_class in ("Known", "Derived") else "Medium",
        thermal_disposition=thermal_disposition,
    )


def box_from_dimensions(dimensions, z, x_offset=None, y_offset=None):
    x = centred_offset(p.HEAD["width"], dimensions["width"]) if x_offset is None else x_offset
    y = centred_offset(p.HEAD["height"], dimensions["height"]) if y_offset is None else y_offset
    return Part.makeBox(
        dimensions["width"],
        dimensions["height"],
        dimensions["thickness"],
        vector(x, y, z),
    )


def ring(outer_width, outer_height, inner_width, inner_height, thickness, z):
    outer = Part.makeBox(
        outer_width,
        outer_height,
        thickness,
        vector(
            centred_offset(p.HEAD["width"], outer_width),
            centred_offset(p.HEAD["height"], outer_height),
            z,
        ),
    )
    inner = Part.makeBox(
        inner_width,
        inner_height,
        thickness + 0.2,
        vector(
            centred_offset(p.HEAD["width"], inner_width),
            centred_offset(p.HEAD["height"], inner_height),
            z - 0.1,
        ),
    )
    return outer.cut(inner)


def _perimeter_ring(outer_w, outer_h, wall, z, height):
    """Ring solid centred on head, wall-thick perimeter, height in z."""
    inner_w = outer_w - 2.0 * wall
    inner_h = outer_h - 2.0 * wall
    outer = Part.makeBox(
        outer_w,
        outer_h,
        height,
        vector(
            centred_offset(p.HEAD["width"], outer_w),
            centred_offset(p.HEAD["height"], outer_h),
            z,
        ),
    )
    inner = Part.makeBox(
        inner_w,
        inner_h,
        height + 0.2,
        vector(
            centred_offset(p.HEAD["width"], inner_w),
            centred_offset(p.HEAD["height"], inner_h),
            z - 0.1,
        ),
    )
    return outer.cut(inner)


def build_mid_frame_shape():
    """Build the structural mid-frame with continuous perimeter sidewall,
    fused corner boss pads, and a horizontal VESA reinforcement spine.

    Geometry summary (all mm):
        - Perimeter main sidewall: outer 741.6 x 491.6 (0.2 mm inset each
          side from HEAD outer 742 x 492 for the designed front seam),
          wall 2 mm, z=3.2 .. 22.0 (18.8 mm tall). Bridges the historic
          15.8 mm front/rear enclosure gap.
        - Perimeter lap sidewall: outer 735.8 x 485.8 (fits inside rear
          cover inner cavity 736.4 with 0.3 mm radial clearance per side),
          wall 2 mm, z=22.0 .. 25.0 (3 mm lap depth).
        - Four corner boss pads: 70 x 70 x 3 mm at each HEAD corner,
          z=22.0 .. 25.0, fused into perimeter lap walls so they are
          structurally continuous with the sidewall and provide a
          mounting shelf for the corner boss cylinders (rooted at z=25).
        - VESA reinforcement spine: 742 x 140 x 3 mm at (0, 176, 22.0),
          fuses to the perimeter left/right lap walls and provides a
          continuous horizontal structural web that carries the four VESA
          bosses. Load path: external VESA mount -> VESA bosses -> spine
          -> perimeter left/right walls -> corner bosses -> fasteners ->
          rear cover.
    """
    em = p.ENCLOSURE_MATING
    housing = p.HOUSING
    head = p.HEAD

    front_inset = em["front_seam_radial_clearance"]
    main_outer_w = head["width"] - 2.0 * front_inset
    main_outer_h = head["height"] - 2.0 * front_inset
    wall = housing["mid_frame_wall"]

    main_height = housing["mid_frame_lap_start_z"] - housing["mid_frame_front_z"]
    main_ring = _perimeter_ring(
        main_outer_w,
        main_outer_h,
        wall,
        housing["mid_frame_front_z"],
        main_height,
    )

    lap_inset = em["lap_radial_clearance"] + housing["rear_wall"]
    lap_outer_w = head["width"] - 2.0 * lap_inset
    lap_outer_h = head["height"] - 2.0 * lap_inset
    lap_height = housing["mid_frame_rear_z"] - housing["mid_frame_lap_start_z"]
    lap_ring = _perimeter_ring(
        lap_outer_w,
        lap_outer_h,
        wall,
        housing["mid_frame_lap_start_z"],
        lap_height,
    )

    shape = main_ring.fuse(lap_ring)

    lap_z = housing["mid_frame_lap_start_z"]
    lap_plate_thickness = housing["mid_frame_rear_z"] - lap_z

    # Corner pads and VESA spine must stay INSIDE the rear cover inner
    # cavity to avoid interfering with the rear cover sidewalls
    # (walls occupy X=0..rear_wall and X=head-rear_wall..head). Use the
    # rear wall thickness as the safe inset.
    rear_wall = housing["rear_wall"]
    pad_size = 70.0 - rear_wall
    for bx, by in p.CORNER_BOSS_POSITIONS:
        px = rear_wall if bx < head["width"] / 2.0 else head["width"] - rear_wall - pad_size
        py = rear_wall if by < head["height"] / 2.0 else head["height"] - rear_wall - pad_size
        pad = Part.makeBox(
            pad_size, pad_size, lap_plate_thickness, vector(px, py, lap_z)
        )
        shape = shape.fuse(pad)

    vesa_spine_h = 140.0
    vesa_spine_y = 176.0
    vesa_spine_x = rear_wall
    vesa_spine_w = head["width"] - 2.0 * rear_wall
    vesa_spine = Part.makeBox(
        vesa_spine_w,
        vesa_spine_h,
        lap_plate_thickness,
        vector(vesa_spine_x, vesa_spine_y, lap_z),
    )
    shape = shape.fuse(vesa_spine)

    return shape


def _rib_solid(spec):
    _, x, y, w, d, h, _ = spec
    housing = p.HOUSING
    rear_inner_z = p.HEAD["depth"] - housing["rear_wall"] - h
    return Part.makeBox(w, d, h, vector(x, y, rear_inner_z))


def rib_shapes():
    return [_rib_solid(spec) for spec in REAR_RIB_LAYOUT]


def build_rear_enclosure():
    housing = p.HOUSING
    wall = housing["rear_wall"]
    front_z = housing["rear_cover_front_z"]
    rear_z = p.HEAD["depth"] - wall

    outer_w = p.HEAD["width"]
    outer_h = p.HEAD["height"]

    # Rear back panel
    back = Part.makeBox(outer_w, outer_h, wall, vector(0.0, 0.0, rear_z))
    inlet_slots = vent_slots(30.0, rear_z - 0.2)
    outlet_slots = vent_slots(outer_h - 55.0, rear_z - 0.2)
    service_cutout = Part.makeBox(
        220.0, 80.0, wall + 0.4, vector(261.0, 206.0, rear_z - 0.2)
    )
    back = back.cut(Part.makeCompound(inlet_slots + outlet_slots + [service_cutout]))

    # Corner fastener through-holes so fasteners actually pass through the
    # rear cover (required by clamping verification).
    fastener_through_hole_radius = 1.9
    corner_holes = [
        Part.makeCylinder(
            fastener_through_hole_radius,
            wall + 0.4,
            vector(x, y, rear_z - 0.2),
        )
        for x, y in p.CORNER_BOSS_POSITIONS
    ]
    vesa_through_hole_radius = 2.6
    vesa_holes = [
        Part.makeCylinder(
            vesa_through_hole_radius,
            wall + 0.4,
            vector(x, y, rear_z - 0.2),
        )
        for x, y in p.VESA_MOUNT_POINTS
    ]
    back = back.cut(Part.makeCompound(corner_holes + vesa_holes))

    # Perimeter sidewall from front (z=22) to back inner face
    side_height = rear_z - front_z
    left = Part.makeBox(wall, outer_h, side_height, vector(0.0, 0.0, front_z))
    right = Part.makeBox(
        wall, outer_h, side_height,
        vector(outer_w - wall, 0.0, front_z),
    )
    bottom = Part.makeBox(
        outer_w - 2.0 * wall, wall, side_height, vector(wall, 0.0, front_z)
    )
    top = Part.makeBox(
        outer_w - 2.0 * wall, wall, side_height,
        vector(wall, outer_h - wall, front_z),
    )
    shape = back.fuse(left).fuse(right).fuse(bottom).fuse(top)

    # Fuse internal ribs as continuous features on the rear cover inner face.
    for rib_shape in rib_shapes():
        shape = shape.fuse(rib_shape)

    return shape, inlet_slots, outlet_slots


def vesa_reinforcement_shape():  # retained for backward compatibility only
    return None


def vent_slots(y, z):
    slot_width = 12.0
    slot_height = 25.0
    pitch = 20.0
    field_x = centred_offset(p.HEAD["width"], 400.0)
    return [
        Part.makeBox(
            slot_width,
            slot_height,
            3.2,
            vector(field_x + index * pitch + 4.0, y, z),
        )
        for index in range(20)
    ]


def build_display_stack(doc, groups):
    display_group = groups["01_Display_Stack"]
    parts = []

    z_positions = {
        "Cover_Glass": 0.0,
        "PCAP_Sensor": 3.2,
        "Optical_Bond": 4.0,
        "LCD_Cell": 4.5,
        "BLU_Optical_Films": 7.0,
        "Light_Guide_Plate": 8.5,
        "Panel_Backplate": 12.5,
    }
    material_map = {
        "Cover_Glass": p.MATERIAL_INTENTS["Display_Glass"],
        "PCAP_Sensor": "FLOEFD equivalent PCAP sensor",
        "Optical_Bond": "Optically clear adhesive equivalent",
        "LCD_Cell": "FLOEFD equivalent LCD cell",
        "BLU_Optical_Films": p.MATERIAL_INTENTS["Optical_Film"],
        "Light_Guide_Plate": p.MATERIAL_INTENTS["Light_Guide"],
        "Panel_Backplate": p.MATERIAL_INTENTS["Panel_Backplate"],
    }
    source_class_map = {
        "Cover_Glass": "Derived",
        "PCAP_Sensor": "EngineeringAssumption",
        "Optical_Bond": "EngineeringAssumption",
        "LCD_Cell": "EngineeringAssumption",
        "BLU_Optical_Films": "EngineeringAssumption",
        "Light_Guide_Plate": "EngineeringAssumption",
        "Panel_Backplate": "EngineeringAssumption",
    }
    id_map = {
        "Cover_Glass": "HNK-DS-001",
        "PCAP_Sensor": "HNK-DS-002",
        "Optical_Bond": "HNK-DS-003",
        "LCD_Cell": "HNK-DS-004",
        "BLU_Optical_Films": "HNK-DS-005",
        "Light_Guide_Plate": "HNK-DS-006",
        "Panel_Backplate": "HNK-DS-007",
    }

    for name in z_positions:
        z = z_positions[name]
        dims = p.DISPLAY_STACK[name]
        if name == "Panel_Backplate":
            # Backplate has a cutout for the LED bar to prevent interference.
            base = box_from_dimensions(dims, z)
            led = p.LED_BAR
            films_dims = p.DISPLAY_STACK["Light_Guide_Plate"]
            films_y = centred_offset(p.HEAD["height"], films_dims["height"])
            led_x = centred_offset(p.HEAD["width"], led["width"])
            cutout = Part.makeBox(
                led["width"] + 2.0 * p.BACKPLATE_LED_CUTOUT_CLEARANCE,
                led["depth"] + 2.0 * p.BACKPLATE_LED_CUTOUT_CLEARANCE,
                dims["thickness"] + 0.4,
                vector(
                    led_x - p.BACKPLATE_LED_CUTOUT_CLEARANCE,
                    films_y - p.BACKPLATE_LED_CUTOUT_CLEARANCE,
                    z - 0.2,
                ),
            )
            shape = base.cut(cutout)
        else:
            shape = box_from_dimensions(dims, z)
        obj = semantic_part(
            doc,
            display_group,
            name,
            name.replace("_", " "),
            shape,
            metadata(
                id_map[name],
                name,
                "01_Display_Stack",
                material_map[name],
                source_class_map[name],
                DISPLAY_SOURCE,
            ),
        )
        parts.append(obj)

    # Edge-lit LED bar (bottom edge), separate physical solid so it can carry
    # a discrete Heat_BLU_LED heat source.
    led = p.LED_BAR
    lgp_dims = p.DISPLAY_STACK["Light_Guide_Plate"]
    lgp_y = centred_offset(p.HEAD["height"], lgp_dims["height"])
    led_x = centred_offset(p.HEAD["width"], led["width"])
    led_z = 12.5
    led_shape = Part.makeBox(
        led["width"],
        led["depth"],
        led["thickness"],
        vector(led_x, lgp_y, led_z),
    )
    led_bar = semantic_part(
        doc,
        display_group,
        "LED_Bar_Bottom",
        "LED Bar (Bottom Edge)",
        led_shape,
        metadata(
            "HNK-DS-008",
            "LED_Bar_Bottom",
            "01_Display_Stack",
            p.MATERIAL_INTENTS["LED_Assembly"],
            "EngineeringAssumption",
            led["source_reference"],
        ),
    )
    add_property(led_bar, "App::PropertyString", "PanelArchitecture", led["architecture"])
    parts.append(led_bar)

    # Panel gate/source driver (COF) strip placed behind the panel_backplate
    # (z=15.6..16.6, between backplate back face and Display_Carrier front).
    gate = p.PANEL_DRIVER["Panel_Gate_Source_Driver"]
    gate_shape = Part.makeBox(
        gate["width"],
        gate["depth"],
        gate["thickness"],
        vector(
            centred_offset(p.HEAD["width"], gate["width"]),
            48.0,
            15.6,
        ),
    )
    gate_part = semantic_part(
        doc,
        display_group,
        "Panel_Gate_Source_Driver",
        "Panel Gate/Source COF Driver",
        gate_shape,
        metadata(
            "HNK-DS-009",
            "Panel_Gate_Source_Driver",
            "01_Display_Stack",
            p.MATERIAL_INTENTS["COF_Driver"],
            "EngineeringAssumption",
            gate["source_reference"],
        ),
    )
    parts.append(gate_part)

    # Display carrier (existing) and TCON PCB (existing) plus TCON IC (new).
    display_carrier = semantic_part(
        doc,
        display_group,
        "Display_Carrier",
        "Display Carrier",
        ring(722.0, 412.0, 704.0, 394.0, 2.0, 19.0),
        metadata(
            "HNK-DS-010",
            "Display_Carrier",
            "01_Display_Stack",
            p.MATERIAL_INTENTS["Sheet_Bracket_Shield"],
            "DixieReference",
            "Dixie display carrier architecture; Hinoki envelope rebuild",
        ),
    )
    parts.append(display_carrier)

    tcon = semantic_part(
        doc,
        display_group,
        "TCON_PCB",
        "T-CON PCB",
        Part.makeBox(200.0, 30.0, 1.6, vector(271.0, 32.0, 21.2)),
        metadata(
            "HNK-DS-011",
            "TCON_PCB",
            "01_Display_Stack",
            p.MATERIAL_INTENTS["PCB"],
            "EngineeringAssumption",
            "Display-stack packaging assumption; design section 6.1",
        ),
    )
    parts.append(tcon)

    tcon_ic_spec = p.PANEL_DRIVER["TCON_IC"]
    tcon_ic_shape = Part.makeBox(
        tcon_ic_spec["width"],
        tcon_ic_spec["height"],
        tcon_ic_spec["thickness"],
        vector(360.0, 40.0, 22.8),
    )
    tcon_ic = semantic_part(
        doc,
        display_group,
        "TCON_IC",
        "T-CON IC",
        tcon_ic_shape,
        metadata(
            "HNK-DS-012",
            "TCON_IC",
            "01_Display_Stack",
            p.MATERIAL_INTENTS["IC_Package"],
            "EngineeringAssumption",
            tcon_ic_spec["source_reference"],
        ),
    )
    parts.append(tcon_ic)

    blu_driver_spec = p.PANEL_DRIVER["BLU_Driver_PCB"]
    blu_driver_shape = Part.makeBox(
        blu_driver_spec["width"],
        blu_driver_spec["height"],
        blu_driver_spec["thickness"],
        vector(490.0, 34.0, 21.2),
    )
    blu_driver = semantic_part(
        doc,
        display_group,
        "BLU_Driver_PCB",
        "BLU LED Driver PCB",
        blu_driver_shape,
        metadata(
            "HNK-DS-013",
            "BLU_Driver_PCB",
            "01_Display_Stack",
            p.MATERIAL_INTENTS["PCB"],
            "EngineeringAssumption",
            blu_driver_spec["source_reference"],
        ),
    )
    parts.append(blu_driver)

    return parts


def build_housing_shell(doc, groups):
    housing_group = groups["02_Housing_Structure"]
    fastener_group = groups["07_Fasteners_Seals_Consumables"]
    reference_group = groups["08_Reference_Datums_Keepouts"]
    parts = []

    front_bezel = semantic_part(
        doc,
        housing_group,
        "Front_Bezel",
        "Front Bezel",
        ring(742.0, 492.0, 726.0, 446.0, 3.2, 0.0),
        metadata(
            "HNK-HS-001",
            "Front_Bezel",
            "02_Housing_Structure",
            p.MATERIAL_INTENTS["Housing_Polymer"],
            "EngineeringAssumption",
            HOUSING_SOURCE,
        ),
    )
    add_dimension(
        front_bezel,
        "SeamNominalClearance",
        p.ENCLOSURE_MATING["front_seam_radial_clearance"],
    )
    add_dimension(front_bezel, "FrameWidthX", 8.0)
    add_dimension(front_bezel, "FrameWidthY", 23.0)
    add_dimension(front_bezel, "BezelThickness", p.ENCLOSURE_MATING["bezel_thickness"])
    add_area(front_bezel, "GlassCavityOpen", 726.0 * 446.0)
    parts.append(front_bezel)

    mid_frame = semantic_part(
        doc,
        housing_group,
        "Metal_Mid_Frame",
        "Metal Mid Frame (Structural Spine)",
        build_mid_frame_shape(),
        metadata(
            "HNK-HS-002",
            "Metal_Mid_Frame",
            "02_Housing_Structure",
            p.MATERIAL_INTENTS["Aluminum_Structure"],
            "DixieReference",
            MID_FRAME_SOURCE,
        ),
    )
    add_dimension(mid_frame, "PerimeterWallThickness", p.HOUSING["mid_frame_wall"])
    add_dimension(mid_frame, "TransversePlateThickness", p.HOUSING["mid_frame_plate_thickness"])
    add_dimension(mid_frame, "LapDepth", p.ENCLOSURE_MATING["lap_depth"])
    add_dimension(mid_frame, "DraftAngleDeg", 1.0)
    add_dimension(mid_frame, "RootFilletRadius", 0.8)
    add_property(
        mid_frame,
        "App::PropertyStringList",
        "IntegratedFeatures",
        [
            "Perimeter_Sidewall_Main",
            "Perimeter_Sidewall_Lap",
            "Corner_Boss_Mounting_Pads",
            "VESA_Reinforcement_Spine",
        ],
    )
    add_property(mid_frame, "App::PropertyInteger", "BossFeatureCount", 8)
    add_property(
        mid_frame,
        "App::PropertyStringList",
        "BossFeatureIds",
        [
            "Primary_Boss_01",
            "Primary_Boss_02",
            "Primary_Boss_03",
            "Primary_Boss_04",
            "VESA_Boss_01",
            "VESA_Boss_02",
            "VESA_Boss_03",
            "VESA_Boss_04",
        ],
    )
    add_property(
        mid_frame,
        "App::PropertyStringList",
        "AuthorizedContactTargets",
        [
            "Primary_Boss_01",
            "Primary_Boss_02",
            "Primary_Boss_03",
            "Primary_Boss_04",
            "VESA_Boss_01",
            "VESA_Boss_02",
            "VESA_Boss_03",
            "VESA_Boss_04",
        ],
    )
    parts.append(mid_frame)

    rear_shape, inlet_slots, outlet_slots = build_rear_enclosure()
    rear = semantic_part(
        doc,
        housing_group,
        "Rear_Enclosure",
        "Rear Enclosure",
        rear_shape,
        metadata(
            "HNK-HS-003",
            "Rear_Enclosure",
            "02_Housing_Structure",
            p.MATERIAL_INTENTS["Housing_Polymer"],
            "EngineeringAssumption",
            HOUSING_SOURCE,
        ),
    )
    add_dimension(rear, "WallThickness", p.HOUSING["rear_wall"])
    add_area(rear, "InletOpenArea", 6000.0)
    add_area(rear, "OutletOpenArea", 6000.0)
    add_property(rear, "App::PropertyInteger", "RibFeatureCount", len(REAR_RIB_LAYOUT))
    add_property(
        rear,
        "App::PropertyStringList",
        "RibFeatureIds",
        [spec[0] for spec in REAR_RIB_LAYOUT],
    )
    add_property(rear, "App::PropertyString", "RibHostPart", "Rear_Enclosure")
    add_dimension(rear, "RibThickness", p.HOUSING["rib_thickness"])
    add_dimension(rear, "ServiceToolClearance_M3", 40.0)
    add_dimension(rear, "ServiceToolClearance_M4", 45.0)
    add_property(
        rear,
        "App::PropertyStringList",
        "AssemblySequence",
        [
            "1_Front_Assy_into_Mid_Frame",
            "2_PCB_and_Thermal_onto_Mid_Frame",
            "3_Rear_Enclosure_over_Mid_Frame_from_back",
            "4_M3_Corner_Fasteners_from_rear",
            "5_M4_VESA_Fasteners_external",
            "6_Rear_IO_Cover_service_hatch",
        ],
    )
    add_property(
        rear,
        "App::PropertyString",
        "InsertionDirection",
        "-Z (rear-to-front); ribs travel with rear cover",
    )
    parts.append(rear)

    io_cover = semantic_part(
        doc,
        housing_group,
        "Rear_IO_Cover",
        "Rear I/O Service Cover",
        Part.makeBox(218.0, 78.0, 2.0, vector(262.0, 207.0, 60.0)),
        metadata(
            "HNK-HS-004",
            "Rear_IO_Cover",
            "02_Housing_Structure",
            p.MATERIAL_INTENTS["Housing_Polymer"],
            "EngineeringAssumption",
            "Serviceable rear I/O zone; design section 6.2",
        ),
    )
    parts.append(io_cover)

    # Corner bosses on mid-frame back face: 34.2 mm tall, top face touches
    # rear cover inner face at z=59.2. M3 tapped hole engaged from the rear.
    for index, (x, y) in enumerate(p.CORNER_BOSS_POSITIONS, start=1):
        boss_z = p.COLLISION_CLEARANCE["rear_boss_z"]
        boss_height = p.COLLISION_CLEARANCE["rear_boss_height"]
        boss_shape = Part.makeCylinder(
            p.HOUSING["primary_boss_od"] / 2.0,
            boss_height,
            vector(x, y, boss_z),
        ).cut(
            Part.makeCylinder(
                1.6, 10.5, vector(x, y, boss_z + boss_height - 10.4)
            )
        )
        boss = semantic_part(
            doc,
            housing_group,
            "Primary_Boss_{:02d}".format(index),
            "Primary Boss {:02d}".format(index),
            boss_shape,
            metadata(
                "HNK-HS-{:03d}".format(30 + index),
                "Primary_Boss_{:02d}".format(index),
                "02_Housing_Structure",
                p.MATERIAL_INTENTS["Aluminum_Structure"],
                "DixieReference",
                "Corner boss integral with mid-frame; M3 tapped hole; "
                "0.5 mm root engagement into mid-frame lap",
                "Aggregate",
            ),
        )
        add_dimension(boss, "BossOuterDiameter", p.HOUSING["primary_boss_od"])
        add_dimension(boss, "RootEngagement", p.COLLISION_CLEARANCE["boss_root_engagement"])
        add_dimension(boss, "DraftAngleDeg", 1.5)
        add_dimension(boss, "RootFilletRadius", 0.8)
        add_dimension(boss, "ToolAccessDia", 6.0)
        add_dimension(boss, "TapDepth", 10.5)
        add_property(boss, "App::PropertyString", "HostPart", "Metal_Mid_Frame")
        add_property(boss, "App::PropertyString", "MoldingDraftDirection", "-Z (drawn from rear)")
        add_property(
            boss,
            "App::PropertyStringList",
            "AuthorizedContactTargets",
            ["Metal_Mid_Frame"],
        )
        parts.append(boss)

        # M3 fastener: 12 mm long, spans z=50..62 through rear cover into boss.
        fastener_length = 12.0
        fastener_z = p.HEAD["depth"] - fastener_length
        fastener = semantic_part(
            doc,
            fastener_group,
            "M3_Fastener_{:02d}".format(index),
            "M3 Fastener {:02d}".format(index),
            Part.makeCylinder(1.5, fastener_length, vector(x, y, fastener_z)),
            metadata(
                "HNK-FS-{:03d}".format(index),
                "M3_Fastener_{:02d}".format(index),
                "07_Fasteners_Seals_Consumables",
                p.MATERIAL_INTENTS["Steel_Hardware"],
                "DixieReference",
                "M3x12 fastener; clamps rear cover to mid-frame corner boss",
                "Suppress",
            ),
        )
        add_property(fastener, "App::PropertyString", "ClampedStack", "Rear_Enclosure|Primary_Boss_{:02d}".format(index))
        add_property(fastener, "App::PropertyString", "TargetHost", "Primary_Boss_{:02d}".format(index))
        parts.append(fastener)

    # VESA bosses: also mid-frame back face, M4 tapped for external VESA
    # mounting. Provides load path from external mount into the mid-frame.
    # Tap depth is 12 mm (matches M4x14 fastener 12 mm engagement).
    for index, (x, y) in enumerate(p.VESA_MOUNT_POINTS, start=1):
        boss_z = p.COLLISION_CLEARANCE["rear_boss_z"]
        boss_height = p.COLLISION_CLEARANCE["vesa_boss_height"]
        vesa_tap_depth = 12.0
        boss_shape = Part.makeCylinder(
            p.HOUSING["vesa_boss_od"] / 2.0,
            boss_height,
            vector(x, y, boss_z),
        ).cut(
            Part.makeCylinder(
                2.1,
                vesa_tap_depth,
                vector(x, y, boss_z + boss_height - (vesa_tap_depth - 0.1)),
            )
        )
        boss = semantic_part(
            doc,
            housing_group,
            "VESA_Boss_{:02d}".format(index),
            "VESA Boss {:02d}".format(index),
            boss_shape,
            metadata(
                "HNK-HS-{:03d}".format(40 + index),
                "VESA_Boss_{:02d}".format(index),
                "02_Housing_Structure",
                p.MATERIAL_INTENTS["Aluminum_Structure"],
                "CompetitorOfficial",
                "VESA 100 x 100 mount boss; integral with mid-frame VESA spine; "
                "0.5 mm root engagement",
                "Aggregate",
            ),
        )
        add_dimension(boss, "BossOuterDiameter", p.HOUSING["vesa_boss_od"])
        add_dimension(boss, "RootEngagement", p.COLLISION_CLEARANCE["boss_root_engagement"])
        add_dimension(boss, "DraftAngleDeg", 1.5)
        add_dimension(boss, "RootFilletRadius", 1.0)
        add_dimension(boss, "ToolAccessDia", 8.0)
        add_dimension(boss, "TapDepth", 12.0)
        add_property(boss, "App::PropertyString", "HostPart", "Metal_Mid_Frame")
        add_property(boss, "App::PropertyString", "MoldingDraftDirection", "-Z (drawn from rear)")
        set_external_standard(boss, "VESA MIS-D 100 (100x100 mm fixed monitor mount)")
        add_property(
            boss,
            "App::PropertyStringList",
            "AuthorizedContactTargets",
            ["Metal_Mid_Frame"],
        )
        parts.append(boss)

        # M4 fastener stub (14 mm) representing external VESA mounting screw.
        # 14 mm gives 11.2 mm engagement into the boss (z=48..59.2 boss span),
        # meeting typical VESA screw depth guidance.
        fastener_length = 14.0
        fastener_z = p.HEAD["depth"] - fastener_length
        fastener = semantic_part(
            doc,
            fastener_group,
            "M4_VESA_Fastener_{:02d}".format(index),
            "M4 VESA Fastener {:02d}".format(index),
            Part.makeCylinder(2.0, fastener_length, vector(x, y, fastener_z)),
            metadata(
                "HNK-FS-{:03d}".format(10 + index),
                "M4_VESA_Fastener_{:02d}".format(index),
                "07_Fasteners_Seals_Consumables",
                p.MATERIAL_INTENTS["Steel_Hardware"],
                "CompetitorOfficial",
                "M4x14 VESA fastener; clamps external mount + rear cover to VESA boss",
                "Suppress",
            ),
        )
        add_property(
            fastener,
            "App::PropertyString",
            "ClampedStack",
            "Rear_Enclosure|VESA_Boss_{:02d}".format(index),
        )
        add_property(fastener, "App::PropertyString", "TargetHost", "VESA_Boss_{:02d}".format(index))
        set_external_standard(fastener, "ISO 4762 M4 socket-head (VESA-mount fastener)")
        parts.append(fastener)

    for name, label, slots, part_id in (
        ("Inlet_Vent_Field", "Lower Rear Inlet Field", inlet_slots, "HNK-RF-001"),
        ("Outlet_Vent_Field", "Upper Rear Outlet Field", outlet_slots, "HNK-RF-002"),
    ):
        reference = semantic_part(
            doc,
            reference_group,
            name,
            label,
            Part.makeCompound(slots),
            metadata(
                part_id,
                name,
                "08_Reference_Datums_Keepouts",
                "Opening reference",
                "Known",
                VENT_SOURCE,
                "Keep",
            ),
        )
        add_area(reference, "OpenArea", 6000.0)

    return parts


def build_display_housing(doc, groups):
    parts = []
    parts.extend(build_display_stack(doc, groups))
    parts.extend(build_housing_shell(doc, groups))
    return parts
