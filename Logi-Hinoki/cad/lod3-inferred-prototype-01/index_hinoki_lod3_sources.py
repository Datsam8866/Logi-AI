"""Build a metadata-only index of external LOD 3 engineering references."""

import hashlib
import json
import os
from pathlib import Path
import tempfile


REQUIRED_FILES = (
    (
        "Hinoki_Master_Parameters_and_Assumption_Log.xlsx",
        "Known",
    ),
    ("Dixie and Hinoki table.xlsx", "Known"),
    (
        "Dixie/3D/001_dixie65_set_asm_20250425_asm.stp",
        "DixieReference",
    ),
    (
        "Dixie/BOM/logitech_Dixie65_Parts list_REV_20250506V1.xlsx",
        "DixieReference",
    ),
)

REQUIRED_GROUPS = (
    ("Dixie/2D", "DixieReference"),
    ("Dixie/Panel", "DixieReference"),
    ("Dixie/Thermal", "DixieReference"),
)

REJECTED_LITERALS = (
    {
        "literal": "14498.4 mm",
        "reason": (
            "Conflicts with approved 742 mm Hinoki envelope; "
            "uniform Dixie scaling is prohibited."
        ),
    },
)


def _stat_signature(stat):
    return (
        stat.st_dev,
        stat.st_ino,
        stat.st_size,
        stat.st_mtime_ns,
        stat.st_ctime_ns,
    )


def _fingerprint(path):
    before = path.stat()
    digest = hashlib.sha256()
    byte_size = 0
    with open(path, "rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
            byte_size += len(chunk)
    try:
        after = path.stat()
    except OSError as exc:
        raise RuntimeError("Source changed during indexing: " + str(path)) from exc
    if _stat_signature(before) != _stat_signature(after) or byte_size != after.st_size:
        raise RuntimeError("Source changed during indexing: " + str(path))
    return digest.hexdigest(), byte_size


def _record(source_root, path, authority_class):
    digest, byte_size = _fingerprint(path)
    return {
        "path": path.relative_to(source_root).as_posix(),
        "sha256": digest,
        "byte_size": byte_size,
        "authority_class": authority_class,
        "external_reference": True,
        "copied_into_repository": False,
    }


def _publish_inventory(inventory, output_path):
    serialized = json.dumps(inventory, indent=2, sort_keys=True) + "\n"
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output_path.parent,
            prefix=output_path.name + ".",
            suffix=".tmp",
            delete=False,
        ) as staged:
            temp_path = Path(staged.name)
            staged.write(serialized)
            staged.flush()
        os.replace(temp_path, output_path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def build_source_index(source_root, output_path):
    """Write hashes and authority metadata without embedding source contents."""
    source_root = Path(source_root)
    output_path = Path(output_path)
    sources = []

    for relative_path, authority_class in REQUIRED_FILES:
        source_path = source_root / relative_path
        if not source_path.is_file():
            raise FileNotFoundError("Required source missing: " + str(source_path))
        sources.append(_record(source_root, source_path, authority_class))

    for relative_path, authority_class in REQUIRED_GROUPS:
        group_path = source_root / relative_path
        group_files = (
            sorted(path for path in group_path.rglob("*") if path.is_file())
            if group_path.is_dir()
            else []
        )
        if not group_files:
            raise FileNotFoundError("Required source group missing: " + str(group_path))
        sources.extend(
            _record(source_root, path, authority_class) for path in group_files
        )

    inventory = {
        "schema_version": 1,
        "sources": sorted(sources, key=lambda record: record["path"]),
        "rejected_literals": [dict(record) for record in REJECTED_LITERALS],
    }
    _publish_inventory(inventory, output_path)
    return inventory
