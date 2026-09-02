"""Immutable parameters for the approved Hinoki FLOEFD CHT handoff case."""

from types import MappingProxyType


HEAD = MappingProxyType({"width": 742.0, "height": 492.0, "depth": 62.0})
GLASS_THICKNESS = 3.0
REAR_WALL = 2.5
MIDFRAME_THICKNESS = 2.0
ACTIVE_AREA = MappingProxyType({"width": 708.4, "height": 398.5})

AMBIENT_C = 35.0
COOLING_MODE = "NaturalConvection"
GRAVITY_MM_S2 = (0.0, -9810.0, 0.0)
VENT = MappingProxyType({"width": 400.0, "height": 15.0, "area": 6000.0})

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

SOLID_BODIES = (
    "Cover_Glass",
    "Mid_Frame",
    "Rear_Enclosure",
    "Heat_Panel_Backlight",
    "Carrier_PCB",
    "Heat_Spreader",
    "TIM_QC7790",
    "Heat_QC7790",
    "Heat_Memory",
    "Heat_Carrier_PMIC",
    "Heat_IO",
    "Heat_WiFi_BLE",
    "Heat_Camera",
    "Heat_Audio",
    "Heat_Radar_ALS",
    "Heat_Front_Lighting",
)
FLUID_BODIES = ("Internal_Air_Volume",)
BOUNDARY_FACES = (
    "Inlet_Opening_Lower_Rear",
    "Outlet_Opening_Upper_Rear",
)

# Every body is explicit so the FLOEFD handoff never relies on an implicit
# material default; all solid intents are effective isotropic solid models.
MATERIAL_INTENT = MappingProxyType(
    {
        "Cover_Glass": "Generic glass",
        "Mid_Frame": "Aluminum 6061",
        "Rear_Enclosure": "PC/ABS",
        "Heat_Panel_Backlight": "FLOEFD equivalent display stack",
        "Carrier_PCB": "FLOEFD equivalent PCB",
        "Heat_Spreader": "Aluminum 6061",
        "TIM_QC7790": "Isotropic TIM; k=3 W/m-K",
        "Heat_QC7790": "QC7790 package, effective isotropic solid",
        "Heat_Memory": "Memory package, effective isotropic solid",
        "Heat_Carrier_PMIC": "PMIC package, effective isotropic solid",
        "Heat_IO": "I/O package, effective isotropic solid",
        "Heat_WiFi_BLE": "Wi-Fi/BLE package, effective isotropic solid",
        "Heat_Camera": "Camera package, effective isotropic solid",
        "Heat_Audio": "Audio package, effective isotropic solid",
        "Heat_Radar_ALS": "Radar/ALS package, effective isotropic solid",
        "Heat_Front_Lighting": "Front lighting package, effective isotropic solid",
        "Internal_Air_Volume": "Air",
    }
)

MODEL_FILE = "Hinoki_Thermal_CHT_Iteration01.FCStd"
SOLIDS_STEP = "Hinoki_Thermal_Solids_Iteration01.step"
AIR_STEP = "Hinoki_Thermal_Air_Iteration01.step"
SETUP_JSON = "Hinoki_FLOEFD_CHT_Setup_Iteration01.json"
REVIEW_JSON = "Hinoki_FLOEFD_CHT_Review_Iteration01.json"
