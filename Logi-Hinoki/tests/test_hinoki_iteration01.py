"""Acceptance checks for the Hinoki Concept CAD Iteration 01 assembly."""

from pathlib import Path
import os
import subprocess
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CAD_ROOT = PROJECT_ROOT / "cad" / "iteration-01"
BUILD_SCRIPT = CAD_ROOT / "build_hinoki_iteration01.py"
CAD_FILE = CAD_ROOT / "Hinoki_Concept_CAD_Iteration01.FCStd"
FREECAD_CMD = Path(
    os.environ.get(
        "FREECAD_CMD",
        r"C:\Users\skuan1\AppData\Local\Programs\FreeCAD 1.1\bin\freecadcmd.exe",
    )
)


class HinokiIteration01Tests(unittest.TestCase):
    def test_iteration01_assembly_contains_required_concept_groups(self):
        self.assertTrue(BUILD_SCRIPT.exists(), "Iteration 01 builder must exist")
        self.assertTrue(FREECAD_CMD.exists(), "FreeCAD command-line executable must exist")

        subprocess.run(
            [str(FREECAD_CMD), "-c"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
            input="exec(compile(open(r'{}', encoding='utf-8').read(), r'{}', 'exec'))\n".format(
                BUILD_SCRIPT.as_posix(), BUILD_SCRIPT.as_posix()
            ),
        )

        self.assertTrue(CAD_FILE.exists(), "Iteration 01 assembly must be created")

        probe = """
import FreeCAD as App
doc = App.open(r'{cad_file}')
required = [
    'Master_Parameters', 'Neutral_Assembly', 'Motion_Envelopes',
    'Head_Envelope', 'Display_Touch_Stack', 'Upper_AV_Bar',
    'Camera_Manual_Shutter', 'Speaker_Left', 'Speaker_Right',
    'Camera_FOV_KeepOut',
    'USB_C_PD_Interface', 'Rear_IO_Bay', 'VESA_Reinforcement',
    'Desktop_Base', 'Height_Column', 'Low_Forward_Envelope',
    'High_Rearward_Envelope'
]
missing = [name for name in required if doc.getObject(name) is None]
assert not missing, 'Missing objects: ' + ', '.join(missing)
params = doc.getObject('Master_Parameters')
assert params.HeadWidth == 760.0
assert params.HeadHeight == 540.0
assert params.HeadDepth == 80.0
assert params.PivotLow == 370.0
assert params.PivotNeutral == 430.0
assert params.PivotHigh == 490.0
assert params.TiltForward == -5.0
assert params.TiltRearward == 20.0
assert params.BaseWidth == 500.0
assert params.BaseDepth == 340.0
head = doc.getObject('Head_Envelope').Shape.BoundBox
display = doc.getObject('Display_Touch_Stack').Shape.BoundBox
av_bar = doc.getObject('Upper_AV_Bar').Shape.BoundBox
assert display.XMin - head.XMin == 15.0
assert head.XMax - display.XMax == 15.0
assert display.ZMin - head.ZMin == 35.0
assert display.ZMax == av_bar.ZMin
camera_fov = doc.getObject('Camera_FOV_KeepOut')
assert camera_fov.HorizontalFOV == 137.0
assert camera_fov.ClearanceStatus.startswith('Concept pass')
assert doc.getObject('Camera_Manual_Shutter').AssumptionID == 'A-016'
assert doc.getObject('Desktop_Base').AssumptionID == 'A-039'
assert doc.getObject('Low_Forward_Envelope').AssumptionID == 'A-035; A-036'
assert doc.getObject('High_Rearward_Envelope').AssumptionID == 'A-035; A-036'
print('CAD iteration 01 acceptance checks passed')
""".format(cad_file=CAD_FILE.as_posix())
        result = subprocess.run(
            [str(FREECAD_CMD), "-c"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
            input=probe,
        )
        self.assertIn("CAD iteration 01 acceptance checks passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
