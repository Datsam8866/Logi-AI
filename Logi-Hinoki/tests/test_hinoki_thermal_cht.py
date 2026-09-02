"""Contract checks for the approved Hinoki FLOEFD thermal CHT case."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PARAMETERS_FILE = PROJECT_ROOT / "cad" / "thermal-simulation-01" / "hinoki_thermal_parameters.py"


def load_parameters():
    spec = spec_from_file_location("hinoki_thermal_parameters", PARAMETERS_FILE)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HinokiThermalCHTTests(unittest.TestCase):
  def test_parameter_contract_matches_approved_floefd_case(self):
    self.assertTrue(PARAMETERS_FILE.exists(), "thermal parameters module must exist")
    p = load_parameters()

    self.assertEqual(p.HEAD, {"width": 742.0, "height": 492.0, "depth": 62.0})
    self.assertEqual(p.GLASS_THICKNESS, 3.0)
    self.assertEqual(p.REAR_WALL, 2.5)
    self.assertEqual(p.MIDFRAME_THICKNESS, 2.0)
    self.assertEqual(p.ACTIVE_AREA, {"width": 708.4, "height": 398.5})
    self.assertEqual(p.AMBIENT_C, 35.0)
    self.assertEqual(p.COOLING_MODE, "NaturalConvection")
    self.assertEqual(p.GRAVITY_MM_S2, (0.0, -9810.0, 0.0))
    self.assertEqual(p.VENT, {"width": 400.0, "height": 15.0, "area": 6000.0})

    self.assertEqual(p.HEAT_LOADS_W, {
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
    })
    self.assertEqual(len(p.HEAT_LOADS_W), 10)
    self.assertEqual(sum(p.HEAT_LOADS_W.values()), 57.0)

    self.assertEqual(p.SOLID_BODIES, (
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
    ))
    self.assertEqual(p.FLUID_BODIES, ("Internal_Air_Volume",))
    self.assertEqual(p.BOUNDARY_FACES, (
        "Inlet_Opening_Lower_Rear",
        "Outlet_Opening_Upper_Rear",
    ))

    expected_materials = {
        "Cover_Glass": "Generic glass",
        "Heat_Panel_Backlight": "FLOEFD equivalent display stack",
        "Mid_Frame": "Aluminum 6061",
        "Rear_Enclosure": "PC/ABS",
        "Carrier_PCB": "FLOEFD equivalent PCB",
        "Heat_Spreader": "Aluminum 6061",
        "TIM_QC7790": "Isotropic TIM; k=3 W/m-K",
        "Internal_Air_Volume": "Air",
    }
    for body, material in expected_materials.items():
        self.assertEqual(p.MATERIAL_INTENT[body], material)
    self.assertEqual(set(p.SOLID_BODIES) | set(p.FLUID_BODIES), set(p.MATERIAL_INTENT))

    self.assertEqual(p.MODEL_FILE, "Hinoki_Thermal_CHT_Model.FCStd")
    self.assertEqual(p.SOLIDS_STEP, "Hinoki_Thermal_CHT_Solids.step")
    self.assertEqual(p.AIR_STEP, "Hinoki_Thermal_Internal_Air.step")
    self.assertEqual(p.SETUP_JSON, "Hinoki_Thermal_FLOEFD_Setup.json")
    self.assertEqual(p.REVIEW_JSON, "Hinoki_Thermal_CHT_Review.json")
