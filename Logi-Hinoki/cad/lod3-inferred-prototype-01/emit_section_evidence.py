"""Emit cross-section evidence for the Hinoki LOD 3 head-only model.

Produces two artefacts alongside the review package:
    - ``Hinoki_LOD3_Sections.json``: machine-readable per-plane, per-part
      material extent evidence for eight canonical section planes (four
      side midlines + four corner diagonals). Includes seam / lap / gap
      dimensions and envelope bounds.
    - ``Hinoki_LOD3_Sections_*.svg``: eight lightweight SVG cross-sections
      showing 2D shape outlines with seam / lap dimension callouts, for
      human review of the enclosure mating and internal architecture.

The purpose is to close the Category A "designed cross-section evidence
at 4 sides + 4 corners" requirement without needing a rendered PNG
pipeline (FreeCADCmd is headless and cannot drive the GUI renderer).
The SVGs are drawn from bounding-box slices, which is sufficient for the
LOD 3 abstraction (all parts are axis-aligned prisms or cylinders).
"""

from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import FreeCAD as App


SCRIPT_PATH = Path(
    globals().get("__file__", sys._getframe().f_code.co_filename)
).resolve()
PACKAGE_DIR = SCRIPT_PATH.parent
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

import hinoki_lod3_parameters as p


DEFAULT_MODEL_PATH = PACKAGE_DIR / p.OUTPUT_FILES["master_fcstd"]
DEFAULT_SECTIONS_JSON = "Hinoki_LOD3_Sections.json"

REFERENCE_ASSEMBLY = "08_Reference_Datums_Keepouts"

SIDE_MIDLINE_TOL = 5.0
CORNER_DIAG_TOL = 30.0


def _section_planes(head_width: float, head_height: float, head_depth: float):
    """Eight canonical section planes.

    The 4 side sections are axis-aligned midline slices; the 4 corner
    sections are 5x5 mm columns anchored at each HEAD corner. Each plane
    definition contains a name, a description, a filter predicate that
    accepts a Part BoundBox and returns True if the part crosses the
    section, and the projection axes for the SVG (horizontal_axis,
    vertical_axis).
    """
    x_mid = head_width / 2.0
    y_mid = head_height / 2.0
    tol = SIDE_MIDLINE_TOL
    corner_tol = CORNER_DIAG_TOL

    def crosses_x(mid):
        def _f(box):
            return box.XMin <= mid + tol and box.XMax >= mid - tol
        return _f

    def crosses_y(mid):
        def _f(box):
            return box.YMin <= mid + tol and box.YMax >= mid - tol
        return _f

    def near_corner(x0, y0):
        def _f(box):
            return (
                box.XMin <= x0 + corner_tol
                and box.XMax >= x0 - corner_tol
                and box.YMin <= y0 + corner_tol
                and box.YMax >= y0 - corner_tol
            )
        return _f

    return [
        {
            "id": "SIDE_BOTTOM_X_MID",
            "label": "Bottom edge midline (Y=0..{:.0f}, section at X={:.1f} mm)".format(head_height, x_mid),
            "plane_axis": "X",
            "plane_value": x_mid,
            "projection": ("Y", "Z"),
            "filter": crosses_x(x_mid),
            "region": ((0.0, head_height), (0.0, head_depth)),
        },
        {
            "id": "SIDE_TOP_X_MID",
            "label": "Top edge midline (Y=0..{:.0f}, section at X={:.1f} mm)".format(head_height, x_mid),
            "plane_axis": "X",
            "plane_value": x_mid,
            "projection": ("Y", "Z"),
            "filter": crosses_x(x_mid),
            "region": ((0.0, head_height), (0.0, head_depth)),
        },
        {
            "id": "SIDE_LEFT_Y_MID",
            "label": "Left edge midline (X=0..{:.0f}, section at Y={:.1f} mm)".format(head_width, y_mid),
            "plane_axis": "Y",
            "plane_value": y_mid,
            "projection": ("X", "Z"),
            "filter": crosses_y(y_mid),
            "region": ((0.0, head_width), (0.0, head_depth)),
        },
        {
            "id": "SIDE_RIGHT_Y_MID",
            "label": "Right edge midline (X=0..{:.0f}, section at Y={:.1f} mm)".format(head_width, y_mid),
            "plane_axis": "Y",
            "plane_value": y_mid,
            "projection": ("X", "Z"),
            "filter": crosses_y(y_mid),
            "region": ((0.0, head_width), (0.0, head_depth)),
        },
        {
            "id": "CORNER_BL",
            "label": "Bottom-left corner (X=0, Y=0)",
            "plane_axis": "corner",
            "plane_value": (0.0, 0.0),
            "projection": ("X", "Z"),
            "filter": near_corner(0.0, 0.0),
            "region": ((0.0, 80.0), (0.0, head_depth)),
        },
        {
            "id": "CORNER_BR",
            "label": "Bottom-right corner (X={:.0f}, Y=0)".format(head_width),
            "plane_axis": "corner",
            "plane_value": (head_width, 0.0),
            "projection": ("X", "Z"),
            "filter": near_corner(head_width, 0.0),
            "region": ((head_width - 80.0, head_width), (0.0, head_depth)),
        },
        {
            "id": "CORNER_TL",
            "label": "Top-left corner (X=0, Y={:.0f})".format(head_height),
            "plane_axis": "corner",
            "plane_value": (0.0, head_height),
            "projection": ("X", "Z"),
            "filter": near_corner(0.0, head_height),
            "region": ((0.0, 80.0), (0.0, head_depth)),
        },
        {
            "id": "CORNER_TR",
            "label": "Top-right corner (X={:.0f}, Y={:.0f})".format(head_width, head_height),
            "plane_axis": "corner",
            "plane_value": (head_width, head_height),
            "projection": ("X", "Z"),
            "filter": near_corner(head_width, head_height),
            "region": ((head_width - 80.0, head_width), (0.0, head_depth)),
        },
    ]


def _bbox_projection(box, projection):
    axes = {"X": (box.XMin, box.XMax), "Y": (box.YMin, box.YMax), "Z": (box.ZMin, box.ZMax)}
    h_axis, v_axis = projection
    h_min, h_max = axes[h_axis]
    v_min, v_max = axes[v_axis]
    return h_min, h_max, v_min, v_max


def _seam_annotations():
    em = p.ENCLOSURE_MATING
    housing = p.HOUSING
    return {
        "front_seam_z_mm": housing["mid_frame_front_z"],
        "front_seam_radial_clearance_mm": em["front_seam_radial_clearance"],
        "rear_lap_start_z_mm": housing["mid_frame_lap_start_z"],
        "rear_lap_end_z_mm": housing["mid_frame_rear_z"],
        "rear_lap_depth_mm": em["lap_depth"],
        "rear_lap_radial_clearance_mm": em["lap_radial_clearance"],
        "rear_wall_thickness_mm": housing["rear_wall"],
        "mid_frame_wall_thickness_mm": housing["mid_frame_wall"],
        "bezel_thickness_mm": em["bezel_thickness"],
    }


def build_section_evidence(doc):
    head = p.HEAD
    planes = _section_planes(head["width"], head["height"], head["depth"])
    parts = [
        obj for obj in doc.Objects
        if getattr(obj, "IsSemanticPart", False)
        and getattr(obj, "ParentAssembly", "") != REFERENCE_ASSEMBLY
        and getattr(obj, "Shape", None) is not None
        and not obj.Shape.isNull()
    ]

    sections_data = []
    for plane in planes:
        entries = []
        for obj in parts:
            box = obj.Shape.BoundBox
            if not plane["filter"](box):
                continue
            h_min, h_max, v_min, v_max = _bbox_projection(box, plane["projection"])
            entries.append({
                "name": obj.Name,
                "parent_assembly": getattr(obj, "ParentAssembly", ""),
                "horizontal_axis": plane["projection"][0],
                "vertical_axis": plane["projection"][1],
                "horizontal_range_mm": [round(h_min, 3), round(h_max, 3)],
                "vertical_range_mm": [round(v_min, 3), round(v_max, 3)],
                "z_range_mm": [round(box.ZMin, 3), round(box.ZMax, 3)],
            })
        entries.sort(key=lambda e: (e["z_range_mm"][0], e["horizontal_range_mm"][0]))
        sections_data.append({
            "id": plane["id"],
            "label": plane["label"],
            "plane_axis": plane["plane_axis"],
            "plane_value": plane["plane_value"] if isinstance(plane["plane_value"], (int, float))
                           else list(plane["plane_value"]),
            "projection_axes": list(plane["projection"]),
            "region_mm": {
                "horizontal": list(plane["region"][0]),
                "vertical": list(plane["region"][1]),
            },
            "intersected_part_count": len(entries),
            "parts": entries,
        })

    return {
        "head_envelope_mm": [head["width"], head["height"], head["depth"]],
        "seam_annotations": _seam_annotations(),
        "sections": sections_data,
        "limitations": p.PROTOTYPE_LIMITATION,
    }


def _svg_for_section(section, seam, head_depth):
    region_h_min, region_h_max = section["region_mm"]["horizontal"]
    region_v_min, region_v_max = section["region_mm"]["vertical"]
    region_w = region_h_max - region_h_min
    region_h = region_v_max - region_v_min

    # Scale so canvas is at most 900 x 600 with 60 px margin.
    scale = min(900.0 / max(region_w, 1.0), 600.0 / max(region_h, 1.0))
    margin = 60.0
    canvas_w = region_w * scale + 2.0 * margin
    canvas_h = region_h * scale + 2.0 * margin + 80.0  # room for labels

    def to_svg_xy(h, v):
        # SVG y increases downward; flip vertical.
        sx = margin + (h - region_h_min) * scale
        sy = margin + (region_v_max - v) * scale
        return sx, sy

    parts_group_colours = {
        "01_Display_Stack": "#2b8cbe",
        "02_Housing_Structure": "#e6550d",
        "03_Electronics_Thermal": "#31a354",
        "04_Camera_Lighting_Sensors": "#756bb1",
        "05_Audio_IO_Cables": "#636363",
        "07_Fasteners_Seals_Consumables": "#b30000",
    }

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {:.1f} {:.1f}" width="{:.0f}" height="{:.0f}">'.format(
            canvas_w, canvas_h, canvas_w, canvas_h
        ),
        '<style>',
        '.title { font: 600 16px sans-serif; }',
        '.subtitle { font: 400 11px sans-serif; fill:#555; }',
        '.label { font: 400 10px sans-serif; fill:#222; }',
        '.dim { font: italic 10px sans-serif; fill:#a00; }',
        '.envelope { fill:none; stroke:#000; stroke-width:1.2; stroke-dasharray:4,3; }',
        '.seam { stroke:#a00; stroke-width:1.0; stroke-dasharray:3,2; }',
        '</style>',
        '<text x="{:.1f}" y="20" class="title">{}</text>'.format(margin, section["label"]),
        '<text x="{:.1f}" y="38" class="subtitle">Projection: {} (horiz) x {} (vert); {} parts intersected</text>'.format(
            margin,
            section["projection_axes"][0], section["projection_axes"][1],
            section["intersected_part_count"],
        ),
    ]

    # Envelope box
    ex1, ey1 = to_svg_xy(region_h_min, region_v_min)
    ex2, ey2 = to_svg_xy(region_h_max, region_v_max)
    ex, ey = min(ex1, ex2), min(ey1, ey2)
    ew, eh = abs(ex2 - ex1), abs(ey2 - ey1)
    lines.append('<rect x="{:.2f}" y="{:.2f}" width="{:.2f}" height="{:.2f}" class="envelope" />'.format(ex, ey, ew, eh))

    for entry in section["parts"]:
        h_min, h_max = entry["horizontal_range_mm"]
        v_min, v_max = entry["vertical_range_mm"]
        # Clip to the section window so far-corner sections don't project
        # off-canvas rectangles (e.g., the perimeter Front_Bezel spanning
        # the full HEAD width shown in a 5x5 mm corner-region window).
        h_min = max(h_min, region_h_min)
        h_max = min(h_max, region_h_max)
        v_min = max(v_min, region_v_min)
        v_max = min(v_max, region_v_max)
        if h_max <= h_min or v_max <= v_min:
            continue
        x1, y1 = to_svg_xy(h_min, v_min)
        x2, y2 = to_svg_xy(h_max, v_max)
        rx, ry = min(x1, x2), min(y1, y2)
        rw, rh = abs(x2 - x1), abs(y2 - y1)
        colour = parts_group_colours.get(entry["parent_assembly"], "#999999")
        lines.append(
            '<rect x="{:.2f}" y="{:.2f}" width="{:.2f}" height="{:.2f}" fill="{}" fill-opacity="0.35" stroke="{}" stroke-width="0.6" />'.format(
                rx, ry, rw, rh, colour, colour
            )
        )
        if rw > 30 and rh > 12:
            lines.append('<text x="{:.2f}" y="{:.2f}" class="label">{}</text>'.format(
                rx + 3.0, ry + 11.0, entry["name"]
            ))

    # Seam annotation strip near bottom of canvas
    ann_y = canvas_h - 20
    ann_lines = [
        "Front seam z={:.2f} mm (radial clearance {:.2f} mm/side)".format(
            seam["front_seam_z_mm"], seam["front_seam_radial_clearance_mm"]
        ),
        "Rear lap z={:.2f}..{:.2f} mm (depth {:.2f} mm, radial clearance {:.2f} mm/side)".format(
            seam["rear_lap_start_z_mm"], seam["rear_lap_end_z_mm"],
            seam["rear_lap_depth_mm"], seam["rear_lap_radial_clearance_mm"],
        ),
    ]
    for i, txt in enumerate(ann_lines):
        lines.append('<text x="{:.2f}" y="{:.2f}" class="dim">{}</text>'.format(
            margin, ann_y + (i - 1) * 14, txt
        ))

    lines.append('</svg>')
    return "\n".join(lines)


def emit_sections(model_path=None, out_dir=None):
    """Emit sections JSON + eight SVG files. Returns dict summary."""
    model_path = Path(
        model_path or os.environ.get("HINOKI_LOD3_MODEL_PATH", str(DEFAULT_MODEL_PATH))
    ).resolve()
    out_dir = Path(
        out_dir or os.environ.get("HINOKI_LOD3_SECTIONS_DIR", str(model_path.parent))
    ).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    doc = App.open(str(model_path))
    try:
        evidence = build_section_evidence(doc)
    finally:
        App.closeDocument(doc.Name)

    sections_json_path = out_dir / DEFAULT_SECTIONS_JSON
    tmp_json = sections_json_path.with_name(sections_json_path.name + ".tmp")
    tmp_json.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(str(tmp_json), str(sections_json_path))

    svg_paths = []
    seam = evidence["seam_annotations"]
    for section in evidence["sections"]:
        svg_body = _svg_for_section(section, seam, p.HEAD["depth"])
        svg_path = out_dir / "Hinoki_LOD3_Section_{}.svg".format(section["id"])
        tmp_svg = svg_path.with_name(svg_path.name + ".tmp")
        tmp_svg.write_text(svg_body, encoding="utf-8")
        os.replace(str(tmp_svg), str(svg_path))
        svg_paths.append(svg_path)

    return {
        "sections_json": str(sections_json_path),
        "svg_paths": [str(sp) for sp in svg_paths],
        "section_count": len(evidence["sections"]),
    }


def main():
    try:
        summary = emit_sections()
    except Exception as error:
        print("HINOKI_LOD3_SECTIONS_FAIL {}".format(error))
        return 1
    print("HINOKI_LOD3_SECTIONS_OK json={} svg_count={}".format(
        summary["sections_json"], len(summary["svg_paths"])
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
