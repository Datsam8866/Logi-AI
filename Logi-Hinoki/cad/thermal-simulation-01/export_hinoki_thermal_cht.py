"""Export the approved Hinoki CHT solids and internal air for FLOEFD import."""

import os
import sys
import uuid
from pathlib import Path

import FreeCAD as App
import Import
import Part


SCRIPT_PATH = Path(
    globals().get("__file__", sys._getframe().f_code.co_filename)
).resolve()
if str(SCRIPT_PATH.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT_PATH.parent))

import hinoki_thermal_parameters as parameters


MODEL_PATH = Path(
    os.environ.get(
        "HINOKI_THERMAL_MODEL_PATH", SCRIPT_PATH.with_name(parameters.MODEL_FILE)
    )
)
SOLIDS_PATH = Path(
    os.environ.get(
        "HINOKI_THERMAL_SOLIDS_STEP_PATH",
        SCRIPT_PATH.with_name(parameters.SOLIDS_STEP),
    )
)
AIR_PATH = Path(
    os.environ.get(
        "HINOKI_THERMAL_AIR_STEP_PATH", SCRIPT_PATH.with_name(parameters.AIR_STEP)
    )
)


def _temporary_path(path):
    """Return a unique same-directory STEP staging path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.with_name(".{}.{}.step".format(path.stem, uuid.uuid4().hex))


def _positive_feature_objects(document):
    return [
        obj for obj in document.Objects
        if hasattr(obj, "Shape") and obj.Shape.isValid() and obj.Shape.Volume > 0.0
    ]


def _semantic_body_features(document):
    """Discard importer-only aggregate containers and their duplicate compound children."""
    features = _positive_feature_objects(document)
    containers = [obj for obj in features if len(obj.Shape.Solids) > 1]
    top_container = max(containers, key=lambda obj: obj.Shape.Volume, default=None)
    body_containers = [obj for obj in containers if obj is not top_container]

    def is_container_child(obj):
        return any(
            obj is not container
            and abs(container.Shape.common(obj.Shape).Volume - obj.Shape.Volume) <= 0.01
            for container in body_containers
        )

    return [
        obj for obj in features
        if obj is not top_container and not is_container_child(obj)
    ]


def _validate_source_objects(document, names):
    """Resolve exactly the named valid, positive-volume Part features."""
    objects = []
    for name in names:
        obj = document.getObject(name)
        if obj is None or obj.TypeId != "Part::Feature":
            raise RuntimeError("missing Part::Feature {}".format(name))
        shape = obj.Shape
        if not shape.isValid() or shape.Volume <= 0.0 or not shape.Solids:
            raise RuntimeError("invalid positive-volume body {}".format(name))
        objects.append(obj)
    if len(objects) != len(names):
        raise RuntimeError("source body count mismatch")
    return objects


def _combined_bbox(objects):
    """Return a native compound bounding box without changing exported bodies."""
    return Part.makeCompound([obj.Shape for obj in objects]).BoundBox


def _validate_step_reimport(path, expected_count, expected_bbox):
    """Reopen one staged STEP and validate exact body count and millimetre scale."""
    document = App.newDocument("Hinoki_STEP_Reimport")
    try:
        Import.insert(str(path), document.Name)
        objects = _semantic_body_features(document)
        if len(objects) != expected_count:
            raise RuntimeError(
                "STEP {} positive feature count {} != {}".format(
                    path.name, len(objects), expected_count
                )
            )
        for obj in objects:
            if not obj.Shape.isValid() or obj.Shape.Volume <= 0.0:
                raise RuntimeError("STEP {} has invalid body {}".format(path.name, obj.Name))
        bounds = _combined_bbox(objects)
        actual = (
            bounds.XMin, bounds.YMin, bounds.ZMin,
            bounds.XMax, bounds.YMax, bounds.ZMax,
        )
        if any(abs(left - right) > 0.1 for left, right in zip(actual, expected_bbox)):
            raise RuntimeError(
                "STEP {} bounding box {} != {}".format(path.name, actual, expected_bbox)
            )
    finally:
        App.closeDocument(document.Name)


def _restore_path(path, original_bytes):
    """Rollback a changed handoff file without deleting a pre-existing file first."""
    if original_bytes is None:
        if path.exists():
            path.unlink()
        return
    temporary = _temporary_path(path)
    try:
        temporary.write_bytes(original_bytes)
        os.replace(str(temporary), str(path))
    finally:
        if temporary.exists():
            temporary.unlink()


def _publish_pair(solids_temp, air_temp):
    """Replace both verified exports, restoring the first if the second fails."""
    original_solids = SOLIDS_PATH.read_bytes() if SOLIDS_PATH.exists() else None
    original_air = AIR_PATH.read_bytes() if AIR_PATH.exists() else None
    try:
        os.replace(str(solids_temp), str(SOLIDS_PATH))
        try:
            os.replace(str(air_temp), str(AIR_PATH))
        except Exception:
            _restore_path(SOLIDS_PATH, original_solids)
            raise
    except Exception:
        if AIR_PATH.exists() and original_air is not None:
            # The second replacement can only have succeeded if no exception occurred.
            pass
        raise


def export_handoff(model_path=MODEL_PATH):
    """Export validated source objects to staged STEP files before publication."""
    source = App.openDocument(str(model_path))
    solids_temp = _temporary_path(SOLIDS_PATH)
    air_temp = _temporary_path(AIR_PATH)
    try:
        solids = _validate_source_objects(source, parameters.SOLID_BODIES)
        air = _validate_source_objects(source, parameters.FLUID_BODIES)
        solids_bbox = _combined_bbox(solids)
        air_bbox = _combined_bbox(air)
        Import.export(solids, str(solids_temp))
        Import.export(air, str(air_temp))
        _validate_step_reimport(
            solids_temp,
            len(parameters.SOLID_BODIES),
            (
                solids_bbox.XMin, solids_bbox.YMin, solids_bbox.ZMin,
                solids_bbox.XMax, solids_bbox.YMax, solids_bbox.ZMax,
            ),
        )
        _validate_step_reimport(
            air_temp,
            len(parameters.FLUID_BODIES),
            (
                air_bbox.XMin, air_bbox.YMin, air_bbox.ZMin,
                air_bbox.XMax, air_bbox.YMax, air_bbox.ZMax,
            ),
        )
        _publish_pair(solids_temp, air_temp)
        return SOLIDS_PATH, AIR_PATH
    finally:
        App.closeDocument(source.Name)
        if solids_temp.exists():
            solids_temp.unlink()
        if air_temp.exists():
            air_temp.unlink()


def main():
    """Run export with exactly one success sentinel."""
    try:
        solids, air = export_handoff()
    except Exception as error:
        print("HINOKI_THERMAL_EXPORT_FAIL {}".format(error))
        return 1
    print("HINOKI_THERMAL_EXPORT_OK solids={} air={}".format(solids, air))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
