"""Contract and geometry tests for the Hinoki LOD 3 inferred prototype."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = PROJECT_ROOT / "cad" / "lod3-inferred-prototype-01"
PARAMETERS_FILE = PACKAGE_ROOT / "hinoki_lod3_parameters.py"
SOURCES_FILE = PACKAGE_ROOT / "hinoki_lod3_sources.py"


def load_module(path, name):
    spec = spec_from_file_location(name, path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestFrozenEngineeringContract(unittest.TestCase):
    def test_frozen_product_envelope_and_display_stack(self):
        p = load_module(PARAMETERS_FILE, "hinoki_lod3_parameters")
        self.assertEqual((742.0, 492.0, 62.0), tuple(p.HEAD.values()))
        self.assertEqual(
            (726.0, 446.0, 3.2),
            tuple(p.DISPLAY_STACK["Cover_Glass"].values()),
        )
        self.assertEqual(
            6000.0,
            p.VENTS["Inlet_Lower_Rear"]["minimum_open_area"],
        )
        self.assertEqual(
            (
                "01_Display_Stack",
                "02_Housing_Structure",
                "03_Electronics_Thermal",
                "04_Camera_Lighting_Sensors",
                "05_Audio_IO_Cables",
                "06_Stand_Base_Kinematics",
                "07_Fasteners_Seals_Consumables",
                "08_Reference_Datums_Keepouts",
            ),
            p.REQUIRED_TOP_GROUPS,
        )

    def test_source_precedence_rejects_uniform_dixie_scale(self):
        s = load_module(SOURCES_FILE, "hinoki_lod3_sources")
        result = s.resolve_candidates(
            "HeadWidth",
            (
                {
                    "source_class": "DixieReference",
                    "value": 14498.4,
                    "source_reference": "Dixie conflicting literal",
                },
                {
                    "source_class": "Known",
                    "value": 742.0,
                    "source_reference": "Approved Hinoki baseline",
                },
            ),
        )
        self.assertEqual(742.0, result["value"])
        self.assertEqual("Known", result["source_class"])
        self.assertEqual(1, len(result["rejected_candidates"]))
        self.assertFalse(s.UNIFORM_DIXIE_SCALE_POLICY["allowed"])
        self.assertEqual("MP-077", s.UNIFORM_DIXIE_SCALE_POLICY["parameter_id"])

    def test_thermal_case_is_exactly_57_w(self):
        p = load_module(PARAMETERS_FILE, "hinoki_lod3_parameters")
        self.assertEqual(35.0, p.THERMAL_CASE["ambient_c"])
        self.assertEqual("NaturalConvection", p.THERMAL_CASE["cooling_mode"])
        self.assertFalse(p.THERMAL_CASE["fan_present"])
        self.assertEqual(10, len(p.HEAT_LOADS_W))
        self.assertAlmostEqual(57.0, sum(p.HEAT_LOADS_W.values()), places=9)

    def test_manifest_schema_denies_manufacturing_authority(self):
        p = load_module(PARAMETERS_FILE, "hinoki_lod3_parameters")
        record = p.part_metadata(
            part_id="HNK-DS-001",
            part_name="Cover_Glass",
            parent_assembly="01_Display_Stack",
            material_intent="Display glass",
            source_class="EngineeringAssumption",
            source_reference="Approved LOD 3 design section 5.1",
            confidence="Medium",
            thermal_disposition="Keep",
            heat_load_w=0.0,
        )
        self.assertEqual(set(p.METADATA_KEYS), set(record))
        self.assertIs(False, record["ManufacturingAuthority"])
        self.assertEqual("A", record["Revision"])
        self.assertIn("not manufacturing release", p.PROTOTYPE_LIMITATION.lower())


if __name__ == "__main__":
    unittest.main()
