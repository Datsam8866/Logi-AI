"""Display-stack and enclosure geometry for the Hinoki LOD 3 master."""

import Part

import hinoki_lod3_parameters as p
from hinoki_lod3_common import (
    add_area,
    add_dimension,
    centred_offset,
    semantic_part,
    vector,
)
from hinoki_lod3_electronics_thermal import housing_keepout_shapes


DISPLAY_SOURCE = "Approved LOD 3 design section 5.1"
HOUSING_SOURCE = "Dixie DFM-informed Hinoki assumption; design section 5.1"
VENT_SOURCE = "Approved lower/rear-lower inlet and upper-rear outlet topology"


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


def box_from_dimensions(dimensions, z):
    x = centred_offset(p.HEAD["width"], dimensions["width"])
    y = centred_offset(p.HEAD["height"], dimensions["height"])
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


def vesa_reinforcement_shape():
    shape = Part.makeBox(140.0, 140.0, 3.0, vector(301.0, 176.0, 56.2))
    radius = (
        p.HOUSING["primary_boss_od"] / 2.0
        + p.COLLISION_CLEARANCE["radial"]
    )
    cutters = [
        Part.makeCylinder(radius, 3.2, vector(x, y, 56.1))
        for x, y in p.VESA_MOUNT_POINTS
    ]
    return shape.cut(Part.makeCompound(cutters))


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


def build_rear_enclosure():
    wall = p.HOUSING["rear_wall"]
    rear_z = p.HEAD["depth"] - wall
    back = Part.makeBox(
        p.HEAD["width"], p.HEAD["height"], wall, vector(0.0, 0.0, rear_z)
    )
    inlet_slots = vent_slots(30.0, rear_z - 0.2)
    outlet_slots = vent_slots(p.HEAD["height"] - 55.0, rear_z - 0.2)
    service_cutout = Part.makeBox(
        220.0, 80.0, wall + 0.4, vector(261.0, 206.0, rear_z - 0.2)
    )
    back = back.cut(Part.makeCompound(inlet_slots + outlet_slots + [service_cutout]))

    shell_depth = rear_z - 19.0
    left = Part.makeBox(wall, p.HEAD["height"], shell_depth, vector(0.0, 0.0, 19.0))
    right = Part.makeBox(
        wall,
        p.HEAD["height"],
        shell_depth,
        vector(p.HEAD["width"] - wall, 0.0, 19.0),
    )
    bottom = Part.makeBox(
        p.HEAD["width"] - 2.0 * wall,
        wall,
        shell_depth,
        vector(wall, 0.0, 19.0),
    )
    top = Part.makeBox(
        p.HEAD["width"] - 2.0 * wall,
        wall,
        shell_depth,
        vector(wall, p.HEAD["height"] - wall, 19.0),
    )
    return back.fuse(left).fuse(right).fuse(bottom).fuse(top), inlet_slots, outlet_slots


def build_display_housing(doc, groups):
    display_group = groups["01_Display_Stack"]
    housing_group = groups["02_Housing_Structure"]
    fastener_group = groups["07_Fasteners_Seals_Consumables"]
    reference_group = groups["08_Reference_Datums_Keepouts"]
    parts = []

    front_frame = semantic_part(
        doc,
        housing_group,
        "Front_Frame",
        "Front Frame",
        ring(742.0, 492.0, 726.0, 446.0, 3.2, 0.0),
        metadata(
            "HNK-HS-001",
            "Front_Frame",
            "02_Housing_Structure",
            p.MATERIAL_INTENTS["Housing_Polymer"],
            "EngineeringAssumption",
            HOUSING_SOURCE,
        ),
    )
    parts.append(front_frame)

    z_positions = {
        "Cover_Glass": 0.0,
        "PCAP_Sensor": 3.2,
        "Optical_Bond": 4.0,
        "LCD_Cell": 4.5,
        "Backlight_Unit": 7.0,
    }
    material_map = {
        "Cover_Glass": p.MATERIAL_INTENTS["Display_Glass"],
        "PCAP_Sensor": "FLOEFD equivalent PCAP sensor",
        "Optical_Bond": "Optically clear adhesive equivalent",
        "LCD_Cell": "FLOEFD equivalent LCD cell",
        "Backlight_Unit": "FLOEFD equivalent display backlight",
    }
    for index, name in enumerate(z_positions, start=1):
        parts.append(
            semantic_part(
                doc,
                display_group,
                name,
                name.replace("_", " "),
                box_from_dimensions(p.DISPLAY_STACK[name], z_positions[name]),
                metadata(
                    "HNK-DS-{:03d}".format(index),
                    name,
                    "01_Display_Stack",
                    material_map[name],
                    "Derived" if name == "Cover_Glass" else "EngineeringAssumption",
                    DISPLAY_SOURCE,
                ),
            )
        )

    display_carrier = semantic_part(
        doc,
        display_group,
        "Display_Carrier",
        "Display Carrier",
        ring(722.0, 412.0, 704.0, 394.0, 2.0, 19.0),
        metadata(
            "HNK-DS-006",
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
            "HNK-DS-007",
            "TCON_PCB",
            "01_Display_Stack",
            p.MATERIAL_INTENTS["PCB"],
            "EngineeringAssumption",
            "Display-stack packaging assumption; design section 6.1",
        ),
    )
    parts.append(tcon)

    mid_frame = semantic_part(
        doc,
        housing_group,
        "Metal_Mid_Frame",
        "Metal Mid Frame",
        ring(730.0, 450.0, 700.0, 390.0, 2.0, 23.0),
        metadata(
            "HNK-HS-002",
            "Metal_Mid_Frame",
            "02_Housing_Structure",
            p.MATERIAL_INTENTS["Aluminum_Structure"],
            "DixieReference",
            "Dixie metal-frame architecture; Hinoki parametric rebuild",
        ),
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

    vesa_reinforcement = semantic_part(
        doc,
        housing_group,
        "VESA_Reinforcement",
        "VESA Reinforcement",
        vesa_reinforcement_shape(),
        metadata(
            "HNK-HS-005",
            "VESA_Reinforcement",
            "02_Housing_Structure",
            p.MATERIAL_INTENTS["Sheet_Bracket_Shield"],
            "CompetitorOfficial",
            "Neat Board 32 VESA benchmark; approved 100 x 100 interface",
        ),
    )
    parts.append(vesa_reinforcement)

    rib_keepouts = Part.makeCompound(
        housing_keepout_shapes(p.COLLISION_CLEARANCE["linear"])
    )
    for index, x in enumerate((80.0, 196.0, 312.0, 428.0, 544.0, 660.0), start=1):
        rib_shape = Part.makeBox(
            p.HOUSING["structural_rib"],
            360.0,
            22.0,
            vector(x, 66.0, 32.0),
        ).cut(rib_keepouts)
        rib = semantic_part(
            doc,
            housing_group,
            "Structural_Rib_{:02d}".format(index),
            "Structural Rib {:02d}".format(index),
            rib_shape,
            metadata(
                "HNK-HS-{:03d}".format(10 + index),
                "Structural_Rib_{:02d}".format(index),
                "02_Housing_Structure",
                p.MATERIAL_INTENTS["Housing_Polymer"],
                "Derived",
                "0.6 x nominal-wall DFM rule; design section 5.1",
                "Aggregate",
            ),
        )
        add_dimension(rib, "RibThickness", p.HOUSING["structural_rib"])
        parts.append(rib)

    boss_positions = (
        (40.0, 40.0),
        (702.0, 40.0),
        (40.0, 452.0),
        (702.0, 452.0),
    ) + p.VESA_MOUNT_POINTS
    for index, (x, y) in enumerate(boss_positions, start=1):
        boss_z = (
            27.0
            if index <= 4
            else p.COLLISION_CLEARANCE["rear_boss_z"]
        )
        boss_height = (
            30.0
            if index <= 4
            else p.COLLISION_CLEARANCE["rear_boss_height"]
        )
        boss_shape = Part.makeCylinder(
            p.HOUSING["primary_boss_od"] / 2.0,
            boss_height,
            vector(x, y, boss_z),
        ).cut(
            Part.makeCylinder(
                1.6,
                boss_height + 0.2,
                vector(x, y, boss_z - 0.1),
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
                p.MATERIAL_INTENTS["Housing_Polymer"],
                "DixieReference",
                HOUSING_SOURCE,
                "Aggregate",
            ),
        )
        add_dimension(boss, "BossOuterDiameter", p.HOUSING["primary_boss_od"])
        parts.append(boss)

        fastener = semantic_part(
            doc,
            fastener_group,
            "M3_Fastener_{:02d}".format(index),
            "M3 Fastener {:02d}".format(index),
            Part.makeCylinder(1.5, 6.0, vector(x, y, 51.0)),
            metadata(
                "HNK-FS-{:03d}".format(index),
                "M3_Fastener_{:02d}".format(index),
                "07_Fasteners_Seals_Consumables",
                p.MATERIAL_INTENTS["Steel_Hardware"],
                "DixieReference",
                "Nominal M3 hardware pattern; helical thread suppressed",
                "Suppress",
            ),
        )
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
