"""Export a validated head-only LOD 3 STEP and its traceability JSON files."""

import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

import FreeCAD as App
import Import


SCRIPT_PATH = Path(globals().get("__file__", sys._getframe().f_code.co_filename)).resolve()
if str(SCRIPT_PATH.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT_PATH.parent))

import hinoki_lod3_parameters as p
from review_hinoki_lod3 import validate_master


OUTPUT_KEYS = ("head_step", "manifest_json", "validation_json")
REFERENCE_ASSEMBLY = "08_Reference_Datums_Keepouts"
STAND_ASSEMBLY = "06_Stand_Base_Kinematics"


def _temporary_path(destination):
    """Reserve an owned same-directory file, retaining the format extension."""
    descriptor, name = tempfile.mkstemp(
        prefix="." + destination.stem + ".", suffix=destination.suffix,
        dir=str(destination.parent),
    )
    os.close(descriptor)
    return Path(name)


def _geometry_record(shape):
    box = shape.BoundBox
    return {
        "bbox_mm": [float(getattr(box, key)) for key in
                    ("XMin", "YMin", "ZMin", "XMax", "YMax", "ZMax")],
        "volume_mm3": float(shape.Volume),
        "solid_count": len(shape.Solids),
    }


def _validate_step(path, expected):
    """Match semantic roots by stable labels, including multi-solid parts."""
    document = App.newDocument("Hinoki_LOD3_STEP_Reimport")
    try:
        Import.insert(str(path), document.Name)
        # FreeCAD wraps a multi-object STEP in one assembly. Compound semantic
        # parts become nested App::Part groups; their Name retains the STEP
        # product name while Label may gain digits due to duplicate child labels.
        features = [obj for obj in document.Objects
                    if obj.TypeId in ("Part::Feature", "App::Part")]
        roots = [obj for obj in features
                 if not any(parent in features for parent in obj.InList)]
        if len(roots) == 1 and roots[0].Name == "Hinoki_LOD3_Head_Export":
            roots = [obj for obj in roots[0].Group if obj in features]
        def semantic_name(obj):
            return obj.Name if obj.TypeId == "App::Part" else obj.Label
        names = [semantic_name(obj) for obj in roots]
        if len(names) != len(expected) or set(names) != set(expected):
            raise RuntimeError("STEP semantic-body membership mismatch: " + repr(names))
        for obj in roots:
            shape = obj.Shape
            if shape.isNull() or not shape.isValid() or shape.Volume <= 0 or not shape.Solids:
                raise RuntimeError("STEP invalid positive solid: " + obj.Label)
            actual = _geometry_record(shape)
            wanted = expected[semantic_name(obj)]
            if actual["solid_count"] != wanted["solid_count"]:
                raise RuntimeError("STEP solid count mismatch: " + obj.Label)
            if abs(actual["volume_mm3"] - wanted["volume_mm3"]) > max(0.01, wanted["volume_mm3"] * 1e-7):
                raise RuntimeError("STEP volume mismatch: " + obj.Label)
            if any(abs(left - right) > 0.1 for left, right in zip(actual["bbox_mm"], wanted["bbox_mm"])):
                raise RuntimeError("STEP millimetre scale/bounds mismatch: " + obj.Label)
        return {"units": "mm", "body_count": len(names), "names": sorted(names),
                "status": "Pass", "bbox_tolerance_mm": 0.1}
    finally:
        App.closeDocument(document.Name)


def _publish_files(pairs):
    """Replace a verified set, rolling back completed replacements on error.

    This protects against handled exceptions, not process termination or power
    loss between replacements. Recovery backups are retained if rollback fails.
    """
    backups = {}
    changed = []
    retain = set()
    try:
        for staged, destination in pairs:
            if staged.parent != destination.parent or staged == destination:
                raise ValueError("publication requires distinct same-directory staging")
            if destination.exists():
                if not destination.is_file():
                    raise ValueError("output is not a regular file: " + str(destination))
                backup = _temporary_path(destination)
                backups[destination] = backup
                shutil.copyfile(destination, backup)
            else:
                backups[destination] = None
        for staged, destination in pairs:
            os.replace(str(staged), str(destination))
            changed.append(destination)
    except Exception as error:
        recovery_errors = []
        for destination in reversed(changed):
            backup = backups[destination]
            try:
                if backup is None:
                    destination.unlink()
                else:
                    os.replace(str(backup), str(destination))
            except OSError as recovery_error:
                if backup is not None:
                    retain.add(backup)
                recovery_errors.append(str(recovery_error))
        if recovery_errors:
            raise RuntimeError("publication and rollback failed; retained recovery files: "
                               + repr(sorted(str(path) for path in retain))) from error
        raise
    finally:
        for path in [stage for stage, _ in pairs] + list(backups.values()):
            if path is not None and path not in retain and path.is_file():
                path.unlink()


def export_package(model_path, output_directory):
    """Validate the source and staged package before replacing three outputs.

    The caller must explicitly choose the destination; the native model is
    read-only. Reference/keep-out geometry and deferred stand parts are excluded.
    """
    output_directory = Path(output_directory).resolve()
    model_path = Path(model_path).resolve()
    staged = []
    owned_documents = []
    try:
        source = App.openDocument(str(model_path))
        owned_documents.append(source.Name)
        report = validate_master(source)
        if report["status"] != "Pass":
            raise RuntimeError("LOD 3 master validation failed")
        semantic = [obj for obj in source.Objects if getattr(obj, "IsSemanticPart", False)]
        # Iter 7 (Task 6): stand/base parts are now approved for export
        # as part of the full-assembly STEP. Head-only export is still
        # available by filtering semantic to exclude STAND_ASSEMBLY.
        part_ids = [obj.PartID for obj in semantic]
        if len(part_ids) != len(set(part_ids)):
            raise RuntimeError("duplicate semantic PartID")
        physical = [obj for obj in semantic
                    if obj.ParentAssembly != REFERENCE_ASSEMBLY
                    and getattr(obj, "PhysicalCollision", True)]
        expected = {obj.Name: _geometry_record(obj.Shape) for obj in physical}
        for obj in physical:
            if not obj.Shape.Solids:
                raise RuntimeError("export body has no solids: " + obj.Name)
        manifest = {"scope": "HeadOnly", "units": "mm",
                    "limitations": p.PROTOTYPE_LIMITATION, "parts": []}
        for obj in semantic:
            row = {}
            for key in p.METADATA_KEYS:
                value = getattr(obj, key, None)
                if value is None:
                    row[key] = None
                elif key in ("HeatLoadW", "ThermalConductivityWmK"):
                    row[key] = float(value)
                elif hasattr(value, "Value"):
                    row[key] = float(value.Value)
                else:
                    row[key] = value
            row.update(name=obj.Name, label=obj.Label, exported=obj.Name in expected)
            if obj.Name in expected:
                row.update(expected[obj.Name])
            manifest["parts"].append(row)
        output_directory.mkdir(parents=True, exist_ok=True)
        destinations = [output_directory / p.OUTPUT_FILES[key] for key in OUTPUT_KEYS]
        for destination in destinations:
            staged.append(_temporary_path(destination))
        # Copy shapes into an owned export document to give STEP stable labels
        # without changing source display labels or the FCStd file.
        export_doc = App.newDocument("Hinoki_LOD3_Head_Export")
        owned_documents.append(export_doc.Name)
        export_objects = []
        for original in physical:
            obj = export_doc.addObject("Part::Feature", original.Name)
            obj.Label = original.Name
            obj.Shape = original.Shape.copy()
            export_objects.append(obj)
        export_doc.recompute()
        Import.export(export_objects, str(staged[0]))
        report["step_export"] = _validate_step(staged[0], expected)
        for path, payload in ((staged[1], manifest), (staged[2], report)):
            path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            try:
                reopened = json.loads(path.read_text(encoding="utf-8"))
            except (ValueError, OSError) as error:
                raise RuntimeError("staged JSON cannot reopen: " + path.name) from error
            if reopened != payload:
                raise RuntimeError("staged JSON content mismatch: " + path.name)
        _publish_files(list(zip(staged, destinations)))
        return report
    finally:
        for name in reversed(owned_documents):
            if name in App.listDocuments():
                App.closeDocument(name)
        for path in staged:
            if path.is_file():
                path.unlink()


def main():
    """Run explicit-destination export with a unique result sentinel."""
    try:
        output = os.environ.get("HINOKI_LOD3_EXPORT_DIR")
        if not output:
            raise ValueError("set HINOKI_LOD3_EXPORT_DIR explicitly; no default formal publication")
        model = os.environ.get("HINOKI_LOD3_MODEL_PATH", str(SCRIPT_PATH.parent / p.OUTPUT_FILES["master_fcstd"]))
        export_package(model, output)
    except Exception as error:
        print("HINOKI_LOD3_EXPORT_FAIL {}".format(error))
        return 1
    print("HINOKI_LOD3_EXPORT_OK {}".format(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
