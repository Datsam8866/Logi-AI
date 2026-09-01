"""Apply a review view and export a PNG preview from the open Hinoki CAD document.

Run this script inside the FreeCAD GUI after opening the Iteration 01 FCStd file.
"""

from pathlib import Path

import FreeCAD as App
import FreeCADGui as Gui


SCRIPT_PATH = Path(globals().get("__file__", Path.cwd() / "cad" / "iteration-01" / "preview_hinoki_iteration01.py"))
OUTPUT_PATH = SCRIPT_PATH.with_name("Hinoki_Concept_CAD_Iteration01_Preview.png")
DOC_NAME = "Hinoki_Concept_CAD_Iteration01"


doc = App.getDocument(DOC_NAME)
if doc is None:
    raise RuntimeError("Open {} before running this preview script.".format(DOC_NAME))

gui_doc = Gui.activeDocument()
styles = {
    "Head_Envelope": ((0.72, 0.75, 0.78), 92),
    "Display_Touch_Stack": ((0.08, 0.12, 0.16), 0),
    "Upper_AV_Bar": ((0.16, 0.18, 0.20), 20),
    "Speaker_Left": ((0.18, 0.20, 0.22), 15),
    "Speaker_Right": ((0.18, 0.20, 0.22), 15),
    "Camera_Manual_Shutter": ((0.05, 0.05, 0.05), 0),
    "Privacy_Shutter_Closed": ((0.72, 0.75, 0.78), 0),
    "Front_Light_Left": ((1.00, 0.82, 0.25), 0),
    "Front_Light_Right": ((1.00, 0.82, 0.25), 0),
    "Microphone_Left": ((0.30, 0.80, 0.60), 15),
    "Microphone_Right": ((0.30, 0.80, 0.60), 15),
    "Radar_KeepOut": ((0.30, 0.80, 0.60), 65),
    "Ambient_Light_Provision": ((0.30, 0.80, 0.60), 30),
    "Camera_FOV_KeepOut": ((0.25, 0.70, 0.95), 94),
    "Compute_Thermal_Module": ((0.75, 0.30, 0.18), 10),
    "USB_C_PD_Interface": ((0.20, 0.45, 0.82), 10),
    "Rear_IO_Bay": ((0.20, 0.45, 0.82), 10),
    "VESA_Reinforcement": ((0.42, 0.45, 0.50), 30),
    "Rear_Vent_KeepOut": ((0.30, 0.80, 0.60), 78),
    "Desktop_Base": ((0.12, 0.14, 0.16), 0),
    "ACDC_BulkPD_Ballast": ((0.58, 0.22, 0.20), 55),
    "Height_Column": ((0.42, 0.45, 0.50), 20),
    "VESA_Pivot_Carrier": ((0.42, 0.45, 0.50), 40),
    "Cable_Motion_KeepOut": ((0.30, 0.80, 0.60), 88),
    "Low_Forward_Envelope": ((0.25, 0.70, 0.95), 90),
    "High_Rearward_Envelope": ((0.90, 0.40, 0.25), 90),
}
for obj in doc.Objects:
    view = gui_doc.getObject(obj.Name)
    if view is not None and hasattr(obj, "Shape") and not obj.Shape.isNull():
        view.Visibility = True
        if obj.Name in styles:
            view.ShapeColor, view.Transparency = styles[obj.Name]

gui_doc.activeView().viewAxonometric()
gui_doc.activeView().fitAll()
gui_doc.activeView().saveImage(str(OUTPUT_PATH), 1920, 1080, "Current")
print("Hinoki Iteration 01 preview exported: {}".format(OUTPUT_PATH))
