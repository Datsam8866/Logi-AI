"""Export the Iteration 02 physical concept geometry to STEP for review.

The export intentionally omits transparent head, motion and camera-FOV
keep-out envelopes. It is a concept-review interchange file, not release or
manufacturing geometry.
"""

from pathlib import Path

import FreeCAD as App
import Import


SCRIPT_PATH = Path(
    globals().get(
        "__file__",
        Path.cwd() / "cad" / "iteration-02" / "export_iteration02_step.py",
    )
)
CAD_FILE = SCRIPT_PATH.with_name("Hinoki_Concept_CAD_Iteration02_Review.FCStd")
STEP_FILE = SCRIPT_PATH.with_name("Hinoki_Concept_CAD_Iteration02_Concept.stp")

EXPORT_OBJECTS = [
    "OWT_LM3237_Display_Proxy",
    "LI_IMX477_140H_Camera",
    "Privacy_Shutter_Assumption",
    "VESA_200x200_Interface",
    "Desktop_Base_Assumption",
    "Ergotron_HX_Mechanism_Benchmark",
]


def main():
    if not CAD_FILE.exists():
        raise FileNotFoundError("Iteration 02 CAD file is missing: {}".format(CAD_FILE))

    doc = App.open(str(CAD_FILE))
    objects = []
    for name in EXPORT_OBJECTS:
        obj = doc.getObject(name)
        if obj is None or not hasattr(obj, "Shape") or obj.Shape.isNull():
            raise RuntimeError("STEP export object is missing or empty: {}".format(name))
        objects.append(obj)

    if STEP_FILE.exists():
        STEP_FILE.unlink()
    Import.export(objects, str(STEP_FILE))
    if not STEP_FILE.exists() or STEP_FILE.stat().st_size <= 1000:
        raise RuntimeError("STEP export was not created or is unexpectedly small")

    print("Hinoki Iteration 02 concept-review STEP exported: {}".format(STEP_FILE))
    print("Exported physical objects: {}".format(", ".join(EXPORT_OBJECTS)))
    print("Warning: concept review only; not release or manufacturing geometry")


if __name__ == "__main__":
    main()
