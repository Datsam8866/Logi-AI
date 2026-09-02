"""Build the Hinoki LOD 3 inferred master assembly in FreeCAD."""

import os
from pathlib import Path
import sys

import FreeCAD as App


SCRIPT_PATH = Path(
    globals().get("__file__", sys._getframe().f_code.co_filename)
).resolve()
PACKAGE_DIR = SCRIPT_PATH.parent
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

import hinoki_lod3_parameters as p
from hinoki_lod3_common import make_groups
from hinoki_lod3_display_housing import build_display_housing
from hinoki_lod3_electronics_thermal import build_electronics_thermal


def output_path():
    return Path(
        os.environ.get(
            "HINOKI_LOD3_MODEL_OUT",
            str(PACKAGE_DIR / p.OUTPUT_FILES["master_fcstd"]),
        )
    ).resolve()


def build_document():
    doc = App.newDocument("Hinoki_LOD3_Inferred_Master")
    groups = make_groups(doc, p.REQUIRED_TOP_GROUPS)
    build_display_housing(doc, groups)
    build_electronics_thermal(doc, groups)
    doc.recompute()
    return doc


def save_atomically(doc, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".tmp.FCStd")
    if temporary.exists():
        temporary.unlink()
    doc.saveAs(str(temporary))
    App.closeDocument(doc.Name)
    os.replace(str(temporary), str(destination))


def main():
    destination = output_path()
    doc = None
    temporary = destination.with_name(destination.name + ".tmp.FCStd")
    try:
        doc = build_document()
        part_count = len(
            [
                obj
                for obj in doc.Objects
                if getattr(obj, "IsSemanticPart", False)
            ]
        )
        save_atomically(doc, destination)
        doc = None
        print(
            "HINOKI_LOD3_BUILD_OK path={} semantic_parts={}".format(
                destination, part_count
            )
        )
    except Exception:
        if doc is not None and doc.Name in App.listDocuments():
            App.closeDocument(doc.Name)
        if temporary.exists():
            temporary.unlink()
        print("HINOKI_LOD3_BUILD_FAILED")
        raise
    finally:
        for document_name in tuple(App.listDocuments()):
            App.closeDocument(document_name)


if __name__ == "__main__":
    main()
