"""Electronics and passive thermal-path geometry for the LOD 3 master."""

import Part

import hinoki_lod3_parameters as p
from hinoki_lod3_common import add_dimension, add_property, semantic_part, vector


SOURCE = "Approved LOD 3 design sections 6.2 and 6.5"
SOURCE_BOARDS = "Approved LOD 3 design section 6.2; carrier/compute/power/IO board envelopes"
SOURCE_SHIELDS = "Approved LOD 3 design section 6.5; EMI shield cans over SOM/Power/IO"
SOURCE_CONNECTORS = "Approved LOD 3 design section 6.2; connector effective solids"
SOURCE_HEAT = "Approved LOD 3 design sections 6.2 and 6.5; heat-source proxy solids"
SOURCE_THERMAL_PATH = (
    "Approved LOD 3 design section 6.5; QC7790 die-to-rear-cover conduction chain"
)

BOARD_POSITIONS = {
    "Carrier_PCB": (246.0, 176.0, 27.0),
    "Compute_SOM_PCB": (326.0, 211.0, 28.6),
    "Power_PCB": (55.0, 176.0, 27.0),
    "IO_PCB": (281.0, 106.0, 27.0),
    "WiFi_BLE_Module": (652.0, 215.0, 27.0),
}
CONNECTOR_SPECS = {
    "Carrier_BoardToBoard_Connector": (
        (30.0, 8.0, 5.0),
        (356.0, 200.0, 28.6),
    ),
    "Power_Input_Connector": ((24.0, 12.0, 8.0), (68.0, 210.0, 28.6)),
    "Display_FFC_Connector": ((42.0, 6.0, 4.0), (350.0, 306.0, 28.6)),
    "IO_Harness_Connector": ((38.0, 8.0, 5.0), (352.0, 126.0, 28.6)),
}
# Heat boxes and thermal shapes extended by 0.1..0.4 mm in Z so adjacent
# components in the die->rear-cover conduction chain have a positive
# authorised contact volume (>= 0.01 mm^3 threshold).
HEAT_BOX_SPECS = {
    "Heat_Memory": ((22.0, 16.0, 2.0), (294.0, 228.0, 30.2)),
    "Heat_IO": ((35.0, 20.0, 3.0), (353.5, 111.0, 28.6)),
}
THERMAL_BOX_SPECS = {
    "Copper_Spreader": ((100.0, 80.0, 2.2), (321.0, 206.0, 33.2)),
    # Aluminum_Interface reshaped to reach up to Rear_Hatch_TIM (was
    # 2.5 mm thick pancake at z=41.2..43.7 with a 11 mm air gap to TIM;
    # now a 13.9 mm heatsink block at z=41.2..55.1 with a shield-can
    # clearance hole cut for the SOM shield can).
    "Aluminum_Interface": ((128.0, 120.0, 13.9), (307.0, 186.0, 41.2)),
}
ALUMINUM_INTERFACE_SHIELD_CUTOUT = ((84.0, 64.0, 4.4), (329.0, 214.0, 43.5))
HEAT_PIPE_SPECS = {
    "Heat_Pipe_Left": (3.0, 160.0, (291.0, 224.0, 38.3)),
    "Heat_Pipe_Right": (3.0, 160.0, (291.0, 268.0, 38.3)),
}


def metadata(part_id, name, material, source="EngineeringAssumption", load=0.0,
             source_reference=None):
    return p.part_metadata(
        part_id=part_id,
        part_name=name,
        parent_assembly="03_Electronics_Thermal",
        material_intent=material,
        source_class=source,
        source_reference=source_reference or SOURCE,
        confidence="Medium",
        thermal_disposition="Keep",
        heat_load_w=load,
    )


def board_shape(width, height, thickness, x, y, z):
    board = Part.makeBox(width, height, thickness, vector(x, y, z))
    inset = 5.0
    cutters = [
        Part.makeCylinder(1.6, thickness + 0.2, vector(px, py, z - 0.1))
        for px, py in (
            (x + inset, y + inset),
            (x + width - inset, y + inset),
            (x + inset, y + height - inset),
            (x + width - inset, y + height - inset),
        )
    ]
    return board.cut(Part.makeCompound(cutters))


def expanded_box(dimensions, position, clearance):
    width, height, depth = dimensions
    x, y, z = position
    return Part.makeBox(
        width + 2.0 * clearance,
        height + 2.0 * clearance,
        depth + 2.0 * clearance,
        vector(x - clearance, y - clearance, z - clearance),
    )


def expanded_connector_shape(name):
    return expanded_box(
        *CONNECTOR_SPECS[name],
        p.COLLISION_CLEARANCE["linear"]
    )


def housing_keepout_shapes(clearance):
    boxes = [
        expanded_box(*CONNECTOR_SPECS["Power_Input_Connector"], clearance),
        expanded_box(*HEAT_BOX_SPECS["Heat_Memory"], clearance),
        expanded_box(*THERMAL_BOX_SPECS["Aluminum_Interface"], clearance),
    ]
    pipes = [
        Part.makeCylinder(
            radius + clearance,
            length + 2.0 * clearance,
            vector(position[0] - clearance, position[1], position[2]),
            vector(1.0, 0.0, 0.0),
        )
        for radius, length, position in HEAT_PIPE_SPECS.values()
    ]
    return boxes + pipes


def open_shield_shape(dimensions, position, connector_clearance=None):
    width, height, depth = dimensions
    x, y, z = position
    wall = p.COLLISION_CLEARANCE["shield_wall"]
    outer = Part.makeBox(width, height, depth, vector(x, y, z))
    inner = Part.makeBox(
        width - 2.0 * wall,
        height - 2.0 * wall,
        depth - wall + 0.1,
        vector(x + wall, y + wall, z - 0.1),
    )
    shape = outer.cut(inner)
    if connector_clearance is not None:
        shape = shape.cut(connector_clearance)
    return shape


def add_heat_source(obj, source_name, load):
    add_property(obj, "App::PropertyString", "HeatSourceID", source_name)
    obj.HeatLoadW = float(load)


def build_electronics_thermal(doc, groups):
    group = groups["03_Electronics_Thermal"]
    parts = []
    for index, (name, position) in enumerate(BOARD_POSITIONS.items(), start=1):
        dimensions = p.BOARD_ENVELOPES[name]
        obj = semantic_part(
            doc,
            group,
            name,
            name.replace("_", " "),
            board_shape(
                dimensions["width"],
                dimensions["height"],
                dimensions["thickness"],
                position[0],
                position[1],
                position[2],
            ),
            metadata(
                "HNK-ET-{:03d}".format(index),
                name,
                p.MATERIAL_INTENTS["PCB"],
                "EngineeringAssumption",
                source_reference=SOURCE_BOARDS,
            ),
        )
        parts.append(obj)

    compute = doc.getObject("Compute_SOM_PCB")
    carrier = doc.getObject("Carrier_PCB")
    wifi = doc.getObject("WiFi_BLE_Module")
    add_heat_source(wifi, "Heat_WiFi_BLE", p.HEAT_LOADS_W["Heat_WiFi_BLE"])

    head = p.HEAD
    camera = p.CAMERA_LIGHT_SENSOR["Camera_Module"]
    barrel = p.CAMERA_LIGHT_SENSOR["Camera_Barrel"]
    light_gap = (barrel["width"] - camera["width"]) / 2.0
    light_positions = {
        "Front_Light_Left": (
            head["width"] / 2.0
            - barrel["width"] / 2.0
            - p.CAMERA_LIGHT_SENSOR["Front_Light_Left"]["width"]
            - light_gap
        ),
        "Front_Light_Right": (
            head["width"] / 2.0
            - barrel["width"] / 2.0
            + barrel["width"]
            + light_gap
        ),
    }
    lighting_heat_shape = Part.makeCompound(
        [
            Part.makeBox(
                p.CAMERA_LIGHT_SENSOR[name]["width"],
                p.CAMERA_LIGHT_SENSOR[name]["height"],
                p.CAMERA_LIGHT_SENSOR[name]["depth"],
                vector(
                    light_positions[name],
                    head["height"] - p.CAMERA_LIGHT_SENSOR[name]["height"],
                    0.0,
                ),
            )
            for name in ("Front_Light_Left", "Front_Light_Right")
        ]
    )

    heat_shapes = {
        "Heat_QC7790": Part.makeBox(35.0, 35.0, 2.1, vector(353.5, 228.5, 30.2)),
        "Heat_Memory": Part.makeBox(
            *HEAT_BOX_SPECS["Heat_Memory"][0],
            vector(*HEAT_BOX_SPECS["Heat_Memory"][1])
        ),
        "Heat_Carrier_PMIC": Part.makeBox(18.0, 18.0, 2.0, vector(420.0, 230.0, 28.6)),
        "Heat_IO": Part.makeBox(
            *HEAT_BOX_SPECS["Heat_IO"][0],
            vector(*HEAT_BOX_SPECS["Heat_IO"][1])
        ).cut(expanded_connector_shape("IO_Harness_Connector")),
        "Heat_Camera": Part.makeBox(38.0, 18.0, 4.0, vector(352.0, 443.0, 27.0)),
        "Heat_Audio": Part.makeBox(60.0, 20.0, 4.0, vector(80.0, 86.0, 27.0)),
        "Heat_Radar_ALS": Part.makeBox(59.8, 18.0, 3.0, vector(341.1, 63.0, 27.0)),
        "Heat_Front_Lighting": lighting_heat_shape,
    }
    for index, (name, shape) in enumerate(heat_shapes.items(), start=20):
        obj = semantic_part(
            doc,
            group,
            name,
            name.replace("_", " "),
            shape,
            metadata(
                "HNK-ET-{:03d}".format(index),
                name,
                "Effective isotropic electronic package",
                "EngineeringAssumption",
                p.HEAT_LOADS_W[name],
                source_reference=SOURCE_HEAT,
            ),
        )
        add_heat_source(obj, name, p.HEAT_LOADS_W[name])
        if name == "Heat_Camera":
            add_property(
                obj,
                "App::PropertyStringList",
                "AuthorizedContactTargets",
                ["Camera_Module"],
            )
        elif name == "Heat_Front_Lighting":
            add_property(
                obj,
                "App::PropertyStringList",
                "AuthorizedContactTargets",
                ["Front_Light_Left", "Front_Light_Right"],
            )
        elif name == "Heat_QC7790":
            add_property(
                obj,
                "App::PropertyStringList",
                "AuthorizedContactTargets",
                ["TIM_QC7790"],
            )
        parts.append(obj)

    # Panel Module (20 W total) split into four discrete physical heat
    # sources, each attached to its own physical solid built in
    # hinoki_lod3_display_housing.py. Original 20 W envelope preserved.
    panel_heat_bindings = (
        ("LED_Bar_Bottom", "Heat_BLU_LED"),
        ("BLU_Driver_PCB", "Heat_BLU_Driver"),
        ("TCON_IC", "Heat_TCON"),
        ("Panel_Gate_Source_Driver", "Heat_Panel_Gate_Source"),
    )
    panel_bound_watts = 0.0
    for host_name, source_id in panel_heat_bindings:
        host = doc.getObject(host_name)
        if host is None:
            raise RuntimeError(
                "Panel heat host missing: {}".format(host_name)
            )
        add_heat_source(host, source_id, p.HEAT_LOADS_W[source_id])
        panel_bound_watts += float(p.HEAT_LOADS_W[source_id])
    if abs(panel_bound_watts - p.PANEL_MODULE_BUDGET_W) > 1e-6:
        raise RuntimeError(
            "Panel module budget mismatch: bound={} expected={}".format(
                panel_bound_watts, p.PANEL_MODULE_BUDGET_W
            )
        )

    aluminum_dims, aluminum_pos = THERMAL_BOX_SPECS["Aluminum_Interface"]
    aluminum_solid = Part.makeBox(*aluminum_dims, vector(*aluminum_pos))
    shield_dims, shield_pos = ALUMINUM_INTERFACE_SHIELD_CUTOUT
    shield_cutter = Part.makeBox(*shield_dims, vector(*shield_pos))
    aluminum_shape = aluminum_solid.cut(shield_cutter)

    thermal_shapes = {
        # TIM_QC7790 thickened to 1.2 mm so it overlaps Heat_QC7790 (0.1 mm)
        # and Copper_Spreader (0.2 mm) for declared contact evidence.
        "TIM_QC7790": Part.makeBox(35.0, 35.0, 1.2, vector(353.5, 228.5, 32.2)),
        "Copper_Spreader": Part.makeBox(
            *THERMAL_BOX_SPECS["Copper_Spreader"][0],
            vector(*THERMAL_BOX_SPECS["Copper_Spreader"][1])
        ).cut(expanded_connector_shape("Carrier_BoardToBoard_Connector")),
        "Heat_Pipe_Left": Part.makeCylinder(
            HEAT_PIPE_SPECS["Heat_Pipe_Left"][0],
            HEAT_PIPE_SPECS["Heat_Pipe_Left"][1],
            vector(*HEAT_PIPE_SPECS["Heat_Pipe_Left"][2]),
            vector(1.0, 0.0, 0.0),
        ),
        "Heat_Pipe_Right": Part.makeCylinder(
            HEAT_PIPE_SPECS["Heat_Pipe_Right"][0],
            HEAT_PIPE_SPECS["Heat_Pipe_Right"][1],
            vector(*HEAT_PIPE_SPECS["Heat_Pipe_Right"][2]),
            vector(1.0, 0.0, 0.0),
        ),
        "Aluminum_Interface": aluminum_shape,
        # Rear_Hatch_TIM thickened to 5.4 mm (z=54.7..60.1) so it bridges
        # Aluminum_Interface (top z=55.1, overlap 0.4 mm) to Rear_IO_Cover
        # (inner face z=60.0, overlap 0.1 mm). The main rear back wall has a
        # service cutout at this location; heat exits via the removable I/O
        # cover, which sits flush with the head envelope at z=62.
        "Rear_Hatch_TIM": Part.makeBox(80.0, 40.0, 5.4, vector(331.0, 226.0, 54.7)),
    }
    materials = {
        "TIM_QC7790": "Isotropic TIM; k=3 W/m-K",
        "Copper_Spreader": p.MATERIAL_INTENTS["Thermal_Copper"],
        "Heat_Pipe_Left": p.MATERIAL_INTENTS["Heat_Pipe"],
        "Heat_Pipe_Right": p.MATERIAL_INTENTS["Heat_Pipe"],
        "Aluminum_Interface": p.MATERIAL_INTENTS["Aluminum_Heatsink"],
        "Rear_Hatch_TIM": "Isotropic TIM; k=8 W/m-K",
    }
    thermal_authorized_contacts = {
        "TIM_QC7790": ["Heat_QC7790", "Copper_Spreader"],
        "Copper_Spreader": ["TIM_QC7790", "Heat_Pipe_Left", "Heat_Pipe_Right"],
        "Heat_Pipe_Left": ["Copper_Spreader", "Aluminum_Interface"],
        "Heat_Pipe_Right": ["Copper_Spreader", "Aluminum_Interface"],
        "Aluminum_Interface": [
            "Heat_Pipe_Left",
            "Heat_Pipe_Right",
            "Rear_Hatch_TIM",
        ],
        "Rear_Hatch_TIM": ["Aluminum_Interface", "Rear_IO_Cover"],
    }
    thermal_conductivity_wmk = {
        "TIM_QC7790": 3.0,
        "Copper_Spreader": 400.0,
        "Heat_Pipe_Left": 8000.0,
        "Heat_Pipe_Right": 8000.0,
        "Aluminum_Interface": 167.0,
        "Rear_Hatch_TIM": 8.0,
    }
    for index, (name, shape) in enumerate(thermal_shapes.items(), start=40):
        obj = semantic_part(
            doc,
            group,
            name,
            name.replace("_", " "),
            shape,
            metadata(
                "HNK-ET-{:03d}".format(index),
                name,
                materials[name],
                "DixieReference",
                source_reference=SOURCE_THERMAL_PATH,
            ),
        )
        if name.startswith("Heat_Pipe"):
            add_dimension(obj, "Diameter", 6.0)
        if name in thermal_conductivity_wmk:
            add_dimension(obj, "ThermalConductivityWmK", thermal_conductivity_wmk[name])
        targets = thermal_authorized_contacts.get(name)
        if targets:
            add_property(
                obj,
                "App::PropertyStringList",
                "AuthorizedContactTargets",
                targets,
            )
        parts.append(obj)

    # Rear_IO_Cover is the customer-serviceable thermal exit face; declare
    # its symmetric authorized contact with Rear_Hatch_TIM.
    io_cover = doc.getObject("Rear_IO_Cover")
    if io_cover is not None:
        existing = list(getattr(io_cover, "AuthorizedContactTargets", []) or [])
        if "Rear_Hatch_TIM" not in existing:
            existing.append("Rear_Hatch_TIM")
        add_property(
            io_cover,
            "App::PropertyStringList",
            "AuthorizedContactTargets",
            existing,
        )

    for index, (name, dimensions, position) in enumerate(
        (
            ("SOM_Shield_Can", (82.0, 62.0, 4.0), (330.0, 215.0, 43.7)),
            ("Power_Shield_Can", (72.0, 52.0, 4.0), (90.0, 200.0, 30.0)),
            ("IO_Shield_Can", (60.0, 22.0, 4.0), (341.0, 110.0, 31.6)),
        ),
        start=60,
    ):
        connector_clearance = None
        if name == "Power_Shield_Can":
            connector_clearance = expanded_connector_shape(
                "Power_Input_Connector"
            )
        elif name == "IO_Shield_Can":
            connector_clearance = expanded_connector_shape(
                "IO_Harness_Connector"
            )
        obj = semantic_part(
            doc,
            group,
            name,
            name.replace("_", " "),
            open_shield_shape(dimensions, position, connector_clearance),
            metadata(
                "HNK-ET-{:03d}".format(index),
                name,
                p.MATERIAL_INTENTS["Sheet_Bracket_Shield"],
                "DixieReference",
                source_reference=SOURCE_SHIELDS,
            ),
        )
        parts.append(obj)

    for index, (name, spec) in enumerate(CONNECTOR_SPECS.items(), start=70):
        dimensions, position = spec
        parts.append(
            semantic_part(
                doc,
                group,
                name,
                name.replace("_", " "),
                Part.makeBox(*dimensions, vector(*position)),
                metadata(
                    "HNK-ET-{:03d}".format(index),
                    name,
                    "Connector effective solid",
                    "DixieReference",
                    source_reference=SOURCE_CONNECTORS,
                ),
            )
        )

    # Cut VESA boss clearance holes from electronics that span the boss
    # z-range. Bosses at VESA_MOUNT_POINTS radius vesa_boss_od/2 need
    # matching clearance holes in PCBs and heat spreaders so the mid-frame
    # bosses can pass through cleanly.
    vesa_boss_radius = p.HOUSING["vesa_boss_od"] / 2.0
    vesa_clearance_radius = vesa_boss_radius + p.COLLISION_CLEARANCE["radial"]
    for board_name in ("Carrier_PCB", "Aluminum_Interface"):
        target = doc.getObject(board_name)
        if target is None:
            continue
        bbox = target.Shape.BoundBox
        cutters = [
            Part.makeCylinder(
                vesa_clearance_radius,
                bbox.ZLength + 1.0,
                vector(vx, vy, bbox.ZMin - 0.5),
            )
            for vx, vy in p.VESA_MOUNT_POINTS
        ]
        target.Shape = target.Shape.cut(Part.makeCompound(cutters))

    return parts
