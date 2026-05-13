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
    'PTZ Camera':      {'bg': '#eef2ff', 'text': '#3730a3', 'border': '#c7d2fe'},
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
    st = (f'background:{c["bg"]};color:{c["text"]};border:1px solid {c["border"]};'
          'display:inline-block;padding:2px 10px;border-radius:9999px;'
          'font-size:0.7rem;font-weight:700;letter-spacing:0.04em;white-space:nowrap')
    return f'<span style="{st}">{e(cat)}</span>'


def soc_status(d):
    v = str(d.get('teardown_pcb') or '').strip()
    if v and v not in _NA_VALS and len(v) > 3:
        return '<span style="color:#16a34a;font-weight:600;font-size:0.75rem">✓ 有資料</span>'
    return '<span style="color:#a8a29e;font-size:0.75rem">—</span>'


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


def build_html(devices):
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    cats = list(dict.fromkeys(d['category'] for d in devices if d['category']))
    count = len(devices)
    cat_count = len(cats)
    td_count = sum(
        1 for d in devices
        if d.get('teardown_pcb') and str(d['teardown_pcb']).strip() not in _NA_VALS
        and len(str(d['teardown_pcb'])) > 3
    )

    kpi_html = (
        f'<div class="kpi-chip"><span class="kpi-val">{count}</span>'
        f'<span class="kpi-label">競品總數</span></div>'
        f'<div class="kpi-chip"><span class="kpi-val">{cat_count}</span>'
        f'<span class="kpi-label">產品類別</span></div>'
        f'<div class="kpi-chip"><span class="kpi-val">{td_count}</span>'
        f'<span class="kpi-label">有 SoC 資料</span></div>'
    )

    pill_html = ('<button class="cat-pill-btn pill-active" data-cat="all"'
                 ' onclick="setCategory(this.dataset.cat)">All</button>')
    for cat in cats:
        pill_html += (f'<button class="cat-pill-btn" data-cat="{e(cat)}"'
                      f' onclick="setCategory(this.dataset.cat)">{e(cat)}</button>')

    table_rows = ''
    for i, d in enumerate(devices, 1):
        power = str(d.get('power_consumption') or '').strip()
        if not power or power == 'N/A':
            power_html = '<span class="muted">—</span>'
        else:
            trunc = power[:45] + '…' if len(power) > 45 else power
            power_html = e(trunc)
        link_html = ''
        if is_url(d.get('datasheet_url')):
            link_html = (f'<a href="{e(d["datasheet_url"])}" target="_blank"'
                         f' class="tbl-link" onclick="event.stopPropagation()">↗</a>')
        row_cls = 'tbl-row tbl-alt' if i % 2 == 0 else 'tbl-row'
        table_rows += (
            f'<tr class="{row_cls}" data-id="{d["id"]}" data-cat="{e(d["category"])}"'
            f' data-name="{e(d["product_name"])}" onclick="openDrawer({d["id"]})">'
            f'<td class="tc tc-num">{i}</td>'
            f'<td class="tc tc-name">{e(d["product_name"])}</td>'
            f'<td class="tc">{cat_pill(d["category"])}</td>'
            f'<td class="tc tc-muted">{power_html}</td>'
            f'<td class="tc">{soc_status(d)}</td>'
            f'<td class="tc tc-date">{e(d.get("date_added") or "")}</td>'
            f'<td class="tc tc-link">{link_html}</td>'
            f'</tr>'
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
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:#fafaf9;color:#1c1917;line-height:1.5}}
#site-header{{
  position:sticky;top:0;z-index:30;background:#fff;border-bottom:1px solid #e7e5e4;
  padding:12px 24px;display:flex;align-items:center;gap:16px;
}}
.header-brand .title{{font-size:1rem;font-weight:700;color:#1c1917}}
.header-brand .sub{{font-size:0.72rem;color:#a8a29e;margin-top:1px}}
#search-box{{
  flex:1;max-width:300px;border:1px solid #e7e5e4;border-radius:8px;
  padding:7px 12px;font-size:0.85rem;color:#1c1917;background:#fafaf9;outline:none;
}}
#search-box:focus{{border-color:#4f46e5;background:#fff}}
.header-right{{display:flex;align-items:center;gap:10px;margin-left:auto;flex-shrink:0}}
#gen-time{{font-size:0.72rem;color:#a8a29e}}
#update-btn{{
  display:flex;align-items:center;gap:6px;background:#4f46e5;color:#fff;
  border:none;border-radius:8px;padding:7px 14px;font-size:0.8rem;font-weight:600;
  cursor:pointer;transition:background .15s;
}}
#update-btn:hover{{background:#4338ca}}
#update-btn:disabled{{opacity:.5;cursor:default}}
#filter-bar{{
  position:sticky;top:61px;z-index:20;background:#fff;border-bottom:1px solid #e7e5e4;
  padding:10px 24px;display:flex;align-items:center;gap:10px;flex-wrap:wrap;
}}
.kpi-chip{{
  display:flex;align-items:center;gap:6px;background:#fafaf9;
  border:1px solid #e7e5e4;border-radius:8px;padding:4px 12px;flex-shrink:0;
}}
.kpi-val{{font-size:0.95rem;font-weight:700;color:#1c1917}}
.kpi-label{{font-size:0.7rem;color:#a8a29e}}
.filter-sep{{width:1px;height:20px;background:#e7e5e4;flex-shrink:0}}
.cat-pill-btn{{
  background:#fafaf9;color:#78716c;border:1px solid #e7e5e4;border-radius:9999px;
  padding:4px 12px;font-size:0.72rem;font-weight:600;cursor:pointer;white-space:nowrap;
  transition:all .1s;
}}
.cat-pill-btn:hover{{background:#f5f5f4;color:#1c1917}}
.cat-pill-btn.pill-active{{background:#4f46e5;color:#fff;border-color:#4f46e5}}
#row-count{{font-size:0.72rem;color:#a8a29e;margin-left:auto;white-space:nowrap}}
main{{padding:0 24px 80px}}
#main-table{{width:100%;border-collapse:collapse;min-width:700px}}
#main-table thead th{{
  background:#fff;border-bottom:2px solid #e7e5e4;
  padding:10px 12px;font-size:0.72rem;font-weight:600;color:#78716c;
  text-align:left;white-space:nowrap;
}}
.tbl-row{{cursor:pointer;transition:background .1s}}
.tbl-row:hover{{background:#eff6ff !important}}
.tbl-alt{{background:#f5f5f4}}
.tc{{
  padding:10px 12px;font-size:0.82rem;color:#1c1917;
  border-bottom:1px solid #e7e5e4;vertical-align:middle;
}}
.tc-num{{color:#a8a29e;font-size:0.75rem;width:40px}}
.tc-name{{font-weight:600;max-width:240px}}
.tc-muted{{color:#78716c;max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.tc-date{{color:#a8a29e;font-size:0.75rem;white-space:nowrap}}
.tc-link{{width:36px;text-align:center}}
.tbl-link{{color:#4f46e5;text-decoration:none;font-size:0.9rem}}
.tbl-link:hover{{color:#4338ca}}
.muted{{color:#a8a29e;font-size:0.75rem}}
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
.drawer-name{{font-size:1.05rem;font-weight:700;color:#1c1917;line-height:1.3;margin-bottom:6px}}
.drawer-meta{{display:flex;align-items:center;gap:8px;flex-wrap:wrap}}
.date-chip{{color:#a8a29e;font-size:0.72rem}}
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
.dl-link{{text-decoration:none;font-size:0.78rem;font-weight:600;border-radius:6px;padding:4px 10px}}
.indigo-link{{background:#eef2ff;color:#4f46e5;border:1px solid #c7d2fe}}
.indigo-link:hover{{background:#e0e7ff}}
.amber-link{{background:#fffbeb;color:#b45309;border:1px solid #fde68a}}
.amber-link:hover{{background:#fef3c7}}
.amber-link-sm{{color:#b45309;font-size:0.75rem}}
.drawer-details{{border-bottom:1px solid #e7e5e4}}
.drawer-summary{{
  display:flex;align-items:center;gap:6px;padding:12px 24px;cursor:pointer;
  font-size:0.8rem;font-weight:600;color:#4f46e5;list-style:none;
}}
.drawer-summary::-webkit-details-marker{{display:none}}
.drawer-summary .arrow{{transition:transform .2s}}
details[open] .drawer-summary .arrow{{transform:rotate(90deg)}}
.kv-section{{padding:4px 24px 14px}}
.kv-table{{width:100%;border-collapse:collapse}}
.kv-label{{color:#78716c;font-size:0.72rem;padding:5px 14px 5px 0;white-space:nowrap;vertical-align:top;width:140px}}
.kv-val{{font-size:0.8rem;color:#1c1917;padding:5px 0;vertical-align:top}}
.drawer-section{{padding:14px 24px}}
.section-hd{{font-size:0.8rem;font-weight:600;color:#4f46e5;margin-bottom:8px}}
.notes-box{{
  background:#fafaf9;border:1px solid #e7e5e4;border-radius:8px;
  padding:10px 14px;font-size:0.78rem;color:#78716c;line-height:1.6;
}}
#drawer-panels{{display:none}}
</style>
</head>
<body>

<header id="site-header">
  <div class="header-brand">
    <div class="title">VC Competitor Benchmarker</div>
    <div class="sub">Logitech 競品分析儀表板</div>
  </div>
  <input id="search-box" type="text" placeholder="搜尋產品名稱…" oninput="applyFilters()">
  <div class="header-right">
    <span id="gen-time">Generated {now}</span>
    <button id="update-btn" onclick="updateDashboard()">
      <span id="update-icon">&#x21BB;</span> 更新資料
    </button>
  </div>
</header>

<div id="filter-bar">
  {kpi_html}
  <div class="filter-sep"></div>
  {pill_html}
  <span id="row-count">顯示 {count} / {count} 筆</span>
</div>

<main>
  <table id="main-table">
    <thead>
      <tr>
        <th class="tc-num">#</th>
        <th style="min-width:200px">產品名稱</th>
        <th>Category</th>
        <th style="min-width:130px">Power 功耗</th>
        <th>SoC 狀態</th>
        <th>新增日期</th>
        <th></th>
      </tr>
    </thead>
    <tbody id="table-body">
      {table_rows}
    </tbody>
  </table>
</main>

<aside id="drawer">
  <div id="drawer-inner"></div>
</aside>

<div id="drawer-overlay" onclick="closeDrawer()"></div>

<div id="drawer-panels">
  {drawer_panels}
</div>

<script>
var activeCategory = 'all';

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

function setCategory(cat) {{
  activeCategory = cat;
  document.querySelectorAll('.cat-pill-btn').forEach(function(btn) {{
    if (btn.dataset.cat === cat) {{
      btn.classList.add('pill-active');
    }} else {{
      btn.classList.remove('pill-active');
    }}
  }});
  applyFilters();
}}

function applyFilters() {{
  var search = (document.getElementById('search-box').value || '').toLowerCase();
  var rows = document.querySelectorAll('#table-body tr');
  var shown = 0;
  rows.forEach(function(row) {{
    var matchCat = activeCategory === 'all' || row.dataset.cat === activeCategory;
    var matchSearch = !search || row.dataset.name.toLowerCase().indexOf(search) !== -1;
    if (matchCat && matchSearch) {{
      row.style.display = '';
      shown++;
    }} else {{
      row.style.display = 'none';
    }}
  }});
  document.getElementById('row-count').textContent =
    '顯示 ' + shown + ' / ' + rows.length + ' 筆';
}}

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
