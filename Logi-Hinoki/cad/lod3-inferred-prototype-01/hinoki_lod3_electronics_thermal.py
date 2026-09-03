"""Electronics and passive thermal-path geometry for the LOD 3 master."""

import Part

import hinoki_lod3_parameters as p
from hinoki_lod3_common import add_dimension, add_property, semantic_part, vector


SOURCE = "Approved LOD 3 design sections 6.2 and 6.5"
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
HEAT_BOX_SPECS = {
    "Heat_Memory": ((22.0, 16.0, 2.0), (294.0, 228.0, 30.2)),
    "Heat_IO": ((35.0, 20.0, 3.0), (353.5, 111.0, 28.6)),
}
THERMAL_BOX_SPECS = {
    "Copper_Spreader": ((100.0, 80.0, 2.0), (321.0, 206.0, 33.2)),
    "Aluminum_Interface": ((220.0, 120.0, 2.5), (261.0, 186.0, 41.2)),
}
HEAT_PIPE_SPECS = {
    "Heat_Pipe_Left": (3.0, 160.0, (291.0, 224.0, 38.2)),
    "Heat_Pipe_Right": (3.0, 160.0, (291.0, 268.0, 38.2)),
}


def metadata(part_id, name, material, source="EngineeringAssumption", load=0.0):
    return p.part_metadata(
        part_id=part_id,
        part_name=name,
        parent_assembly="03_Electronics_Thermal",
        material_intent=material,
        source_class=source,
        source_reference=SOURCE,
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
        "Heat_QC7790": Part.makeBox(35.0, 35.0, 2.0, vector(353.5, 228.5, 30.2)),
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
        parts.append(obj)

    backlight = doc.getObject("Backlight_Unit")
    add_heat_source(
        backlight,
        "Heat_Panel_Backlight",
        p.HEAT_LOADS_W["Heat_Panel_Backlight"],
    )

    thermal_shapes = {
        "TIM_QC7790": Part.makeBox(35.0, 35.0, 1.0, vector(353.5, 228.5, 32.2)),
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
        "Aluminum_Interface": Part.makeBox(
            *THERMAL_BOX_SPECS["Aluminum_Interface"][0],
            vector(*THERMAL_BOX_SPECS["Aluminum_Interface"][1])
        ),
        "Rear_Hatch_TIM": Part.makeBox(80.0, 40.0, 1.5, vector(331.0, 226.0, 54.7)),
    }
    materials = {
        "TIM_QC7790": "Isotropic TIM; k=3 W/m-K",
        "Copper_Spreader": p.MATERIAL_INTENTS["Thermal_Copper"],
        "Heat_Pipe_Left": p.MATERIAL_INTENTS["Thermal_Copper"],
        "Heat_Pipe_Right": p.MATERIAL_INTENTS["Thermal_Copper"],
        "Aluminum_Interface": p.MATERIAL_INTENTS["Aluminum_Structure"],
        "Rear_Hatch_TIM": "Isotropic TIM; k=8 W/m-K",
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
            ),
        )
        if name.startswith("Heat_Pipe"):
            add_dimension(obj, "Diameter", 6.0)
        parts.append(obj)

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
                ),
            )
        )

    return parts
