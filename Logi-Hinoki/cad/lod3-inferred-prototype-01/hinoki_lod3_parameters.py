"""Frozen design inputs for the Hinoki LOD 3 inferred engineering prototype."""

from types import MappingProxyType


def frozen(**values):
    return MappingProxyType(values)


PROTOTYPE_LIMITATION = (
    "LOD 3 inferred engineering prototype; not manufacturing release. "
    "No authority for tooling, GD&T, supplier release, certification, or "
    "production temperature claims."
)

HEAD = frozen(width=742.0, height=492.0, depth=62.0)
ACTIVE_AREA = frozen(width=708.4, height=398.5)
DISPLAY_STACK = MappingProxyType(
    {
        "Cover_Glass": frozen(width=726.0, height=446.0, thickness=3.2),
        "PCAP_Sensor": frozen(width=724.0, height=444.0, thickness=0.8),
        "Optical_Bond": frozen(width=724.0, height=444.0, thickness=0.5),
        "LCD_Cell": frozen(width=712.0, height=402.0, thickness=2.5),
        "Backlight_Unit": frozen(width=716.0, height=406.0, thickness=12.0),
    }
)

HOUSING = frozen(
    rear_wall=2.8,
    structural_rib=1.7,
    primary_boss_od=7.0,
    primary_fastener="M3",
)

VENTS = MappingProxyType(
    {
        "Inlet_Lower_Rear": frozen(
            width=400.0,
            height=25.0,
            target_open_ratio=0.60,
            minimum_open_area=6000.0,
        ),
        "Outlet_Upper_Rear": frozen(
            width=400.0,
            height=25.0,
            target_open_ratio=0.60,
            minimum_open_area=6000.0,
        ),
    }
)

BOARD_ENVELOPES = MappingProxyType(
    {
        "Carrier_PCB": frozen(width=250.0, height=140.0, thickness=1.6),
        "Compute_SOM_PCB": frozen(width=90.0, height=70.0, thickness=1.6),
        "Power_PCB": frozen(width=160.0, height=100.0, thickness=1.6),
        "IO_PCB": frozen(width=180.0, height=30.0, thickness=1.6),
        "WiFi_BLE_Module": frozen(width=30.0, height=20.0, thickness=3.0),
    }
)

CAMERA_LIGHT_SENSOR = MappingProxyType(
    {
        "Camera_Module": frozen(width=38.0, height=38.0, depth=25.78),
        "Camera_Barrel": frozen(width=104.0, height=46.0, depth=32.0),
        "Front_Light_Left": frozen(width=120.0, height=8.0, depth=8.0),
        "Front_Light_Right": frozen(width=120.0, height=8.0, depth=8.0),
        "Radar_Holder": frozen(width=59.8, height=18.0, depth=16.3),
    }
)

CAMERA_OPTICS = frozen(
    hfov_deg=140.0,
    forward_axis_z=-1.0,
    optical_origin_z=0.0,
    validation_distance=100.0,
    lens_to_window_distance=3.2,
    lens_aperture_diameter=6.0,
    assumption_id="A-LOD3-AV-001",
    source_reference="Design section 6.3; LI-IMX477-MIPI-140H 140 degree HFOV",
)
AV_CAVITY = frozen(
    clearance=1.0,
    front_plane_z=3.2,
    assumption_id="A-LOD3-AV-002",
    source_reference="Design section 6.3; inferred AV cavity clearance",
)
SHUTTER_GEOMETRY = frozen(
    width=19.0,
    height=19.0,
    thickness=1.6,
    travel=38.0,
    assumption_id="A-LOD3-AV-003",
    source_reference="DR-06 captive shutter engineering assumption",
)
ALS_GEOMETRY = frozen(
    aperture_diameter=3.2,
    path_depth=16.3,
    assumption_id="A-LOD3-AV-004",
    source_reference="Design section 6.3 independent ALS optical path assumption",
)
MICROPHONE_GEOMETRY = frozen(
    diameter=3.2,
    depth=1.6,
    assumption_id="A-LOD3-AU-001",
    source_reference="Design section 6.4 wide-angle microphone proxy assumption",
)
SPEAKER_GEOMETRY = frozen(
    depth=8.0,
    assumption_id="A-LOD3-AU-002",
    source_reference="Design section 6.4 speaker depth engineering assumption",
)

AUDIO = MappingProxyType(
    {
        "Speaker_Left": frozen(diameter=40.0),
        "Speaker_Right": frozen(diameter=40.0),
        "Passive_Radiator_Left": frozen(width=50.0, height=25.0),
        "Passive_Radiator_Right": frozen(width=50.0, height=25.0),
        "Microphone_Left": frozen(count=1),
        "Microphone_Right": frozen(count=1),
    }
)

IO_PORTS = (
    "HDMI_Input",
    "USB_A_1",
    "USB_A_2",
    "USB_C_Display_Data_PD90W",
    "Ethernet",
    "Line_Out_3p5mm",
)
IO_PORT_GEOMETRY = frozen(
    service_zone_width=180.0,
    body_width=15.0,
    body_height=8.0,
    body_depth=8.0,
    clearance=0.8,
    cut_extension=1.0,
    assumption_id="A-LOD3-IO-001",
    source_reference="Design section 6.2 rear service connector opening assumption",
)
CABLE_GEOMETRY = MappingProxyType(
    {
        "BYOD_Cable_Route": frozen(
            outer_diameter=4.0,
            minimum_bend_radius=12.0,
            lane_z=54.0,
            assumption_id="A-LOD3-CB-001",
            source_reference="DR-13 controlled BYOD cable routing assumption",
        ),
        "Camera_Cable_Route": frozen(
            outer_diameter=2.0,
            minimum_bend_radius=6.0,
            lane_z=52.0,
            assumption_id="A-LOD3-CB-002",
            source_reference="DR-13 controlled camera cable routing assumption",
        ),
        "Audio_Cable_Route_Left": frozen(
            outer_diameter=2.0,
            minimum_bend_radius=6.0,
            lane_z=48.0,
            assumption_id="A-LOD3-CB-003",
            source_reference="DR-13 controlled audio cable routing assumption",
        ),
        "Audio_Cable_Route_Right": frozen(
            outer_diameter=2.0,
            minimum_bend_radius=6.0,
            lane_z=48.0,
            assumption_id="A-LOD3-CB-004",
            source_reference="DR-13 controlled audio cable routing assumption",
        ),
    }
)
CABLE_ROUTE_CLEARANCE = frozen(
    radial=1.0,
    assumption_id="A-LOD3-CB-005",
    source_reference="DR-13 cable obstruction clearance assumption",
)

THERMAL_PATH = MappingProxyType(
    {
        "QC7790": frozen(width=35.0, height=35.0, thickness=2.0),
        "TIM_QC7790": frozen(
            width=35.0, height=35.0, thickness=1.0, conductivity=3.0
        ),
        "Copper_Spreader": frozen(width=100.0, height=80.0, thickness=2.0),
        "Heat_Pipe_Left": frozen(diameter=6.0),
        "Heat_Pipe_Right": frozen(diameter=6.0),
        "Aluminum_Interface": frozen(
            width=220.0, height=120.0, thickness=2.5
        ),
        "Rear_Hatch_TIM": frozen(
            width=80.0, height=40.0, thickness=1.5, conductivity=8.0
        ),
    }
)

STAND = frozen(
    vesa_pitch=100.0,
    vesa_fastener="M4",
    overall_height_min=521.0,
    overall_height_max=621.0,
    depth_envelope=225.0,
    height_travel=100.0,
    tilt_min=-10.0,
    tilt_max=10.0,
    swivel_min=-20.0,
    swivel_max=20.0,
    static_margin_min=25.0,
)
BASE = frozen(
    width=520.0,
    depth=225.0,
    structural_plate_width=500.0,
    structural_plate_depth=205.0,
    structural_plate_thickness=6.0,
    vesa_plate_width=140.0,
    vesa_plate_height=140.0,
    vesa_plate_thickness=4.0,
)

THERMAL_CASE = frozen(
    ambient_c=35.0,
    cooling_mode="NaturalConvection",
    fan_present=False,
    gravity_mm_s2=(0.0, -9810.0, 0.0),
)
HEAT_LOADS_W = MappingProxyType(
    {
        "Heat_Panel_Backlight": 20.0,
        "Heat_QC7790": 12.0,
        "Heat_Memory": 2.0,
        "Heat_Carrier_PMIC": 5.0,
        "Heat_IO": 5.0,
        "Heat_WiFi_BLE": 1.5,
        "Heat_Camera": 3.0,
        "Heat_Audio": 4.0,
        "Heat_Radar_ALS": 0.5,
        "Heat_Front_Lighting": 4.0,
    }
)

REQUIRED_TOP_GROUPS = (
    "01_Display_Stack",
    "02_Housing_Structure",
    "03_Electronics_Thermal",
    "04_Camera_Lighting_Sensors",
    "05_Audio_IO_Cables",
    "06_Stand_Base_Kinematics",
    "07_Fasteners_Seals_Consumables",
    "08_Reference_Datums_Keepouts",
)

SOURCE_CLASSES = (
    "Known",
    "Derived",
    "DixieReference",
    "CompetitorOfficial",
    "EngineeringAssumption",
)
THERMAL_DISPOSITIONS = ("Keep", "Aggregate", "Suppress")
METADATA_KEYS = (
    "PartID",
    "PartName",
    "ParentAssembly",
    "MaterialIntent",
    "SourceClass",
    "SourceReference",
    "Confidence",
    "ManufacturingAuthority",
    "ThermalDisposition",
    "HeatLoadW",
    "Revision",
)

MATERIAL_INTENTS = MappingProxyType(
    {
        "Housing_Polymer": "PCR PC/ABS; UL94 V-0 intent",
        "Display_Glass": "Generic soda-lime/aluminosilicate equivalent",
        "Aluminum_Structure": "Aluminum 6061",
        "Die_Cast_Joint": "ADC12 equivalent",
        "Sheet_Bracket_Shield": "SECC/SGCC; 0.8-1.2 mm",
        "Stand_Structure": "Carbon steel",
        "Thermal_Copper": "Copper",
        "PCB": "FLOEFD equivalent FR-4 stack",
        "Steel_Hardware": "Simplified steel equivalent",
        "Internal_Air": "Air",
    }
)

OUTPUT_FILES = frozen(
    master_fcstd="Hinoki_LOD3_Inferred_Master.FCStd",
    full_step="Hinoki_LOD3_Full_Assembly.step",
    head_step="Hinoki_LOD3_Head.step",
    display_step="Hinoki_LOD3_Display.step",
    electronics_thermal_step="Hinoki_LOD3_Electronics_Thermal.step",
    stand_base_step="Hinoki_LOD3_Stand_Base.step",
    manifest_json="Hinoki_LOD3_Part_Manifest.json",
    validation_json="Hinoki_LOD3_Validation.json",
)


def part_metadata(
    *,
    part_id,
    part_name,
    parent_assembly,
    material_intent,
    source_class,
    source_reference,
    confidence,
    thermal_disposition,
    heat_load_w=0.0,
    revision="A",
):
    """Return one complete non-release semantic-part metadata record."""
    if parent_assembly not in REQUIRED_TOP_GROUPS:
        raise ValueError("Unknown parent assembly: " + str(parent_assembly))
    if source_class not in SOURCE_CLASSES:
        raise ValueError("Unknown source class: " + str(source_class))
    if thermal_disposition not in THERMAL_DISPOSITIONS:
        raise ValueError("Unknown thermal disposition: " + str(thermal_disposition))
    if not source_reference:
        raise ValueError("SourceReference must be non-empty")
    return {
        "PartID": str(part_id),
        "PartName": str(part_name),
        "ParentAssembly": parent_assembly,
        "MaterialIntent": str(material_intent),
        "SourceClass": source_class,
        "SourceReference": str(source_reference),
        "Confidence": str(confidence),
        "ManufacturingAuthority": False,
        "ThermalDisposition": thermal_disposition,
        "HeatLoadW": float(heat_load_w),
        "Revision": str(revision),
    }
