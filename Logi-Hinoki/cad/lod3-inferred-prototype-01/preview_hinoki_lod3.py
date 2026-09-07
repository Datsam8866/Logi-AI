"""Generate five phone-review PNGs for the Hinoki LOD 3 head-only model.

Deterministic cameras render the 78-part manifest into:

    - Hinoki_LOD3_Preview_Front.png          orthographic front (from +Z toward -Z)
    - Hinoki_LOD3_Preview_Rear.png           orthographic rear (from -Z toward +Z)
    - Hinoki_LOD3_Preview_Isometric.png      standard 30 deg/30 deg iso
    - Hinoki_LOD3_Preview_Exploded.png       iso with parts offset radially
    - Hinoki_LOD3_Preview_AirflowCutaway.png iso with translucent rear cover +
                                             inlet-to-outlet airflow arrows

Each PNG is 1600 x 1200 with a white background, "shaded-with-edges" draw
style (filled parts with a darker outline), semantic colours per parent
assembly, and a title + legend. The exploded and airflow views also carry
overlay labels; the airflow view is the only view that carries directional
arrows through the rear inlet/outlet vent fields.

Not a photorealistic render. This is a LOD 3 abstraction rendered from
bounding boxes projected onto each view plane; it is intended for phone
review readability, not for tooling, GD&T, or supplier release.
"""

from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


DEFAULT_MANIFEST = "Hinoki_LOD3_Part_Manifest.json"
DEFAULT_VALIDATION = "Hinoki_LOD3_Validation.json"

PREVIEW_FILES = {
    "front": "Hinoki_LOD3_Preview_Front.png",
    "rear": "Hinoki_LOD3_Preview_Rear.png",
    "isometric": "Hinoki_LOD3_Preview_Isometric.png",
    "exploded": "Hinoki_LOD3_Preview_Exploded.png",
    "airflow": "Hinoki_LOD3_Preview_AirflowCutaway.png",
}

CANVAS_SIZE = (1600, 1200)
MARGIN = 60
LEGEND_WIDTH = 320

# Semantic assembly colours (fill, edge) — tuned for phone screens.
ASSEMBLY_COLOURS = {
    "01_Display_Stack": ((70, 130, 180), (35, 65, 110)),
    "02_Housing_Structure": ((230, 120, 40), (140, 65, 15)),
    "03_Electronics_Thermal": ((85, 165, 85), (40, 90, 40)),
    "04_Camera_Lighting_Sensors": ((150, 110, 200), (85, 55, 130)),
    "05_Audio_IO_Cables": ((115, 115, 115), (60, 60, 60)),
    "07_Fasteners_Seals_Consumables": ((180, 30, 30), (110, 15, 15)),
    "08_Reference_Datums_Keepouts": ((200, 200, 200), (120, 120, 120)),
    "06_Stand_Base_Kinematics": ((160, 160, 160), (100, 100, 100)),
}
UNKNOWN_COLOUR = ((150, 150, 150), (80, 80, 80))

# Isometric rotation matrix components (30 deg/30 deg).
ISO_COS = math.cos(math.radians(30.0))
ISO_SIN = math.sin(math.radians(30.0))


def _load_manifest(manifest_path: Path):
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    parts = []
    for row in data.get("parts", []):
        if not row.get("exported", False):
            continue
        bbox = row.get("bbox_mm")
        if bbox is None or len(bbox) != 6:
            continue
        parts.append({
            "name": row["name"],
            "parent": row.get("ParentAssembly", ""),
            "bbox": bbox,
            "volume_mm3": row.get("volume_mm3", 0.0),
        })
    return parts, data


def _colour_for(part):
    return ASSEMBLY_COLOURS.get(part["parent"], UNKNOWN_COLOUR)


def _bbox_center(bbox):
    return (
        (bbox[0] + bbox[3]) / 2.0,
        (bbox[1] + bbox[4]) / 2.0,
        (bbox[2] + bbox[5]) / 2.0,
    )


def _try_font(size):
    for name in (r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _iso_project(x, y, z):
    px = (x - z) * ISO_COS
    py = y + (x + z) * ISO_SIN
    return px, py


def _project_bbox(bbox, mode):
    x0, y0, z0, x1, y1, z1 = bbox
    corners = [
        (x0, y0, z0), (x1, y0, z0), (x0, y1, z0), (x1, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x0, y1, z1), (x1, y1, z1),
    ]
    if mode == "front":
        projected = [(x, y) for x, y, z in corners]
    elif mode == "rear":
        projected = [(-x, y) for x, y, z in corners]
    elif mode in ("isometric", "exploded", "airflow"):
        projected = [_iso_project(x, y, z) for x, y, z in corners]
    else:
        raise ValueError("unknown mode: " + mode)
    return corners, projected


def _polygon_hull(points):
    """Convex hull for a small point set (used to outline projected bbox)."""
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower = []
    for pt in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], pt) <= 0:
            lower.pop()
        lower.append(pt)
    upper = []
    for pt in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], pt) <= 0:
            upper.pop()
        upper.append(pt)
    return lower[:-1] + upper[:-1]


def _compute_view_transform(all_projected, canvas_size, margin, right_pad):
    xs = [p[0] for p in all_projected]
    ys = [p[1] for p in all_projected]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    span_x = max(x_max - x_min, 1.0)
    span_y = max(y_max - y_min, 1.0)
    canvas_w, canvas_h = canvas_size
    avail_w = canvas_w - 2 * margin - right_pad
    avail_h = canvas_h - 2 * margin - 100
    scale = min(avail_w / span_x, avail_h / span_y) * 0.92
    origin_x = margin + (avail_w - span_x * scale) / 2.0 - x_min * scale
    origin_y = margin + 60 + (avail_h - span_y * scale) / 2.0 + y_max * scale
    return scale, origin_x, origin_y


def _to_canvas(pt, scale, origin_x, origin_y):
    x, y = pt
    return (origin_x + x * scale, origin_y - y * scale)


def _draw_title_and_legend(draw, canvas_size, title, subtitle):
    canvas_w, canvas_h = canvas_size
    font_title = _try_font(32)
    font_sub = _try_font(18)
    font_legend = _try_font(16)

    draw.text((MARGIN, 20), title, fill=(20, 20, 20), font=font_title)
    draw.text((MARGIN, 62), subtitle, fill=(90, 90, 90), font=font_sub)

    # Legend on the right.
    legend_x = canvas_w - LEGEND_WIDTH + 20
    legend_y = MARGIN + 40
    draw.text((legend_x, legend_y - 30), "Legend (parent assembly)",
              fill=(50, 50, 50), font=font_legend)
    for i, (assembly, (fill, edge)) in enumerate(ASSEMBLY_COLOURS.items()):
        row_y = legend_y + i * 28
        draw.rectangle([legend_x, row_y, legend_x + 24, row_y + 20],
                       fill=fill, outline=edge, width=1)
        draw.text((legend_x + 32, row_y + 2),
                  assembly.replace("_", " "), fill=(40, 40, 40), font=font_legend)

    footer = _try_font(14)
    draw.text((MARGIN, canvas_h - 30),
              "LOD 3 inferred engineering prototype; not a manufacturing release.",
              fill=(140, 20, 20), font=footer)


def _render_view(parts, mode, out_path, head_envelope):
    canvas_w, canvas_h = CANVAS_SIZE
    img = Image.new("RGB", CANVAS_SIZE, "white")
    draw = ImageDraw.Draw(img, "RGBA")

    projected_all = []
    per_part = []
    head_cx, head_cy, head_cz = (
        head_envelope[0] / 2.0,
        head_envelope[1] / 2.0,
        head_envelope[2] / 2.0,
    )
    explosion_gain = 0.6

    for part in parts:
        bbox = part["bbox"]
        if mode == "exploded":
            cx, cy, cz = _bbox_center(bbox)
            dx = cx - head_cx
            dy = cy - head_cy
            dz = cz - head_cz
            norm = max(math.sqrt(dx * dx + dy * dy + dz * dz), 1.0)
            offset_scale = explosion_gain * (norm + 40.0) / norm
            ox = dx * offset_scale - dx
            oy = dy * offset_scale - dy
            oz = dz * offset_scale - dz
            bbox = [
                bbox[0] + ox, bbox[1] + oy, bbox[2] + oz,
                bbox[3] + ox, bbox[4] + oy, bbox[5] + oz,
            ]
        corners_world, projected = _project_bbox(bbox, mode)
        projected_all.extend(projected)
        per_part.append((part, corners_world, projected, bbox))

    # Include HEAD envelope so scaling is stable across views.
    env_bbox = [0.0, 0.0, 0.0, head_envelope[0], head_envelope[1], head_envelope[2]]
    _, env_projected = _project_bbox(env_bbox, mode)
    projected_all.extend(env_projected)

    scale, origin_x, origin_y = _compute_view_transform(
        projected_all, CANVAS_SIZE, MARGIN, LEGEND_WIDTH
    )

    # Painter's algorithm depth key.
    def depth_key(item):
        _, corners_world, _, _ = item
        if mode == "front":
            # Objects with larger z_min are behind (further from viewer at +Z).
            return -min(c[2] for c in corners_world)
        if mode == "rear":
            return min(c[2] for c in corners_world)
        # iso variants: sort by (x + y + z) so back-lower-left draws first.
        return sum(sum(c) for c in corners_world) / len(corners_world)

    per_part.sort(key=depth_key)

    # Envelope outline
    env_hull = _polygon_hull(env_projected)
    env_hull_canvas = [_to_canvas(pt, scale, origin_x, origin_y) for pt in env_hull]
    draw.polygon(env_hull_canvas, outline=(0, 0, 0), fill=None)

    airflow_hidden_parts = {"Rear_Enclosure"} if mode == "airflow" else set()

    for part, corners_world, projected, bbox in per_part:
        fill, edge = _colour_for(part)
        alpha = 235
        if mode in ("airflow",) and part["name"] == "Rear_Enclosure":
            # Translucent rear housing so internals are visible.
            alpha = 60
        elif mode == "airflow" and part["parent"] == "02_Housing_Structure":
            alpha = 140
        fill_rgba = (fill[0], fill[1], fill[2], alpha)
        hull = _polygon_hull(projected)
        canvas_pts = [_to_canvas(pt, scale, origin_x, origin_y) for pt in hull]
        if len(canvas_pts) < 3:
            continue
        draw.polygon(canvas_pts, fill=fill_rgba, outline=edge)

    # Airflow arrows for the airflow view only.
    if mode == "airflow":
        _draw_airflow_arrows(draw, scale, origin_x, origin_y, head_envelope, mode)

    # Exploded labels: annotate a few key parts.
    if mode == "exploded":
        _draw_exploded_labels(draw, per_part, scale, origin_x, origin_y)

    title_map = {
        "front": ("Hinoki LOD 3 — Front view (from +Z)",
                  "Orthographic projection onto XY plane; 78 physical semantic parts"),
        "rear": ("Hinoki LOD 3 — Rear view (from -Z)",
                 "Orthographic projection onto XY plane (mirrored); rear I/O cover + vent slots visible"),
        "isometric": ("Hinoki LOD 3 — Isometric view (30 deg / 30 deg)",
                      "Standard iso projection; front bezel through rear cover with lap seam at z=22..25 mm"),
        "exploded": ("Hinoki LOD 3 — Exploded view",
                     "Iso projection with parts offset radially from head centre (371, 246, 31 mm)"),
        "airflow": ("Hinoki LOD 3 — Airflow cutaway",
                    "Iso projection with translucent rear housing; arrows show inlet (bottom) -> outlet (top)"),
    }
    title, subtitle = title_map[mode]
    _draw_title_and_legend(draw, CANVAS_SIZE, title, subtitle)

    # Atomic write via temp file rename.
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_name(out_path.name + ".tmp")
    img.save(str(tmp), "PNG", optimize=True)
    if out_path.exists():
        out_path.unlink()
    os.replace(str(tmp), str(out_path))
    return out_path


def _draw_airflow_arrows(draw, scale, origin_x, origin_y, head_envelope, mode):
    head_w, head_h, head_d = head_envelope
    # Inlet at lower rear at y=30..55, outlet at upper rear at y=437..462.
    inlet_centres = [(head_w * 0.35, 42.5, head_d - 4.0),
                     (head_w * 0.65, 42.5, head_d - 4.0)]
    outlet_centres = [(head_w * 0.35, head_h - 42.5, head_d - 4.0),
                      (head_w * 0.65, head_h - 42.5, head_d - 4.0)]
    arrow_font = _try_font(16)
    for start, end in zip(inlet_centres, outlet_centres):
        sx, sy = _to_canvas(_iso_project(*start), scale, origin_x, origin_y)
        ex, ey = _to_canvas(_iso_project(*end), scale, origin_x, origin_y)
        draw.line([(sx, sy), (ex, ey)], fill=(0, 90, 180), width=4)
        _arrow_head(draw, sx, sy, ex, ey, (0, 90, 180))
    # Legend text near lower left of drawing area.
    label_x = origin_x + 40
    label_y = origin_y - 30
    draw.text((label_x, label_y - 20),
              "Blue arrow = natural convection inlet -> outlet",
              fill=(0, 90, 180), font=arrow_font)


def _arrow_head(draw, sx, sy, ex, ey, colour):
    angle = math.atan2(ey - sy, ex - sx)
    length = 14
    left = (ex - length * math.cos(angle - math.radians(25)),
            ey - length * math.sin(angle - math.radians(25)))
    right = (ex - length * math.cos(angle + math.radians(25)),
             ey - length * math.sin(angle + math.radians(25)))
    draw.polygon([(ex, ey), left, right], fill=colour)


def _draw_exploded_labels(draw, per_part, scale, origin_x, origin_y):
    font = _try_font(12)
    labelled = 0
    important = {
        "Front_Bezel", "Cover_Glass", "LCD_Cell", "LED_Bar_Bottom",
        "Panel_Backplate", "Metal_Mid_Frame", "Rear_Enclosure",
        "Rear_IO_Cover", "Carrier_PCB", "Compute_SOM_PCB",
        "Heat_QC7790", "Copper_Spreader", "Aluminum_Interface",
        "Rear_Hatch_TIM", "Primary_Boss_01", "VESA_Boss_01",
    }
    for part, _corners_world, projected, _bbox in per_part:
        if part["name"] not in important:
            continue
        pt = projected[7]  # top-right-far corner
        cx, cy = _to_canvas(pt, scale, origin_x, origin_y)
        draw.text((cx + 4, cy - 12), part["name"], fill=(30, 30, 30), font=font)
        labelled += 1
        if labelled >= 16:
            break


def emit_previews(manifest_path=None, out_dir=None):
    manifest_path = Path(
        manifest_path
        or os.environ.get(
            "HINOKI_LOD3_MANIFEST_PATH",
            str(Path(__file__).resolve().parent / DEFAULT_MANIFEST),
        )
    ).resolve()
    out_dir = Path(
        out_dir
        or os.environ.get("HINOKI_LOD3_PREVIEW_DIR", str(manifest_path.parent))
    ).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    parts, manifest = _load_manifest(manifest_path)
    if not parts:
        raise RuntimeError("no exported parts with bbox_mm found in manifest")

    validation_path = manifest_path.with_name(DEFAULT_VALIDATION)
    head_envelope = [742.0, 492.0, 62.0]
    if validation_path.exists():
        try:
            v = json.loads(validation_path.read_text(encoding="utf-8"))
            envelope = v.get("head_envelope", {}).get("expected_mm")
            if envelope and len(envelope) == 3:
                head_envelope = envelope
        except (ValueError, OSError):
            pass

    written = []
    for mode, filename in PREVIEW_FILES.items():
        out_path = out_dir / filename
        _render_view(parts, mode, out_path, head_envelope)
        written.append(out_path)

    return {"preview_paths": [str(p) for p in written]}


def main():
    try:
        summary = emit_previews()
    except Exception as error:
        print("HINOKI_LOD3_PREVIEW_FAIL {}".format(error))
        return 1
    print("HINOKI_LOD3_PREVIEW_OK count={}".format(len(summary["preview_paths"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
