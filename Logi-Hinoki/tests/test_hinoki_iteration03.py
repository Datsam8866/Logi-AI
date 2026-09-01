"""Contract checks for the Hinoki Calm Crown Iteration 03 CAD."""

from pathlib import Path
import importlib.util
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CAD_ROOT = PROJECT_ROOT / "cad" / "iteration-03"
PARAMETERS_FILE = CAD_ROOT / "hinoki_calm_crown_parameters.py"


def load_parameters():
    spec = importlib.util.spec_from_file_location(
        "hinoki_calm_crown_parameters", PARAMETERS_FILE
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HinokiIteration03Tests(unittest.TestCase):
    def test_parameter_contract_matches_approved_design(self):
        self.assertTrue(PARAMETERS_FILE.exists())
        p = load_parameters()

        self.assertEqual(
            p.HEAD,
            {
                "width": 742.0,
                "height": 492.0,
                "depth": 62.0,
                "corner_radius": 18.0,
            },
        )
        self.assertEqual(p.CROWN_HEIGHT, 72.0)
        self.assertEqual(p.ACTIVE_AREA, {"width": 708.4, "height": 398.5})
        self.assertEqual(p.VESA_PATTERN, 100.0)
        self.assertEqual(
            p.STAND_MOTION,
            {"travel": 120.0, "tilt_forward": -5.0, "tilt_rear": 20.0},
        )
        self.assertEqual(
            p.BASE, {"width": 420.0, "depth": 285.0, "height": 68.0}
        )
        self.assertEqual(
            p.BASE_POWER, {"width": 360.0, "depth": 240.0, "height": 45.0}
        )
        self.assertEqual(
            p.BALLAST, {"width": 380.0, "depth": 250.0, "height": 8.0}
        )

        expected_export_objects = (
            "Front_Glass",
            "Display_Mask",
            "Crown_Shell",
            "Speaker_Insert_Left",
            "Speaker_Insert_Right",
            "Camera_Pill",
            "Camera_Lens_Window",
            "Shutter_Rail",
            "Shutter_Tab_Open",
            "Fill_Light_Left",
            "Fill_Light_Right",
            "Radar_Window",
            "ALS_Window",
            "Rear_Shell",
            "Rear_Service_Cover",
            "Vent_Insert_Lower",
            "IO_Recess",
            "Stand_Fixed_Spine",
            "Stand_Moving_Spine",
            "Pivot_Pod",
            "VESA_Interface_Cover",
            "Base_Upper",
            "Base_Lower",
            "Foot_Left",
            "Foot_Right",
        )
        expected_mic_apertures = (
            "Mic_Aperture_Left_Outer",
            "Mic_Aperture_Left_Inner",
            "Mic_Aperture_Right_Inner",
            "Mic_Aperture_Right_Outer",
        )
        self.assertEqual(p.PRODUCT_EXPORT_OBJECTS, expected_export_objects)
        self.assertIn("Front_Glass", p.PRODUCT_EXPORT_OBJECTS)
        self.assertIn("Rear_Service_Cover", p.PRODUCT_EXPORT_OBJECTS)
        self.assertNotIn("Camera_FOV_KeepOut", p.PRODUCT_EXPORT_OBJECTS)
        self.assertEqual(
            p.REQUIRED_VISIBLE_OBJECTS,
            expected_export_objects + expected_mic_apertures,
        )
        self.assertEqual(
            p.REQUIRED_INTERNAL_CLAIMS,
            (
                "Panel_Touch_Claim",
                "Speaker_Claim_Left",
                "Speaker_Claim_Right",
                "Camera_ISP_Claim",
                "QC7790_Claim",
                "Heat_Spreader_Claim",
                "USB_C_Interface_Claim",
                "Rear_IO_Board_Claim",
                "VESA_Reinforcement_Claim",
                "Base_Power_PD_Claim",
                "Ballast_Claim",
                "Cable_Loop_Claim",
            ),
        )

        expected_score_weights = {
            "external_design_completeness": 0.15,
            "architecture_consistency": 0.20,
            "visual_communication": 0.10,
            "geometry_health": 0.20,
            "step_portability": 0.10,
            "requirement_traceability": 0.15,
            "risk_integrity": 0.10,
        }
        self.assertEqual(p.SCORE_WEIGHTS, expected_score_weights)
        self.assertAlmostEqual(sum(p.SCORE_WEIGHTS.values()), 1.0)
        self.assertEqual(p.CONCEPT_SCORE_THRESHOLD, 80.0)
        self.assertEqual(
            p.MINIMUM_CATEGORY_SCORES,
            {
                "external_design_completeness": 3,
                "architecture_consistency": 4,
                "visual_communication": 3,
                "geometry_health": 4,
                "step_portability": 4,
                "requirement_traceability": 4,
                "risk_integrity": 3,
            },
        )


if __name__ == "__main__":
    unittest.main()
