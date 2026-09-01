"""Acceptance checks for the Hinoki Iteration 02 preliminary review CAD."""

from pathlib import Path
import json
import os
import subprocess
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CAD_ROOT = PROJECT_ROOT / "cad" / "iteration-02"
BUILD_SCRIPT = CAD_ROOT / "build_hinoki_iteration02.py"
REVIEW_SCRIPT = CAD_ROOT / "review_iteration02.py"
CAD_FILE = CAD_ROOT / "Hinoki_Concept_CAD_Iteration02_Review.FCStd"
REVIEW_FILE = CAD_ROOT / "Hinoki_Iteration02_CAD_Review.json"
FREECAD_CMD = Path(
    os.environ.get(
        "FREECAD_CMD",
        r"C:\Users\skuan1\AppData\Local\Programs\FreeCAD 1.1\bin\freecadcmd.exe",
    )
)


def run_freecad_script(script_path):
    return subprocess.run(
        [str(FREECAD_CMD), "-c"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
        input="exec(compile(open(r'{}', encoding='utf-8').read(), r'{}', 'exec'))\n".format(
            script_path.as_posix(), script_path.as_posix()
        ),
    )


class HinokiIteration02Tests(unittest.TestCase):
    def test_iteration02_review_cad_contains_verified_baselines_and_open_risks(self):
        self.assertTrue(BUILD_SCRIPT.exists(), "Iteration 02 builder must exist")
        self.assertTrue(REVIEW_SCRIPT.exists(), "Iteration 02 review script must exist")
        self.assertTrue(FREECAD_CMD.exists(), "FreeCAD command-line executable must exist")

        run_freecad_script(BUILD_SCRIPT)
        self.assertTrue(CAD_FILE.exists(), "Iteration 02 review CAD must be created")
        run_freecad_script(REVIEW_SCRIPT)
        self.assertTrue(REVIEW_FILE.exists(), "Iteration 02 review report must be created")

        probe = """
import FreeCAD as App
doc = App.open(r'{cad_file}')
required = [
    'Iteration02_Metadata', 'Review_Parameters', 'Head_Envelope',
    'OWT_LM3237_Display_Proxy', 'LI_IMX477_140H_Camera',
    'Privacy_Shutter_Assumption', 'VESA_200x200_Interface',
    'Ergotron_HX_Mechanism_Benchmark', 'Low_Forward_Envelope',
    'High_Rearward_Envelope'
]
missing = [name for name in required if doc.getObject(name) is None]
assert not missing, 'Missing objects: ' + ', '.join(missing)
params = doc.getObject('Review_Parameters')
assert params.HeadWidth == 760.0
assert params.HeadDepth == 80.0
assert params.HeadHeight == 540.0
assert params.DisplayWidth == 750.4
assert params.DisplayDepth == 56.5
assert params.DisplayHeight == 452.7
assert params.CameraWidth == 38.0
assert params.CameraDepth == 25.78
assert params.CameraHeight == 38.0
assert params.CameraHFOV == 140.0
assert params.VESAPattern == 200.0
assert params.DisplayProxyMass == 14.0
assert params.StandCapacityMax == 19.1
display = doc.getObject('OWT_LM3237_Display_Proxy')
camera = doc.getObject('LI_IMX477_140H_Camera')
shutter = doc.getObject('Privacy_Shutter_Assumption')
stand = doc.getObject('Ergotron_HX_Mechanism_Benchmark')
assert display.Classification == 'Verified review proxy'
assert display.SourcePartNumber == 'LM-3237-26B-4K'
assert camera.Classification == 'Verified component envelope'
assert camera.SourcePartNumber == 'LI-IMX477-MIPI-140H'
assert camera.HorizontalFOV == 140.0
assert shutter.Classification == 'Assumed'
assert stand.Classification == 'Verified mechanism benchmark'
assert stand.SourcePartNumber == '45-475-224'
assert doc.getObject('VESA_200x200_Interface').PatternSize == 200.0
print('CAD iteration 02 acceptance checks passed')
""".format(cad_file=CAD_FILE.as_posix())
        result = subprocess.run(
            [str(FREECAD_CMD), "-c"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
            input=probe,
        )
        self.assertIn("CAD iteration 02 acceptance checks passed", result.stdout)

        review = json.loads(REVIEW_FILE.read_text(encoding="utf-8"))
        self.assertEqual(review["cad_review_status"], "PassWithOpenRisks")
        self.assertEqual(review["containment_failures"], [])
        self.assertAlmostEqual(review["display_proxy"]["side_margin_each_mm"], 4.8)
        self.assertAlmostEqual(review["display_proxy"]["top_reserve_mm"], 87.3)
        self.assertAlmostEqual(review["display_proxy"]["depth_reserve_mm"], 23.5)
        self.assertAlmostEqual(review["stand_benchmark"]["pre_av_compute_headroom_kg"], 5.1)
        self.assertEqual(
            set(review["open_risks"]),
            {
                "Integrated display proxy must be decomposed into bare panel/touch/electronics packages.",
                "Privacy shutter travel and optical obscuration remain assumed.",
                "Custom stand geometry, centre of gravity, cable motion and tip stability remain open.",
            },
        )


if __name__ == "__main__":
    unittest.main()
