"""Open the Iteration 02 review CAD, apply review styling, and export PNG."""

from pathlib import Path
import os

import FreeCAD as App
import FreeCADGui as Gui


SCRIPT_PATH = Path(
    globals().get(
        "__file__",
        Path.cwd() / "cad" / "iteration-02" / "preview_hinoki_iteration02.py",
    )
)
CAD_PATH = SCRIPT_PATH.with_name("Hinoki_Concept_CAD_Iteration02_Review.FCStd")
OUTPUT_PATH = SCRIPT_PATH.with_name("Hinoki_Concept_CAD_Iteration02_Review_Preview.png")
DOC_NAME = "Hinoki_Concept_CAD_Iteration02_Review"


try:
    doc = App.getDocument(DOC_NAME)
except NameError:
    doc = App.open(str(CAD_PATH))

if not getattr(App, "GuiUp", 0):
    raise RuntimeError("Preview export requires FreeCAD GUI, not freecadcmd.exe.")

gui_doc = Gui.activeDocument()
styles = {
    "Head_Envelope": ((0.72, 0.75, 0.78), 94),
    "OWT_LM3237_Display_Proxy": ((0.06, 0.18, 0.28), 10),
    "Upper_AV_Reserve": ((0.95, 0.65, 0.12), 78),
    "LI_IMX477_140H_Camera": ((0.04, 0.04, 0.04), 0),
    "Privacy_Shutter_Assumption": ((0.95, 0.65, 0.12), 0),
    "Camera_FOV_KeepOut": ((0.25, 0.70, 0.95), 94),
    "VESA_200x200_Interface": ((0.28, 0.48, 0.78), 38),
    "Desktop_Base_Assumption": ((0.14, 0.16, 0.18), 10),
    "Ergotron_HX_Mechanism_Benchmark": ((0.26, 0.58, 0.42), 44),
    "Low_Forward_Envelope": ((0.25, 0.70, 0.95), 92),
    "High_Rearward_Envelope": ((0.90, 0.40, 0.25), 92),
}
for obj in doc.Objects:
    view = gui_doc.getObject(obj.Name)
    if view is not None and hasattr(obj, "Shape") and not obj.Shape.isNull():
        view.Visibility = True
        if obj.Name in styles:
            view.ShapeColor, view.Transparency = styles[obj.Name]

gui_doc.activeView().setAnimationEnabled(False)
gui_doc.activeView().viewAxonometric()
gui_doc.activeView().fitAll()
gui_doc.activeView().saveImage(str(OUTPUT_PATH), 1920, 1080, "Current")
print("Hinoki Iteration 02 preview exported: {}".format(OUTPUT_PATH))
if os.environ.get("HINOKI_PREVIEW_AUTOCLOSE") == "1":
    Gui.getMainWindow().close()
