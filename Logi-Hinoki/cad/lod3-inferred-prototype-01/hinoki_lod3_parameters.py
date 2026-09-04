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

# Display stack z-plan (z is measured from front face).
# 0.0..3.2   Cover_Glass + Front_Bezel
# 3.2..4.0   PCAP_Sensor
# 4.0..4.5   Optical_Bond
# 4.5..7.0   LCD_Cell
# 7.0..8.5   BLU_Optical_Films (reflector + diffuser + prism equivalent stack)
# 8.5..12.5  Light_Guide_Plate
# 12.5..15.5 Panel_Backplate (metal, holds LGP and LED PCB)
# 15.5..19.0 Display service gap and Display_Carrier
DISPLAY_STACK = MappingProxyType(
    {
        "Cover_Glass": frozen(width=726.0, height=446.0, thickness=3.2),
        "PCAP_Sensor": frozen(width=724.0, height=444.0, thickness=0.8),
        "Optical_Bond": frozen(width=724.0, height=444.0, thickness=0.5),
        "LCD_Cell": frozen(width=712.0, height=402.0, thickness=2.5),
        "BLU_Optical_Films": frozen(width=716.0, height=406.0, thickness=1.5),
        "Light_Guide_Plate": frozen(width=716.0, height=406.0, thickness=4.0),
        "Panel_Backplate": frozen(width=716.0, height=406.0, thickness=3.0),
    }
)

# Edge-lit backlight: single LED PCB along the bottom edge of the LGP.
# LED_Bar is a physical carrier for the Heat_BLU_LED heat source; sized to
# fit within a matching cutout in the Panel_Backplate to avoid interference.
LED_BAR = frozen(
    width=700.0,
    depth=12.0,
    thickness=3.0,
    y_offset_from_lgp_edge=1.0,
    architecture="edge-lit-bottom",
    assumption_id="A-LOD3-PN-001",
    source_reference="Edge-lit engineering assumption; 32-inch panel typical",
)
BACKPLATE_LED_CUTOUT_CLEARANCE = 0.3

# Panel drivers (individual physical solids and heat sources).
PANEL_DRIVER = MappingProxyType(
    {
        "BLU_Driver_PCB": frozen(
            width=48.0,
            height=30.0,
            thickness=1.6,
            assumption_id="A-LOD3-PN-002",
            source_reference="Split of 20 W Panel_Module budget (Q-02 P2 approach); driver only",
        ),
        "TCON_IC": frozen(
            width=15.0,
            height=15.0,
            thickness=1.0,
            assumption_id="A-LOD3-PN-003",
            source_reference="Split of 20 W Panel_Module budget (Q-02 P2 approach); TCON IC package",
        ),
        "Panel_Gate_Source_Driver": frozen(
            width=350.0,
            depth=6.0,
            thickness=1.0,
            assumption_id="A-LOD3-PN-004",
            source_reference="COF equivalent along LCD bottom edge",
        ),
    }
)

HOUSING = frozen(
    rear_wall=2.8,
    mid_frame_wall=2.0,
    mid_frame_front_z=3.2,
    mid_frame_rear_z=25.0,
    mid_frame_lap_start_z=22.0,
    mid_frame_plate_thickness=3.0,
    rear_cover_front_z=22.0,
    rib_thickness=1.7,
    rib_height=15.2,
    primary_boss_od=7.0,
    vesa_boss_od=9.0,
    primary_fastener="M3",
    vesa_fastener="M4",
)

# Enclosure mating geometry: designed clearances to represent real assembly
# interfaces rather than zero-clearance abutment (which would be unbuildable).
ENCLOSURE_MATING = frozen(
    front_seam_radial_clearance=0.2,
    lap_radial_clearance=0.3,
    lap_depth=3.0,
    bezel_thickness=3.2,
    mid_frame_lap_depth=3.0,
)

VESA_MOUNT_POINTS = (
    (321.0, 196.0),
    (421.0, 196.0),
    (321.0, 296.0),
    (421.0, 296.0),
)
# Corner boss positions in mid-frame coordinates.
CORNER_BOSS_POSITIONS = (
    (40.0, 40.0),
    (702.0, 40.0),
    (40.0, 452.0),
    (702.0, 452.0),
)

COLLISION_CLEARANCE = frozen(
    linear=0.5,
    radial=0.5,
    shield_wall=0.8,
    rear_boss_z=24.5,
    rear_boss_height=34.7,
    vesa_boss_height=34.7,
    boss_root_engagement=0.5,
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
    body_width=15.0,
    body_height=8.0,
    body_depth=8.0,
    cluster_columns=2,
    cluster_rows=3,
    service_margin=8.0,
    clearance=0.8,
    cut_extension=1.0,
    assumption_id="A-LOD3-IO-001",
    source_reference="Design section 6.2 rear service connector opening assumption",
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
# Heat sources: total 57 W budget preserved. The 20 W historic
# Heat_Panel_Backlight envelope is split into four physical panel heat sources
# under budget group Panel_Module (Panel_Module_Group). All four are labelled
# EngineeringAssumption because no supplier split is available.
HEAT_LOADS_W = MappingProxyType(
    {
        "Heat_BLU_LED": 16.0,
        "Heat_BLU_Driver": 2.0,
        "Heat_TCON": 1.5,
        "Heat_Panel_Gate_Source": 0.5,
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
HEAT_BUDGET_GROUPS = MappingProxyType(
    {
        "Panel_Module": (
            "Heat_BLU_LED",
            "Heat_BLU_Driver",
            "Heat_TCON",
            "Heat_Panel_Gate_Source",
        ),
        "Compute": (
            "Heat_QC7790",
            "Heat_Memory",
            "Heat_Carrier_PMIC",
            "Heat_WiFi_BLE",
        ),
        "IO": ("Heat_IO",),
        "AV_Sensor": (
            "Heat_Camera",
            "Heat_Radar_ALS",
            "Heat_Front_Lighting",
        ),
        "Audio": ("Heat_Audio",),
    }
)
PANEL_MODULE_BUDGET_W = 20.0
TOTAL_BUDGET_W = 57.0

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

# Frozen semantic contract for the LOD 3 head-only inferred prototype.
# Ribs and VESA_Reinforcement are now fused into their host semantic parts
# (Rear_Enclosure and Metal_Mid_Frame respectively) as internal features and
# are no longer independent semantic parts.
EXPECTED_SEMANTIC_PART_COUNT = 96
EXPECTED_PHYSICAL_PART_COUNT = 78

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
    "ExternalSourceStatus",
    "ExternalStandardID",
    "ThermalConductivityWmK",
)

MATERIAL_INTENTS = MappingProxyType(
    {
        "Housing_Polymer": "PCR PC/ABS; UL94 V-0 intent",
        "Display_Glass": "Generic soda-lime/aluminosilicate equivalent",
        "Aluminum_Structure": "Aluminum 6061",
        "Die_Cast_Joint": "ADC12 equivalent",
        "Sheet_Bracket_Shield": "SECC/SGCC; 0.8-1.2 mm",
        "Stand_Structure": "Carbon steel",
        "Thermal_Copper": "Copper; k=400 W/m-K",
        "PCB": "FLOEFD equivalent FR-4 stack",
        "Steel_Hardware": "Simplified steel equivalent",
        "Internal_Air": "Air",
        "Optical_Film": "Reflector/diffuser/prism equivalent optical stack",
        "Light_Guide": "PMMA equivalent light guide",
        "LED_Assembly": "Aluminum-clad LED PCB with SMD LED array equivalent",
        "IC_Package": "Effective isotropic silicon IC package",
        "COF_Driver": "Chip-on-film driver assembly equivalent",
        "Panel_Backplate": "SECC 3 mm effective (integrates LED trough)",
        "Heat_Pipe": "Copper wick heat pipe; equivalent k=8000 W/m-K",
        "Aluminum_Heatsink": "Aluminum 6061; k=167 W/m-K",
    }
)

OUTPUT_FILES = frozen(
    master_fcstd="Hinoki_LOD3_Inferred_Master.FCStd",
    head_step="Hinoki_LOD3_Head.step",
    manifest_json="Hinoki_LOD3_Part_Manifest.json",
    validation_json="Hinoki_LOD3_Validation.json",
)


_EXTERNAL_SOURCE_STATUS_DEFAULT_MAP = {
    "Known": "None:ApprovedContractValue",
    "Derived": "None:DerivedFromApprovedContract",
    "DixieReference": "DixieArchitecture:LOD3Inference:NoExternalDrawingAtThisPhase",
    "CompetitorOfficial": "External:CompetitorOfficialDatasheetOrSpec",
    "EngineeringAssumption": "None:LOD3EngineeringAssumption",
}


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
    external_source_status=None,
    external_standard_id="",
    thermal_conductivity_wmk=None,
):
    """Return one complete non-release semantic-part metadata record.

    External sourcing hierarchy fields (Iteration 3+):
        * ``external_source_status`` — auto-derived from ``source_class``
          when not overridden; makes the sourcing hierarchy explicit
          (Dixie architecture inference vs. external standard vs.
          engineering assumption).
        * ``external_standard_id`` — free-form external standard citation
          for parts that carry one (VESA MIS-D 100, LI-IMX477 published
          envelope, etc.). Empty string for parts with no external
          standard.
        * ``thermal_conductivity_wmk`` — W/m-K value for thermal parts,
          None otherwise.
    """
    if parent_assembly not in REQUIRED_TOP_GROUPS:
        raise ValueError("Unknown parent assembly: " + str(parent_assembly))
    if source_class not in SOURCE_CLASSES:
        raise ValueError("Unknown source class: " + str(source_class))
    if thermal_disposition not in THERMAL_DISPOSITIONS:
        raise ValueError("Unknown thermal disposition: " + str(thermal_disposition))
    if not source_reference:
        raise ValueError("SourceReference must be non-empty")
    resolved_status = external_source_status or _EXTERNAL_SOURCE_STATUS_DEFAULT_MAP.get(
        source_class, "Unknown:UncategorizedSource"
    )
    conductivity = (
        None if thermal_conductivity_wmk is None else float(thermal_conductivity_wmk)
    )
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
        "ExternalSourceStatus": str(resolved_status),
        "ExternalStandardID": str(external_standard_id),
        "ThermalConductivityWmK": conductivity,
    }
