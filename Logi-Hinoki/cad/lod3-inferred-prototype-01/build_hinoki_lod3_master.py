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
from hinoki_lod3_av_io import build_av_io
from hinoki_lod3_common import make_groups
from hinoki_lod3_display_housing import build_display_housing
from hinoki_lod3_electronics_thermal import build_electronics_thermal
from review_hinoki_lod3 import validate_master


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
    build_av_io(doc, groups)
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
    document_name = None
    temporary = destination.with_name(destination.name + ".tmp.FCStd")
    try:
        doc = build_document()
        document_name = doc.Name
        review = validate_master(doc)
        if review["status"] != "Pass":
            failed_gates = sorted(
                name
                for name, passed in review["hard_gates"].items()
                if not passed
            )
            raise RuntimeError(
                "LOD 3 master validation failed: " + ", ".join(failed_gates)
            )
        part_count = review["semantic_parts"]["count"]
        save_atomically(doc, destination)
        doc = None
        print(
            "HINOKI_LOD3_BUILD_OK path={} semantic_parts={}".format(
                destination, part_count
            )
        )
    except Exception:
        if document_name in App.listDocuments():
            App.closeDocument(document_name)
        try:
            if temporary.exists():
                temporary.unlink()
        except OSError:
            # Cleanup must not replace the original build failure signal.
            pass
        print("HINOKI_LOD3_BUILD_FAILED")
        return 1
    finally:
        for document_name in tuple(App.listDocuments()):
            App.closeDocument(document_name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
