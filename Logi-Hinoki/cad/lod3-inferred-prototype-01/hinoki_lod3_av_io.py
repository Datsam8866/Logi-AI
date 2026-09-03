"""Camera, lighting, sensor, audio, I/O, and cable geometry."""

import Part

import hinoki_lod3_parameters as p
from hinoki_lod3_common import add_dimension, add_property, semantic_part, vector


SOURCE = "Approved LOD 3 design sections 6.2 through 6.4"
BEND_INTENT = (
    "Minimum bend radius pending selected cable and connector data; "
    "preserve this labelled obstruction envelope per DR-13."
)


def metadata(
    part_id,
    name,
    parent,
    material,
    source_class="EngineeringAssumption",
    disposition="Keep",
):
    return p.part_metadata(
        part_id=part_id,
        part_name=name,
        parent_assembly=parent,
        material_intent=material,
        source_class=source_class,
        source_reference=SOURCE,
        confidence="Medium",
        thermal_disposition=disposition,
    )


def add_role(obj, role):
    add_property(obj, "App::PropertyString", "GeometryRole", role)
    return obj


def make_segmented_path(points, radius):
    solids = [Part.makeSphere(radius, vector(*point)) for point in points]
    for start, finish in zip(points, points[1:]):
        start_vector = vector(*start)
        direction = vector(
            finish[0] - start[0],
            finish[1] - start[1],
            finish[2] - start[2],
        )
        if direction.Length > 0.0:
            solids.append(
                Part.makeCylinder(radius, direction.Length, start_vector, direction)
            )
    return Part.makeCompound(solids)


def add_keepout(doc, group, part_id, name, shape, role):
    obj = semantic_part(
        doc,
        group,
        name,
        name.replace("_", " "),
        shape,
        metadata(
            part_id,
            name,
            "08_Reference_Datums_Keepouts",
            "Reference-only spatial allocation",
            disposition="Suppress",
        ),
    )
    return add_role(obj, role)


def build_camera_lighting_sensors(doc, groups):
    group = groups["04_Camera_Lighting_Sensors"]
    keepouts = groups["08_Reference_Datums_Keepouts"]
    parts = []
    head = p.HEAD
    camera = p.CAMERA_LIGHT_SENSOR["Camera_Module"]
    barrel = p.CAMERA_LIGHT_SENSOR["Camera_Barrel"]
    centre_x = head["width"] / 2.0
    barrel_x = centre_x - barrel["width"] / 2.0
    barrel_y = head["height"] - barrel["height"]

    camera_obj = semantic_part(
        doc,
        group,
        "Camera_Module",
        "Camera Module",
        Part.makeBox(
            camera["width"],
            camera["height"],
            camera["depth"],
            vector(
                centre_x - camera["width"] / 2.0,
                head["height"] - camera["height"],
                0.0,
            ),
        ),
        metadata(
            "HNK-AV-001",
            "Camera_Module",
            "04_Camera_Lighting_Sensors",
            "Camera PCB and optics package",
            "CompetitorOfficial",
        ),
    )
    add_dimension(camera_obj, "Width", camera["width"])
    add_dimension(camera_obj, "Height", camera["height"])
    add_dimension(camera_obj, "Depth", camera["depth"])
    parts.append(camera_obj)

    barrel_obj = semantic_part(
        doc,
        group,
        "Camera_Barrel",
        "Camera Barrel",
        Part.makeBox(
            barrel["width"],
            barrel["height"],
            barrel["depth"],
            vector(barrel_x, barrel_y, 0.0),
        ),
        metadata(
            "HNK-AV-002",
            "Camera_Barrel",
            "04_Camera_Lighting_Sensors",
            "Inferred camera barrel assembly",
        ),
    )
    for name in ("width", "height", "depth"):
        add_dimension(barrel_obj, name.title(), barrel[name])
    parts.append(barrel_obj)

    shutter_thickness = p.BOARD_ENVELOPES["IO_PCB"]["thickness"]
    shutter_width = camera["width"] / 2.0
    shutter_height = camera["height"] / 2.0
    shutter_travel = camera["width"]
    shutter_x = centre_x - shutter_width / 2.0
    shutter_y = barrel_y + (barrel["height"] - shutter_height) / 2.0
    shutter = semantic_part(
        doc,
        group,
        "Privacy_Shutter",
        "Captive Privacy Shutter",
        Part.makeBox(
            shutter_width,
            shutter_height,
            shutter_thickness,
            vector(shutter_x, shutter_y, 0.0),
        ),
        metadata(
            "HNK-AV-003",
            "Privacy_Shutter",
            "04_Camera_Lighting_Sensors",
            p.MATERIAL_INTENTS["Housing_Polymer"],
        ),
    )
    add_property(shutter, "App::PropertyBool", "Captive", True)
    add_dimension(shutter, "Travel", shutter_travel)
    add_property(shutter, "App::PropertyString", "ClosedPosition", "Optics obscured")
    add_property(shutter, "App::PropertyString", "OpenPosition", "Optics clear")
    parts.append(shutter)

    travel_shape = Part.makeBox(
        shutter_width + shutter_travel,
        shutter_height,
        shutter_thickness,
        vector(shutter_x, shutter_y, 0.0),
    )
    add_keepout(
        doc,
        keepouts,
        "HNK-KO-101",
        "Shutter_Travel_Envelope",
        travel_shape,
        "MotionKeepout",
    )
    for index, stop_x in enumerate(
        (shutter_x - shutter_thickness, shutter_x + shutter_width + shutter_travel),
        start=1,
    ):
        parts.append(
            semantic_part(
                doc,
                group,
                "Shutter_End_Stop_{}".format("Left" if index == 1 else "Right"),
                "Shutter End Stop {}".format("Left" if index == 1 else "Right"),
                Part.makeBox(
                    shutter_thickness,
                    shutter_height,
                    shutter_thickness,
                    vector(stop_x, shutter_y, 0.0),
                ),
                metadata(
                    "HNK-AV-00{}".format(3 + index),
                    "Shutter_End_Stop_{}".format(
                        "Left" if index == 1 else "Right"
                    ),
                    "04_Camera_Lighting_Sensors",
                    p.MATERIAL_INTENTS["Housing_Polymer"],
                ),
            )
        )

    optical_shape = Part.makeCone(
        shutter_thickness,
        camera["width"] / 2.0,
        camera["depth"],
        vector(centre_x, head["height"] - camera["height"] / 2.0, 0.0),
        vector(0.0, 0.0, 1.0),
    )
    add_keepout(
        doc,
        keepouts,
        "HNK-KO-102",
        "Camera_Optical_Keepout",
        optical_shape,
        "OpticalKeepout",
    )

    light_gap = (barrel["width"] - camera["width"]) / 2.0
    light_positions = {
        "Front_Light_Left": barrel_x
        - p.CAMERA_LIGHT_SENSOR["Front_Light_Left"]["width"]
        - light_gap,
        "Front_Light_Right": barrel_x + barrel["width"] + light_gap,
    }
    for index, (name, light_x) in enumerate(light_positions.items(), start=10):
        dimensions = p.CAMERA_LIGHT_SENSOR[name]
        obj = semantic_part(
            doc,
            group,
            name,
            name.replace("_", " "),
            Part.makeBox(
                dimensions["width"],
                dimensions["height"],
                dimensions["depth"],
                vector(
                    light_x,
                    head["height"] - dimensions["height"],
                    0.0,
                ),
            ),
            metadata(
                "HNK-AV-{:03d}".format(index),
                name,
                "04_Camera_Lighting_Sensors",
                "Front lighting PCB and diffuser proxy",
            ),
        )
        for dimension in ("width", "height", "depth"):
            add_dimension(obj, dimension.title(), dimensions[dimension])
        parts.append(obj)

    radar = p.CAMERA_LIGHT_SENSOR["Radar_Holder"]
    radar_x = centre_x - radar["width"] / 2.0
    radar_obj = semantic_part(
        doc,
        group,
        "Radar_Holder",
        "Radar Holder",
        Part.makeBox(
            radar["width"],
            radar["height"],
            radar["depth"],
            vector(radar_x, 0.0, 0.0),
        ),
        metadata(
            "HNK-AV-020",
            "Radar_Holder",
            "04_Camera_Lighting_Sensors",
            p.MATERIAL_INTENTS["Housing_Polymer"],
        ),
    )
    for name in ("width", "height", "depth"):
        add_dimension(radar_obj, name.title(), radar[name])
    parts.append(radar_obj)

    als_radius = p.BOARD_ENVELOPES["IO_PCB"]["thickness"]
    als_path = add_keepout(
        doc,
        keepouts,
        "HNK-KO-103",
        "ALS_Optical_Path",
        Part.makeCylinder(
            als_radius,
            radar["depth"],
            vector(
                radar_x + radar["width"] + als_radius,
                radar["height"] / 2.0,
                0.0,
            ),
            vector(0.0, 0.0, 1.0),
        ),
        "OpticalKeepout",
    )
    add_property(als_path, "App::PropertyString", "SensorPath", "Independent ALS")
    return parts


def build_audio(doc, groups):
    group = groups["05_Audio_IO_Cables"]
    keepouts = groups["08_Reference_Datums_Keepouts"]
    parts = []
    head = p.HEAD
    barrel = p.CAMERA_LIGHT_SENSOR["Camera_Barrel"]
    speaker_depth = p.CAMERA_LIGHT_SENSOR["Front_Light_Left"]["depth"]
    speaker_diameter = p.AUDIO["Speaker_Left"]["diameter"]
    margin = (head["width"] - p.DISPLAY_STACK["Cover_Glass"]["width"]) / 2.0
    speaker_y = head["height"] - barrel["height"]
    positions = {
        "Left": margin,
        "Right": head["width"] - margin - speaker_diameter,
    }
    for index, (side, speaker_x) in enumerate(positions.items(), start=1):
        speaker_name = "Speaker_" + side
        speaker = semantic_part(
            doc,
            group,
            speaker_name,
            speaker_name.replace("_", " "),
            Part.makeCylinder(
                speaker_diameter / 2.0,
                speaker_depth,
                vector(
                    speaker_x + speaker_diameter / 2.0,
                    speaker_y + speaker_diameter / 2.0,
                    barrel["depth"],
                ),
                vector(0.0, 0.0, 1.0),
            ),
            metadata(
                "HNK-AU-00{}".format(index),
                speaker_name,
                "05_Audio_IO_Cables",
                "Full-range speaker assembly proxy",
            ),
        )
        add_dimension(speaker, "Diameter", speaker_diameter)
        parts.append(speaker)

        acoustic = add_keepout(
            doc,
            keepouts,
            "HNK-KO-11{}".format(index),
            speaker_name + "_Acoustic_Keepout",
            Part.makeCylinder(
                speaker_diameter / 2.0,
                head["depth"],
                vector(
                    speaker_x + speaker_diameter / 2.0,
                    speaker_y + speaker_diameter / 2.0,
                    0.0,
                ),
                vector(0.0, 0.0, 1.0),
            ),
            "AcousticKeepout",
        )
        add_property(
            acoustic,
            "App::PropertyString",
            "PerformanceClaim",
            "Packaging allocation only; no acoustic-performance claim",
        )

        radiator_name = "Passive_Radiator_" + side
        radiator = p.AUDIO[radiator_name]
        radiator_obj = semantic_part(
            doc,
            group,
            radiator_name,
            radiator_name.replace("_", " "),
            Part.makeBox(
                radiator["width"],
                radiator["height"],
                speaker_depth,
                vector(
                    speaker_x + (speaker_diameter - radiator["width"]) / 2.0,
                    speaker_y - radiator["height"],
                    barrel["depth"],
                ),
            ),
            metadata(
                "HNK-AU-01{}".format(index),
                radiator_name,
                "05_Audio_IO_Cables",
                "Passive radiator proxy",
            ),
        )
        add_dimension(radiator_obj, "Width", radiator["width"])
        add_dimension(radiator_obj, "Height", radiator["height"])
        parts.append(radiator_obj)

        microphone_name = "Microphone_" + side
        microphone_count = p.AUDIO[microphone_name]["count"]
        microphone_radius = p.BOARD_ENVELOPES["IO_PCB"]["thickness"]
        microphone = semantic_part(
            doc,
            group,
            microphone_name,
            microphone_name.replace("_", " "),
            Part.makeCylinder(
                microphone_radius,
                microphone_radius,
                vector(
                    speaker_x + speaker_diameter / 2.0,
                    head["height"] - microphone_radius,
                    0.0,
                ),
                vector(0.0, 0.0, 1.0),
            ),
            metadata(
                "HNK-AU-02{}".format(index),
                microphone_name,
                "05_Audio_IO_Cables",
                "Wide-angle microphone module proxy",
            ),
        )
        add_property(
            microphone,
            "App::PropertyInteger",
            "ElementCount",
            microphone_count,
        )
        parts.append(microphone)
    return parts


def build_io_ports(doc, groups):
    group = groups["05_Audio_IO_Cables"]
    keepouts = groups["08_Reference_Datums_Keepouts"]
    parts = []
    io_board = p.BOARD_ENVELOPES["IO_PCB"]
    head = p.HEAD
    light = p.CAMERA_LIGHT_SENSOR["Front_Light_Left"]
    pitch = io_board["width"] / len(p.IO_PORTS)
    port_width = pitch / 2.0
    port_height = light["depth"]
    port_depth = io_board["thickness"]
    zone_x = (head["width"] - io_board["width"]) / 2.0
    zone_y = p.VENTS["Inlet_Lower_Rear"]["height"] + io_board["height"]
    clearance_margin = io_board["thickness"] / 2.0
    for index, port_name in enumerate(p.IO_PORTS, start=1):
        port_x = zone_x + (index - 1) * pitch + (pitch - port_width) / 2.0
        port = semantic_part(
            doc,
            group,
            port_name,
            port_name.replace("_", " "),
            Part.makeBox(
                port_width,
                port_height,
                port_depth,
                vector(port_x, zone_y, head["depth"] - port_depth),
            ),
            metadata(
                "HNK-IO-{:03d}".format(index),
                port_name,
                "05_Audio_IO_Cables",
                "Typed connector body proxy",
            ),
        )
        add_property(port, "App::PropertyString", "PortType", port_name)
        add_role(port, "ConnectorBody")
        parts.append(port)

        hole_name = port_name + "_Clearance_Hole"
        hole = add_keepout(
            doc,
            keepouts,
            "HNK-KO-2{:02d}".format(index),
            hole_name,
            Part.makeBox(
                port_width + 2.0 * clearance_margin,
                port_height + 2.0 * clearance_margin,
                port_depth + 2.0 * clearance_margin,
                vector(
                    port_x - clearance_margin,
                    zone_y - clearance_margin,
                    head["depth"] - port_depth - 2.0 * clearance_margin,
                ),
            ),
            "ClearanceHole",
        )
        add_property(hole, "App::PropertyString", "PortType", port_name)
    return parts


def build_cables(doc, groups):
    cable_group = groups["05_Audio_IO_Cables"]
    keepout_group = groups["08_Reference_Datums_Keepouts"]
    parts = []
    cable_radius = p.BOARD_ENVELOPES["IO_PCB"]["thickness"] / 2.0
    obstruction_radius = p.BOARD_ENVELOPES["IO_PCB"]["thickness"]
    io_centre = doc.getObject("IO_Harness_Connector").Shape.BoundBox.Center
    camera_centre = doc.getObject("Camera_Module").Shape.BoundBox.Center
    usb_c_centre = doc.getObject(
        "USB_C_Display_Data_PD90W"
    ).Shape.BoundBox.Center
    speaker_left = doc.getObject("Speaker_Left").Shape.BoundBox.Center
    speaker_right = doc.getObject("Speaker_Right").Shape.BoundBox.Center
    rear_z = p.HEAD["depth"] - obstruction_radius
    routes = {
        "BYOD_Cable_Route": (
            (usb_c_centre.x, usb_c_centre.y, rear_z),
            (usb_c_centre.x, io_centre.y, rear_z),
            (io_centre.x, io_centre.y, io_centre.z),
        ),
        "Camera_Cable_Route": (
            (io_centre.x, io_centre.y, io_centre.z),
            (camera_centre.x, io_centre.y, io_centre.z),
            (camera_centre.x, camera_centre.y, camera_centre.z),
        ),
        "Audio_Cable_Route_Left": (
            (io_centre.x, io_centre.y, io_centre.z),
            (speaker_left.x, io_centre.y, io_centre.z),
            (speaker_left.x, speaker_left.y, speaker_left.z),
        ),
        "Audio_Cable_Route_Right": (
            (io_centre.x, io_centre.y, io_centre.z),
            (speaker_right.x, io_centre.y, io_centre.z),
            (speaker_right.x, speaker_right.y, speaker_right.z),
        ),
    }
    for index, (name, points) in enumerate(routes.items(), start=1):
        cable = semantic_part(
            doc,
            cable_group,
            name,
            name.replace("_", " "),
            make_segmented_path(points, cable_radius),
            metadata(
                "HNK-CB-{:03d}".format(index),
                name,
                "05_Audio_IO_Cables",
                "Routed cable effective solid",
            ),
        )
        add_role(cable, "RoutedCable")
        add_property(
            cable,
            "App::PropertyString",
            "MinimumBendIntent",
            BEND_INTENT,
        )
        add_property(
            cable,
            "App::PropertyString",
            "BendRadiusStatus",
            "OpenAssumption",
        )
        parts.append(cable)

        obstruction_name = name + "_Obstruction_Envelope"
        obstruction = add_keepout(
            doc,
            keepout_group,
            "HNK-KO-3{:02d}".format(index),
            obstruction_name,
            make_segmented_path(points, obstruction_radius),
            "CableObstructionEnvelope",
        )
        add_property(
            obstruction,
            "App::PropertyString",
            "MinimumBendIntent",
            BEND_INTENT,
        )
    return parts


def build_av_io(doc, groups):
    parts = []
    parts.extend(build_camera_lighting_sensors(doc, groups))
    parts.extend(build_audio(doc, groups))
    parts.extend(build_io_ports(doc, groups))
    parts.extend(build_cables(doc, groups))
    return parts
