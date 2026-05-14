# -*- coding: utf-8-sig -*-
"""Generate reports/dashboard.html from vc_benchmark.db."""
import sqlite3, json, os, html as _html
from datetime import datetime
from urllib.parse import urlparse

BASE = os.path.dirname(os.path.abspath(__file__))

SPEC_KEYS = [
    'camera_system','audio_system','microphone_presence','video_inputs','video_outputs',
    'wireless_sharing','supported_applications','supported_os','power_consumption',
    'mounting_options','environmental_specs','teardown_thermal','teardown_thermal_design',
    'teardown_key_ics','teardown_build_quality',
]

DRAWER_SPEC_FIELDS = [
    ('dimensions',             '尺寸'),
    ('weight',                 '重量'),
    ('camera_system',          'Camera System'),
    ('audio_system',           'Audio System'),
    ('microphone_presence',    'Microphone'),
    ('video_inputs',           'Video Inputs'),
    ('video_outputs',          'Video Outputs'),
    ('supported_applications', 'Supported Apps'),
    ('wireless_sharing',       'Wireless'),
    ('supported_os',           'Supported OS'),
    ('environmental_specs',    'Environmental'),
    ('power_supply',           'Power Supply'),
    ('power_consumption',      'Power Consumption'),
    ('mounting_options',       'Mounting'),
    ('special_features',       'Special Features'),
]

DRAWER_TEARDOWN_FIELDS = [
    ('teardown_pcb',            'PCB / SoC'),
    ('teardown_thermal',        'Thermal Solution'),
    ('teardown_thermal_design', 'Thermal Design'),
    ('teardown_key_ics',        'Key ICs'),
    ('teardown_build_quality',  'Build Quality'),
]

MATRIX_FIELDS = [
    ('camera_system',          'Camera System'),
    ('audio_system',           'Audio System'),
    ('microphone_presence',    'Microphone'),
    ('video_inputs',           'Video Inputs'),
    ('video_outputs',          'Video Outputs'),
    ('wireless_sharing',       'Wireless'),
    ('supported_applications', 'Applications'),
    ('supported_os',           'Supported OS'),
    ('power_consumption',      'Power'),
    ('mounting_options',       'Mounting'),
    ('environmental_specs',    'Environmental'),
    ('teardown_thermal',       'Thermal (Teardown)'),
    ('teardown_build_quality', 'Build Quality'),
]

CAT_COLORS = {
    'PTZ Camera':      {'bg': '#E6FAF8', 'text': '#3730a3', 'border': '#99E8DF'},
    'Room Bar':        {'bg': '#eff6ff', 'text': '#1d4ed8', 'border': '#bfdbfe'},
    'Table Camera':    {'bg': '#f0fdfa', 'text': '#0f766e', 'border': '#99f6e4'},
    'Mic':             {'bg': '#f5f3ff', 'text': '#6d28d9', 'border': '#ddd6fe'},
    'Speaker':         {'bg': '#fffbeb', 'text': '#b45309', 'border': '#fde68a'},
    'AIO Board':       {'bg': '#fff7ed', 'text': '#c2410c', 'border': '#fed7aa'},
    'AIO System':      {'bg': '#fff1f2', 'text': '#be123c', 'border': '#fecdd3'},
    'Accessory':       {'bg': '#fafaf9', 'text': '#57534e', 'border': '#d6d3d1'},
}
DEFAULT_CAT_COLOR = {'bg': '#f1f5f9', 'text': '#334155', 'border': '#cbd5e1'}

_NA_VALS = {'', 'N/A', 'null', '—', '-', 'N/A (no public teardown found)'}


def e(s):
    return _html.escape(str(s or ''), quote=True)


def is_url(value):
    parsed = urlparse(str(value or '').strip())
    return parsed.scheme in ('http', 'https') and bool(parsed.netloc)


def split_sources(value):
    return [p.strip() for p in str(value or '').split('|') if p.strip()]


def source_link_label(url):
    return 'FCC↗' if 'fccid.io' in urlparse(str(url or '')).netloc.lower() else 'Teardown↗'


def cat_pill(cat):
    c = CAT_COLORS.get(cat, DEFAULT_CAT_COLOR)
    st = (f'background:{c["bg"]};color:{c["text"]};border:1px solid #CCCCCC;'
          'display:inline-block;padding:2px 10px;border-radius:9999px;'
          'font-size:0.82rem;font-weight:700;letter-spacing:0.04em;white-space:nowrap')
    return f'<span style="{st}">{e(cat)}</span>'


def soc_status(d):
    v = str(d.get('teardown_pcb') or '').strip()
    if v and v not in _NA_VALS and len(v) > 3:
        return '<span class="soc-confirmed">✓</span>'
    return '<span class="soc-na">—</span>'


def soc_value(d):
    v = str(d.get('teardown_pcb') or '').strip()
    if v and v not in _NA_VALS and len(v) > 3:
        return (v[:45] + '…') if len(v) > 45 else v
    return ''


def completeness(d):
    filled = sum(1 for k in SPEC_KEYS
                 if d.get(k) and str(d[k]).strip() not in ('', 'N/A', 'null') and len(str(d[k])) > 1)
    return round(filled / len(SPEC_KEYS) * 100)


def load_devices():
    conn = sqlite3.connect(os.path.join(BASE, 'vc_benchmark.db'))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('SELECT * FROM devices ORDER BY id ASC')
    devices = []
    for row in cur.fetchall():
        d = dict(row)
        try:
            d['dynamic_columns'] = json.loads(d['dynamic_columns'] or '{}')
        except Exception:
            d['dynamic_columns'] = {}
        devices.append(d)
    conn.close()
    return devices


def _val(v):
    sv = str(v or '').strip()
    if not sv or sv in _NA_VALS:
        return '<span class="muted">N/A</span>'
    return e(sv)


def _kv_row(label, val_html):
    return (f'<tr><td class="kv-label">{label}</td>'
            f'<td class="kv-val">{val_html}</td></tr>')


def build_drawer_panel(d):
    pct = completeness(d)
    bar_color = '#16a34a' if pct >= 80 else '#d97706' if pct >= 50 else '#dc2626'

    link_parts = []
    if is_url(d.get('datasheet_url')):
        link_parts.append(
            f'<a href="{e(d["datasheet_url"])}" target="_blank" class="dl-link indigo-link">Datasheet↗</a>')
    td_urls = [s for s in split_sources(d.get('teardown_source')) if is_url(s)]
    if td_urls:
        link_parts.append(
            f'<a href="{e(td_urls[0])}" target="_blank" class="dl-link amber-link">{source_link_label(td_urls[0])}</a>')
    links_html = ' '.join(link_parts) if link_parts else '<span class="muted">連結不可用</span>'

    spec_rows = ''.join(_kv_row(label, _val(d.get(key))) for key, label in DRAWER_SPEC_FIELDS)
    dc = d.get('dynamic_columns') or {}
    for k, v in dc.items():
        spec_rows += _kv_row(e(str(k)), e(str(v)))

    td_rows = ''.join(_kv_row(label, _val(d.get(key))) for key, label in DRAWER_TEARDOWN_FIELDS)
    src_parts = []
    for source in split_sources(d.get('teardown_source')):
        if is_url(source):
            src_parts.append(f'<a href="{e(source)}" target="_blank" class="amber-link-sm">{source_link_label(source)}</a>')
        elif source and not source.upper().startswith('N/A'):
            src_parts.append(f'<span class="muted">{e(source)}</span>')
    if src_parts:
        td_rows += _kv_row('Source', ' '.join(src_parts))

    notes_html = ''
    if d.get('notes'):
        notes_html = (
            '<div class="drawer-section">'
            '<div class="section-hd">備註</div>'
            f'<div class="notes-box">{e(d["notes"])}</div>'
            '</div>'
        )

    return (
        f'<div class="drawer-panel" data-id="{d["id"]}">'
        '<div class="drawer-hd">'
        '<div class="drawer-title-col">'
        f'<div class="drawer-name">{e(d["product_name"])}</div>'
        '<div class="drawer-meta">'
        f'{cat_pill(d["category"])}'
        f'<span class="date-chip">{e(d.get("date_added") or "")}</span>'
        '</div></div>'
        '<button onclick="closeDrawer()" class="close-btn" title="Close">✕</button>'
        '</div>'
        '<div class="drawer-links-row">'
        f'<div>{links_html}</div>'
        '<div class="comp-row">'
        '<span class="muted">完整度</span>'
        '<div class="mini-bar">'
        f'<div class="mini-bar-fill" style="width:{pct}%;background:{bar_color}"></div>'
        '</div>'
        f'<span class="muted">{pct}%</span>'
        '</div></div>'
        '<details class="drawer-details" open>'
        '<summary class="drawer-summary"><span class="arrow">▸</span> 規格詳情</summary>'
        f'<div class="kv-section"><table class="kv-table">{spec_rows}</table></div>'
        '</details>'
        '<details class="drawer-details" open>'
        '<summary class="drawer-summary"><span class="arrow">▸</span> 拆解資訊</summary>'
        f'<div class="kv-section"><table class="kv-table">{td_rows}</table></div>'
        '</details>'
        f'{notes_html}'
        '</div>'
    )


def _short(val, maxlen):
    v = str(val or '').strip()
    if not v or v in _NA_VALS:
        return ''
    return (v[:maxlen] + '…') if len(v) > maxlen else v



def build_row_all(d):
    """Plain row for All view — no drawer on click."""
    return (
        f'<div class="pr-all searchable-row" data-name="{e(d["product_name"])}">'
        f'<span class="pr-name">{e(d["product_name"])}</span>'
        f'{soc_status(d)}'
        f'</div>'
    )


def build_row_cat(d):
    """Expanded row for Category view — opens Drawer on click."""
    soc  = soc_value(d)
    power = _short(d.get('power_consumption'), 35)

    meta_parts = []
    if soc:
        meta_parts.append(
            f'<span class="cpr-field"><span class="cpr-label">SoC</span>'
            f'<span class="cpr-v">{e(soc)}</span></span>')
    if power:
        meta_parts.append(
            f'<span class="cpr-field"><span class="cpr-label">Power</span>'
            f'<span class="cpr-v">{e(power)}</span></span>')
    meta = ''.join(meta_parts) if meta_parts else '<span class="soc-na">—</span>'

    return (
        f'<div class="cpr searchable-row" data-name="{e(d["product_name"])}" onclick="openDrawer({d["id"]})">'
        f'<div class="cpr-name">{e(d["product_name"])}</div>'
        f'<div class="cpr-meta">{meta}</div>'
        f'</div>'
    )


def build_all_panel(devices, cats):
    html = ''
    for cat in cats:
        c = CAT_COLORS.get(cat, DEFAULT_CAT_COLOR)
        cat_devs = [d for d in devices if d['category'] == cat]
        rows = ''.join(build_row_all(d) for d in cat_devs)
        html += (
            f'<div class="cat-block" style="border-color:{c["border"]}">'
            f'<div class="cat-block-hd" data-cat="{e(cat)}" onclick="showView(this.dataset.cat)"'
            f' style="background:{c["bg"]};border-color:{c["border"]}">'
            f'{cat_pill(cat)}'
            f'<span class="cat-count" style="color:{c["text"]};opacity:0.6">{len(cat_devs)} 筆</span>'
            f'<span class="cat-arrow" style="color:{c["text"]};opacity:0.5">→</span>'
            f'</div>'
            f'<div class="product-list">{rows}</div>'
            f'</div>'
        )
    return html


def build_html(devices):
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    cats = list(dict.fromkeys(d['category'] for d in devices if d['category']))
    count = len(devices)
    cat_count = len(cats)
    brand_count = len(set(d['product_name'].split()[0] for d in devices if d.get('product_name')))

    kpi_html = (
        f'<div class="kpi-chip"><span class="kpi-val">{count}</span>'
        f'<span class="kpi-label">Competitors</span></div>'
        f'<div class="kpi-chip"><span class="kpi-val">{cat_count}</span>'
        f'<span class="kpi-label">Categories</span></div>'
        f'<div class="kpi-chip"><span class="kpi-val">{brand_count}</span>'
        f'<span class="kpi-label">Brands</span></div>'
    )

    all_panel_html = build_all_panel(devices, cats)

    cat_panels_html = ''
    for cat in cats:
        cat_devs = [d for d in devices if d['category'] == cat]
        rows = ''.join(build_row_cat(d) for d in cat_devs)
        cat_panels_html += (
            f'<div class="panel-cat" data-cat="{e(cat)}" style="display:none">'
            f'<div class="cat-panel-hd">'
            f'<button class="back-btn" onclick="showView(\'all\')">← 全部</button>'
            f'{cat_pill(cat)}'
            f'<span class="cat-count">{len(cat_devs)} 筆</span>'
            f'</div>'
            f'<div class="cat-product-list">{rows}</div>'
            f'</div>'
        )

    drawer_panels = ''.join(build_drawer_panel(d) for d in devices)

    data_json = json.dumps(
        [{k: (list(d['dynamic_columns'].items()) if k == 'dynamic_columns' else v)
          for k, v in d.items()} for d in devices],
        ensure_ascii=False
    ).replace('</', '<\\/')
    matrix_json = json.dumps(
        [{'key': k, 'label': l} for k, l in MATRIX_FIELDS],
        ensure_ascii=False
    ).replace('</', '<\\/')

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VC Competitor Benchmarker</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Poppins','Segoe UI',system-ui,sans-serif;background:#fafaf9;color:#1c1917;line-height:1.5}}
#breakthrough-bar{{height:4px;background:#0DFDCF;width:100%}}
/* ── Sticky top block ── */
#sticky-top{{position:sticky;top:0;z-index:30;background:#fff}}
#site-header{{
  border-bottom:1px solid #e7e5e4;padding:12px 24px;
  display:flex;align-items:center;gap:16px;
}}
.header-brand .title{{font-size:1.35rem;font-weight:800;color:#1c1917;letter-spacing:-0.01em}}
#search-box{{
  flex:1;max-width:300px;border:1px solid #e7e5e4;border-radius:8px;
  padding:7px 12px;font-size:1rem;color:#1c1917;background:#fafaf9;outline:none;
}}
#search-box:focus{{border-color:#00978A;background:#fff}}
.header-right{{display:flex;align-items:center;gap:10px;margin-left:auto;flex-shrink:0}}
#gen-time{{font-size:0.85rem;color:#a8a29e}}
#theme-btn{{
  background:none;border:1px solid #e7e5e4;border-radius:8px;
  padding:6px 10px;font-size:1rem;cursor:pointer;color:#78716c;
  transition:background .15s;line-height:1;
}}
#theme-btn:hover{{background:#f5f5f4}}
#update-btn{{
  display:flex;align-items:center;gap:6px;background:#00978A;color:#fff;
  border:none;border-radius:8px;padding:7px 14px;font-size:0.92rem;font-weight:600;
  cursor:pointer;transition:background .15s;
}}
#update-btn:hover{{background:#007A6E}}
#update-btn:disabled{{opacity:.5;cursor:default}}
#kpi-bar{{
  border-bottom:1px solid #e7e5e4;padding:14px 24px;
  display:flex;align-items:center;gap:16px;
}}
.kpi-chip{{
  display:flex;flex-direction:column;align-items:center;gap:2px;background:#fafaf9;
  border:1px solid #e7e5e4;border-radius:12px;padding:14px 32px;
}}
.kpi-val{{font-size:2.2rem;font-weight:800;color:#00978A;line-height:1}}
.kpi-label{{font-size:0.88rem;color:#a8a29e;font-weight:500;margin-top:4px}}
/* ── Main content ── */
main{{padding:24px 24px 100px}}
/* ── All view: 3-column grid ── */
#panel-all{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;align-items:start}}
/* ── Category blocks (All view) ── */
.cat-block{{
  background:#fff;border:1px solid #e7e5e4;border-radius:12px;overflow:hidden;
}}
.cat-block-hd{{
  display:flex;align-items:center;gap:10px;padding:12px 16px;
  cursor:pointer;border-bottom:1px solid #e7e5e4;transition:background .1s;
}}
.cat-block-hd:hover{{background:#f5f5f4}}
.cat-count{{font-size:0.88rem;color:#a8a29e}}
.cat-arrow{{margin-left:auto;color:#a8a29e;font-size:0.85rem;transition:color .1s}}
.cat-block-hd:hover .cat-arrow{{color:#00978A}}
/* ── All-view plain rows (no drawer) ── */
.pr-all{{
  display:flex;align-items:center;justify-content:space-between;
  padding:8px 16px;border-bottom:1px solid #f5f5f4;
}}
.pr-all:last-child{{border-bottom:none}}
.pr-name{{font-size:1rem;color:#1c1917;font-weight:500}}
/* ── Category panel ── */
.cat-panel-hd{{display:flex;align-items:center;gap:12px;padding:4px 0 16px}}
.back-btn{{
  background:none;border:1px solid #e7e5e4;border-radius:8px;
  padding:5px 12px;font-size:0.92rem;color:#78716c;cursor:pointer;
  transition:background .1s;white-space:nowrap;
}}
.back-btn:hover{{background:#f5f5f4;color:#1c1917}}
/* ── Category-view expanded rows ── */
.cat-product-list{{
  background:#fff;border:1px solid #e7e5e4;border-radius:12px;overflow:hidden;
}}
.cpr{{
  padding:11px 20px;cursor:pointer;
  border-bottom:1px solid #f5f5f4;transition:background .1s;
}}
.cpr:last-child{{border-bottom:none}}
.cpr:hover{{background:#eff6ff}}
.cpr-name{{font-size:1rem;font-weight:600;color:#1c1917;margin-bottom:5px}}
.cpr-meta{{display:flex;flex-wrap:wrap;gap:6px 18px}}
.cpr-field{{display:flex;align-items:center;gap:4px}}
.cpr-label{{font-size:0.8rem;color:#a8a29e;font-weight:500;white-space:nowrap}}
.cpr-v{{font-size:0.88rem;color:#57534e}}
.soc-confirmed{{color:#16a34a;font-weight:600;font-size:0.88rem}}
.soc-na{{color:#a8a29e;font-size:0.88rem}}
.muted{{color:#a8a29e;font-size:0.88rem}}
/* ── Drawer ── */
#drawer{{
  position:fixed;right:0;top:0;height:100%;
  width:44vw;min-width:420px;max-width:680px;
  background:#fff;border-left:1px solid #e7e5e4;
  box-shadow:-8px 0 32px rgba(0,0,0,.08);
  transform:translateX(100%);
  transition:transform .25s cubic-bezier(.4,0,.2,1);
  z-index:50;overflow-y:auto;
}}
#drawer.open{{transform:translateX(0)}}
#drawer-overlay{{
  display:none;position:fixed;inset:0;background:rgba(28,25,23,.15);z-index:40;
}}
.drawer-hd{{
  display:flex;align-items:flex-start;justify-content:space-between;gap:12px;
  padding:20px 24px 16px;border-bottom:1px solid #e7e5e4;
  position:sticky;top:0;background:#fff;z-index:5;
}}
.drawer-title-col{{min-width:0}}
.drawer-name{{font-size:1.25rem;font-weight:700;color:#1c1917;line-height:1.3;margin-bottom:6px}}
.drawer-meta{{display:flex;align-items:center;gap:8px;flex-wrap:wrap}}
.date-chip{{color:#a8a29e;font-size:0.85rem}}
.close-btn{{
  background:none;border:1px solid #e7e5e4;cursor:pointer;
  font-size:1rem;color:#78716c;padding:4px 10px;border-radius:6px;flex-shrink:0;
  transition:background .1s;
}}
.close-btn:hover{{background:#f5f5f4}}
.drawer-links-row{{
  display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;
  padding:12px 24px;border-bottom:1px solid #e7e5e4;
}}
.comp-row{{display:flex;align-items:center;gap:6px}}
.mini-bar{{background:#e7e5e4;border-radius:9999px;height:5px;width:72px;overflow:hidden}}
.mini-bar-fill{{height:5px;border-radius:9999px}}
.dl-link{{text-decoration:none;font-size:0.9rem;font-weight:600;border-radius:6px;padding:4px 10px}}
.indigo-link{{background:#E6FAF8;color:#00978A;border:1px solid #99E8DF}}
.indigo-link:hover{{background:#CCF5F1}}
.amber-link{{background:#fffbeb;color:#b45309;border:1px solid #fde68a}}
.amber-link:hover{{background:#fef3c7}}
.amber-link-sm{{color:#b45309;font-size:0.88rem}}
.drawer-details{{border-bottom:1px solid #e7e5e4}}
.drawer-summary{{
  display:flex;align-items:center;gap:6px;padding:12px 24px;cursor:pointer;
  font-size:0.95rem;font-weight:600;color:#00978A;list-style:none;
}}
.drawer-summary::-webkit-details-marker{{display:none}}
.drawer-summary .arrow{{transition:transform .2s}}
details[open] .drawer-summary .arrow{{transform:rotate(90deg)}}
.kv-section{{padding:4px 24px 14px}}
.kv-table{{width:100%;border-collapse:collapse}}
.kv-label{{color:#78716c;font-size:0.85rem;padding:5px 14px 5px 0;white-space:nowrap;vertical-align:top;width:140px}}
.kv-val{{font-size:0.95rem;color:#1c1917;padding:5px 0;vertical-align:top}}
.drawer-section{{padding:14px 24px}}
.section-hd{{font-size:0.95rem;font-weight:600;color:#00978A;margin-bottom:8px}}
.notes-box{{
  background:#fafaf9;border:1px solid #e7e5e4;border-radius:8px;
  padding:10px 14px;font-size:0.92rem;color:#78716c;line-height:1.6;
}}
/* ── Dark mode ── */
body.dark{{background:#1B1B1B;color:#fafaf9}}
body.dark #breakthrough-bar{{background:#0DFDCF}}
body.dark #sticky-top{{background:#242424}}
body.dark #site-header,body.dark #kpi-bar{{background:#242424;border-color:#333333}}
body.dark .header-brand .title{{color:#fafaf9}}
body.dark #search-box{{background:#1B1B1B;border-color:#333333;color:#fafaf9}}
body.dark #search-box:focus{{border-color:#0DFDCF;background:#292524}}
body.dark #theme-btn{{border-color:#333333;color:#a8a29e}}
body.dark #theme-btn:hover{{background:#333333}}
body.dark .kpi-chip{{background:#1B1B1B;border-color:#333333}}
body.dark .kpi-val{{color:#0DFDCF}}
body.dark .kpi-val{{color:#fafaf9}}
body.dark .cat-block{{background:#242424;border-color:#333333}}
body.dark .cat-block-hd{{border-color:#333333}}
body.dark .cat-block-hd:hover{{background:#1B1B1B}}
body.dark .pr-all{{border-color:#333333}}
body.dark .pr-name{{color:#fafaf9}}
body.dark .cat-product-list{{background:#242424;border-color:#333333}}
body.dark .cpr{{border-color:#333333}}
body.dark .cpr:hover{{background:#0A2A27}}
body.dark .cpr-name{{color:#fafaf9}}
body.dark .cpr-v{{color:#a8a29e}}
body.dark .back-btn{{border-color:#333333;color:#a8a29e}}
body.dark .back-btn:hover{{background:#333333;color:#fafaf9}}
body.dark #drawer{{background:#242424;border-color:#333333}}
body.dark .drawer-hd{{background:#242424;border-color:#333333}}
body.dark .drawer-name{{color:#fafaf9}}
body.dark .drawer-links-row{{border-color:#333333}}
body.dark .close-btn{{border-color:#333333;color:#a8a29e}}
body.dark .close-btn:hover{{background:#333333}}
body.dark .drawer-details{{border-color:#333333}}
body.dark .kv-label{{color:#a8a29e}}
body.dark .kv-val{{color:#fafaf9}}
body.dark .drawer-section{{color:#fafaf9}}
body.dark .notes-box{{background:#1B1B1B;border-color:#333333;color:#a8a29e}}
body.dark #drawer-overlay{{background:rgba(0,0,0,.4)}}
body.dark .muted{{color:#78716c}}
#drawer-panels{{display:none}}
</style>
</head>
<body>

<div id="sticky-top">
  <div id="breakthrough-bar"></div>
  <header id="site-header">
    <div class="header-brand">
      <div class="title">Logitech VC Competitor Benchmarker</div>
    </div>
    <input id="search-box" type="text" placeholder="搜尋產品名稱…" oninput="applySearch()">
    <div class="header-right">
      <span id="gen-time">Generated {now}</span>
      <button id="theme-btn" onclick="toggleTheme()" title="切換深色/淺色模式">&#9790;</button>
      <button id="update-btn" onclick="updateDashboard()">
        <span id="update-icon">&#x21BB;</span> 更新資料
      </button>
    </div>
  </header>
  <div id="kpi-bar">
    {kpi_html}
  </div>
</div>

<main>
  <div id="panel-all">
    {all_panel_html}
  </div>
  {cat_panels_html}
</main>

<aside id="drawer">
  <div id="drawer-inner"></div>
</aside>

<div id="drawer-overlay" onclick="closeDrawer()"></div>

<div id="drawer-panels">
  {drawer_panels}
</div>

<script>
function showView(cat) {{
  document.getElementById('panel-all').style.display = cat === 'all' ? '' : 'none';
  document.querySelectorAll('.panel-cat').forEach(function(p) {{
    p.style.display = p.dataset.cat === cat ? '' : 'none';
  }});
  closeDrawer();
  document.getElementById('search-box').value = '';
}}

function applySearch() {{
  var search = (document.getElementById('search-box').value || '').toLowerCase();
  document.querySelectorAll('.searchable-row').forEach(function(row) {{
    var visible = !search || row.dataset.name.toLowerCase().indexOf(search) !== -1;
    row.style.display = visible ? '' : 'none';
  }});
}}

function openDrawer(id) {{
  var panel = document.querySelector('#drawer-panels .drawer-panel[data-id="' + id + '"]');
  if (!panel) {{ return; }}
  document.getElementById('drawer-inner').innerHTML = panel.innerHTML;
  document.getElementById('drawer').classList.add('open');
  document.getElementById('drawer-overlay').style.display = 'block';
  document.body.style.overflow = 'hidden';
}}

function closeDrawer() {{
  document.getElementById('drawer').classList.remove('open');
  document.getElementById('drawer-overlay').style.display = 'none';
  document.body.style.overflow = '';
}}

document.addEventListener('keydown', function(ev) {{
  if (ev.key === 'Escape') {{ closeDrawer(); }}
}});

var DEVICES = {data_json};
var MATRIX_FIELDS = {matrix_json};

function completeness(d) {{
  var keys = ['camera_system','audio_system','microphone_presence','video_inputs','video_outputs',
    'wireless_sharing','supported_applications','supported_os','power_consumption',
    'mounting_options','environmental_specs','teardown_thermal','teardown_thermal_design',
    'teardown_key_ics','teardown_build_quality'];
  var filled = keys.filter(function(k) {{
    var v = d[k];
    return v && String(v).trim() && String(v) !== 'N/A' && String(v).length > 1;
  }}).length;
  return Math.round(filled / keys.length * 100);
}}

function exportMarkdown() {{
  var lines = ['# VC Competitor Benchmarker', ''];
  lines.push('| 產品名稱 | Category | Power | 完整度 | 新增日期 |');
  lines.push('|---|---|---|---|---|');
  DEVICES.forEach(function(d) {{
    lines.push('| ' + d.product_name + ' | ' + d.category + ' | ' +
      (d.power_consumption || 'N/A') + ' | ' + completeness(d) + '% | ' + (d.date_added || '') + ' |');
  }});
  var blob = new Blob([lines.join('\\n')], {{type: 'text/markdown;charset=utf-8'}});
  var a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'vc_benchmark_' + new Date().toISOString().slice(0, 10) + '.md';
  a.click();
}}

function toggleTheme() {{
  var dark = document.body.classList.toggle('dark');
  document.getElementById('theme-btn').innerHTML = dark ? '&#9728;' : '&#9790;';
  try {{ localStorage.setItem('vcb-theme', dark ? 'dark' : 'light'); }} catch(e) {{}}
}}
(function() {{
  try {{
    if (localStorage.getItem('vcb-theme') === 'dark') {{
      document.body.classList.add('dark');
      document.getElementById('theme-btn').innerHTML = '&#9728;';
    }}
  }} catch(e) {{}}
}})();

function updateDashboard() {{
  var btn = document.getElementById('update-btn');
  var icon = document.getElementById('update-icon');
  btn.disabled = true;
  icon.textContent = '⏳';
  fetch('/api/refresh')
    .then(function(r) {{
      if (!r.ok) {{ throw new Error('HTTP ' + r.status); }}
      return r.json();
    }})
    .then(function(data) {{
      if (data.status === 'ok') {{
        window.location.reload();
      }} else {{
        alert('更新失敗：' + (data.message || '未知錯誤'));
        btn.disabled = false;
        icon.textContent = '↻';
      }}
    }})
    .catch(function(err) {{
      if (err.message && err.message.indexOf('Failed to fetch') !== -1) {{
        alert('無法連線到伺服器。\\n請改用以下指令啟動：\\n\\n  python serve_dashboard.py');
      }} else {{
        alert('錯誤：' + err.message);
      }}
      btn.disabled = false;
      icon.textContent = '↻';
    }});
}}
</script>
</body>
</html>"""


def main():
    devices = load_devices()
    html = build_html(devices)
    out = os.path.join(BASE, 'reports', 'dashboard.html')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w', encoding='utf-8-sig') as f:
        f.write(html)
    print('Dashboard generated:', out)


if __name__ == '__main__':
    main()
