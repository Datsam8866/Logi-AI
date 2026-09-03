"""Camera, lighting, sensor, audio, and I/O geometry."""

import math
import Part

import hinoki_lod3_parameters as p
from hinoki_lod3_common import add_dimension, add_property, semantic_part, vector


SOURCE = "Approved LOD 3 design sections 6.2 through 6.4"


def assumption_source(block):
    return "{} [{}]".format(block["source_reference"], block["assumption_id"])


def source_reference_for(name):
    if name == "Camera_Module":
        return "LI-IMX477-MIPI-140H published envelope; Design section 6.3"
    if name in (
        "Camera_Barrel",
        "Camera_Optical_Keepout",
        "Camera_FOV_Reference",
    ):
        return assumption_source(p.CAMERA_OPTICS)
    if name.startswith("Privacy_Shutter") or name.startswith("Shutter_"):
        return assumption_source(p.SHUTTER_GEOMETRY)
    if name == "AV_Cavity":
        return assumption_source(p.AV_CAVITY)
    if name.startswith("Front_Light") or name == "Radar_Holder":
        return "Design section 6.3 controlled CAMERA_LIGHT_SENSOR." + name
    if name == "ALS_Optical_Path":
        return assumption_source(p.ALS_GEOMETRY)
    if name.startswith("Microphone_"):
        return assumption_source(p.MICROPHONE_GEOMETRY)
    if name.startswith("Speaker_"):
        return assumption_source(p.SPEAKER_GEOMETRY)
    if name.startswith("Passive_Radiator_"):
        return "Design section 6.4 controlled AUDIO." + name
    port_name = name.removesuffix("_Clearance_Hole")
    if port_name in p.IO_PORTS:
        return "{} [{}; {}]".format(
            p.IO_PORT_GEOMETRY["source_reference"],
            p.IO_PORT_GEOMETRY["assumption_id"],
            port_name,
        )
    return SOURCE


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
        source_reference=source_reference_for(name),
        confidence="Medium",
        thermal_disposition=disposition,
    )


def add_role(obj, role):
    add_property(obj, "App::PropertyString", "GeometryRole", role)
    return obj


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
    add_property(obj, "App::PropertyBool", "PhysicalCollision", False)
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
    cavity_clearance = p.AV_CAVITY["clearance"]
    front_plane_z = p.AV_CAVITY["front_plane_z"]

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
                front_plane_z,
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
    add_property(
        camera_obj,
        "App::PropertyString",
        "AuthorizedContactRecord",
        "Heat_Camera and Heat_Front_Lighting: intentional thermal endpoint contact.",
    )
    parts.append(camera_obj)

    barrel_obj = add_keepout(
        doc,
        keepouts,
        "HNK-KO-100",
        "Camera_Barrel",
        Part.makeBox(
            barrel["width"],
            barrel["height"],
            barrel["depth"],
            vector(barrel_x, barrel_y, 0.0),
        ),
        "PackageEnvelope",
    )
    for name in ("width", "height", "depth"):
        add_dimension(barrel_obj, name.title(), barrel[name])

    shutter_geometry = p.SHUTTER_GEOMETRY
    shutter_thickness = shutter_geometry["thickness"]
    shutter_width = shutter_geometry["width"]
    shutter_height = shutter_geometry["height"]
    shutter_travel = shutter_geometry["travel"]
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

    shutter_open = add_keepout(
        doc,
        keepouts,
        "HNK-KO-106",
        "Privacy_Shutter_Open",
        Part.makeBox(
            shutter_width,
            shutter_height,
            shutter_thickness,
            vector(shutter_x + shutter_travel, shutter_y, 0.0),
        ),
        "MotionStateReference",
    )
    add_dimension(shutter_open, "TravelFromClosed", shutter_travel)

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

    optics = p.CAMERA_OPTICS
    optical_origin = vector(
        centre_x,
        head["height"] - camera["height"] / 2.0,
        optics["optical_origin_z"],
    )
    internal_optical_shape = Part.makeCylinder(
        optics["lens_aperture_diameter"] / 2.0,
        optics["lens_to_window_distance"],
        optical_origin,
        vector(0.0, 0.0, 1.0),
    )
    internal_optical = add_keepout(
        doc,
        keepouts,
        "HNK-KO-102",
        "Camera_Optical_Keepout",
        internal_optical_shape,
        "InternalOpticalKeepout",
    )
    add_dimension(
        internal_optical,
        "LensToWindowDistance",
        optics["lens_to_window_distance"],
    )

    far_half_width = (
        optics["validation_distance"]
        * math.tan(math.radians(optics["hfov_deg"] / 2.0))
    )
    fov = add_keepout(
        doc,
        keepouts,
        "HNK-KO-104",
        "Camera_FOV_Reference",
        Part.makeCone(
            optics["lens_aperture_diameter"] / 2.0,
            far_half_width,
            optics["validation_distance"],
            optical_origin,
            vector(0.0, 0.0, optics["forward_axis_z"]),
        ),
        "ExternalOpticalReference",
    )
    add_property(fov, "App::PropertyFloat", "HorizontalFOV", optics["hfov_deg"])
    add_property(
        fov,
        "App::PropertyFloat",
        "ForwardAxisZ",
        optics["forward_axis_z"],
    )
    add_dimension(fov, "OpticalOriginZ", optics["optical_origin_z"])
    add_dimension(fov, "ValidationDistance", optics["validation_distance"])
    add_dimension(fov, "FarHalfWidth", far_half_width)

    light_gap = (barrel["width"] - camera["width"]) / 2.0
    light_positions = {
        "Front_Light_Left": barrel_x
        - p.CAMERA_LIGHT_SENSOR["Front_Light_Left"]["width"]
        - light_gap,
        "Front_Light_Right": barrel_x + barrel["width"] + light_gap,
    }
    radar = p.CAMERA_LIGHT_SENSOR["Radar_Holder"]
    radar_x = centre_x - radar["width"] / 2.0
    cavity_shapes = [
        Part.makeBox(
            barrel["width"] + 2.0 * cavity_clearance,
            barrel["height"] + cavity_clearance,
            barrel["depth"] + cavity_clearance,
            vector(
                barrel_x - cavity_clearance,
                barrel_y - cavity_clearance,
                0.0,
            ),
        ),
        Part.makeBox(
            radar["width"] + 2.0 * cavity_clearance,
            radar["height"] + cavity_clearance,
            radar["depth"] + cavity_clearance,
            vector(radar_x - cavity_clearance, 0.0, 0.0),
        ),
    ]
    for name, light_x in light_positions.items():
        dimensions = p.CAMERA_LIGHT_SENSOR[name]
        cavity_shapes.append(
            Part.makeBox(
                dimensions["width"] + 2.0 * cavity_clearance,
                dimensions["height"] + cavity_clearance,
                dimensions["depth"] + cavity_clearance,
                vector(
                    light_x - cavity_clearance,
                    head["height"] - dimensions["height"] - cavity_clearance,
                    0.0,
                ),
            )
        )
    cavity_shape = Part.makeCompound(cavity_shapes)
    cavity = add_keepout(
        doc,
        keepouts,
        "HNK-KO-105",
        "AV_Cavity",
        cavity_shape,
        "CavityReference",
    )
    add_property(
        cavity,
        "App::PropertyString",
        "AuthorizedContactIntent",
        "Zero-volume seating contacts only at controlled cavity datums.",
    )
    for obstacle_name in (
        "Cover_Glass",
        "PCAP_Sensor",
        "Optical_Bond",
        "LCD_Cell",
        "Backlight_Unit",
        "Metal_Mid_Frame",
        "Front_Frame",
        "Rear_Enclosure",
    ):
        obstacle = doc.getObject(obstacle_name)
        obstacle.Shape = obstacle.Shape.cut(cavity_shape)

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

    als = p.ALS_GEOMETRY
    als_radius = als["aperture_diameter"] / 2.0
    als_path = add_keepout(
        doc,
        keepouts,
        "HNK-KO-103",
        "ALS_Optical_Path",
        Part.makeCylinder(
            als_radius,
            als["path_depth"],
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
    microphone_apertures = []
    head = p.HEAD
    barrel = p.CAMERA_LIGHT_SENSOR["Camera_Barrel"]
    speaker_depth = p.SPEAKER_GEOMETRY["depth"]
    speaker_diameter = p.AUDIO["Speaker_Left"]["diameter"]
    speaker_y = head["height"] - barrel["height"]
    camera = p.CAMERA_LIGHT_SENSOR["Camera_Module"]
    light = p.CAMERA_LIGHT_SENSOR["Front_Light_Left"]
    light_gap = (barrel["width"] - camera["width"]) / 2.0
    left_light_x = (
        head["width"] / 2.0
        - barrel["width"] / 2.0
        - light["width"]
        - light_gap
    )
    left_speaker_x = left_light_x - light_gap - speaker_diameter
    positions = {
        "Left": left_speaker_x,
        "Right": head["width"] - left_speaker_x - speaker_diameter,
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
        add_dimension(speaker, "Depth", speaker_depth)
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
        microphone_geometry = p.MICROPHONE_GEOMETRY
        microphone_radius = microphone_geometry["diameter"] / 2.0
        microphone_y = speaker_y - microphone_geometry["diameter"]
        microphone = semantic_part(
            doc,
            group,
            microphone_name,
            microphone_name.replace("_", " "),
            Part.makeCylinder(
                microphone_radius,
                microphone_geometry["depth"],
                vector(
                    speaker_x + speaker_diameter / 2.0,
                    microphone_y,
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
        add_dimension(microphone, "Diameter", microphone_geometry["diameter"])
        add_dimension(microphone, "Depth", microphone_geometry["depth"])
        parts.append(microphone)
        microphone_apertures.append(
            Part.makeCylinder(
                microphone_radius + p.AV_CAVITY["clearance"],
                microphone_geometry["depth"] + 2.0 * p.AV_CAVITY["clearance"],
                vector(
                    speaker_x + speaker_diameter / 2.0,
                    microphone_y,
                    -p.AV_CAVITY["clearance"],
                ),
                vector(0.0, 0.0, 1.0),
            )
        )
    microphone_aperture_shape = Part.makeCompound(microphone_apertures)
    for obstacle_name in (
        "Cover_Glass",
        "PCAP_Sensor",
        "Optical_Bond",
        "LCD_Cell",
        "Backlight_Unit",
        "Metal_Mid_Frame",
        "Front_Frame",
    ):
        obstacle = doc.getObject(obstacle_name)
        obstacle.Shape = obstacle.Shape.cut(microphone_aperture_shape)
    add_keepout(
        doc,
        keepouts,
        "HNK-KO-115",
        "Microphone_Apertures",
        microphone_aperture_shape,
        "CavityReference",
    )
    return parts


def build_io_ports(doc, groups):
    group = groups["05_Audio_IO_Cables"]
    keepouts = groups["08_Reference_Datums_Keepouts"]
    parts = []
    head = p.HEAD
    port_geometry = p.IO_PORT_GEOMETRY
    cover = doc.getObject("Rear_IO_Cover")
    rear = doc.getObject("Rear_Enclosure")
    cover_centre = cover.Shape.BoundBox.Center
    pitch = port_geometry["service_zone_width"] / len(p.IO_PORTS)
    port_width = port_geometry["body_width"]
    port_height = port_geometry["body_height"]
    port_depth = port_geometry["body_depth"]
    zone_x = cover_centre.x - port_geometry["service_zone_width"] / 2.0
    zone_y = cover_centre.y - port_height / 2.0
    rear_z = head["depth"] - p.HOUSING["rear_wall"]
    clearance = port_geometry["clearance"]
    cut_extension = port_geometry["cut_extension"]
    cutters = []
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
                vector(port_x, zone_y, rear_z - port_depth),
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
        passage_z_min = rear_z - port_depth - clearance
        passage_z_max = head["depth"] + cut_extension
        cutter_shape = Part.makeBox(
            port_width + 2.0 * clearance,
            port_height + 2.0 * clearance,
            passage_z_max - passage_z_min,
            vector(
                port_x - clearance,
                zone_y - clearance,
                passage_z_min,
            ),
        )
        cutters.append(cutter_shape)
        hole = add_keepout(
            doc,
            keepouts,
            "HNK-KO-2{:02d}".format(index),
            hole_name,
            cutter_shape,
            "ClearanceHole",
        )
        add_property(hole, "App::PropertyString", "PortType", port_name)
        add_property(hole, "App::PropertyBool", "PhysicalCollision", False)
    cutter_compound = Part.makeCompound(cutters)
    rear.Shape = rear.Shape.cut(cutter_compound)
    cover.Shape = cover.Shape.cut(cutter_compound)
    for obstacle_name in ("VESA_Reinforcement", "Rear_Hatch_TIM"):
        obstacle = doc.getObject(obstacle_name)
        obstacle.Shape = obstacle.Shape.cut(cutter_compound)
    return parts


def build_av_io(doc, groups):
    parts = []
    parts.extend(build_camera_lighting_sensors(doc, groups))
    parts.extend(build_audio(doc, groups))
    parts.extend(build_io_ports(doc, groups))
    return parts
