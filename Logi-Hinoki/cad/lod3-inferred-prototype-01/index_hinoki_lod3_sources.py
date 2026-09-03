"""Build a metadata-only index of external LOD 3 engineering references."""

import hashlib
import json
from pathlib import Path


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


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _record(source_root, path, authority_class):
    return {
        "path": path.relative_to(source_root).as_posix(),
        "sha256": _sha256(path),
        "byte_size": path.stat().st_size,
        "authority_class": authority_class,
        "external_reference": True,
        "copied_into_repository": False,
    }


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
        "rejected_literals": list(REJECTED_LITERALS),
    }
    output_path.write_text(
        json.dumps(inventory, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return inventory
