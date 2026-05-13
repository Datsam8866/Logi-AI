# -*- coding: utf-8-sig -*-
"""
Generate reports/dashboard.html from vc_benchmark.db.
Re-run whenever new competitors are added.
"""
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
CAT_CLS = {
    'Compute':         ('bg-purple-900', 'text-purple-300'),
    'Security Camera': ('bg-blue-900',   'text-blue-300'),
    'IR Camera':       ('bg-orange-900', 'text-orange-300'),
    'VC Device':       ('bg-green-900',  'text-green-300'),
}

def e(s):
    return _html.escape(str(s or ''), quote=True)

def is_url(value):
    parsed = urlparse(str(value or '').strip())
    return parsed.scheme in ('http', 'https') and bool(parsed.netloc)

def split_sources(value):
    return [part.strip() for part in str(value or '').split('|') if part.strip()]

def source_link_label(url):
    host = urlparse(str(url or '')).netloc.lower()
    return 'FCC↗' if 'fccid.io' in host else 'Teardown↗'

def cat_badge(cat):
    bg, fg = CAT_CLS.get(cat, ('bg-gray-700', 'text-gray-300'))
    return f'<span class="tag {bg} {fg}">{e(cat)}</span>'

def completeness(d):
    filled = sum(1 for k in SPEC_KEYS
                 if d.get(k) and str(d[k]).strip() not in ('', 'N/A', 'null') and len(str(d[k])) > 1)
    return round(filled / len(SPEC_KEYS) * 100)

def bar(pct, width='w-24'):
    color = '#22c55e' if pct >= 80 else '#f59e0b' if pct >= 50 else '#ef4444'
    return (f'<div class="flex items-center gap-2">'
            f'<div class="bar-bg {width}"><div class="bar-fill" style="width:{pct}%;background:{color}"></div></div>'
            f'<span class="text-xs text-gray-500">{pct}%</span></div>')

def cell(val):
    v = str(val or '').strip()
    if not v or v in ('N/A', 'null'):
        return '<span class="text-gray-600 text-xs">N/A</span>'
    if v == 'No':
        return '<span class="text-red-400 font-bold">✗</span>'
    if v.lower() == 'yes' or v.lower().startswith('yes ') or v.lower().startswith('yes -'):
        rest = v[v.index(' ')+1:] if ' ' in v else ''
        return f'<span class="text-green-400 font-bold">✓</span>' + (f' <span class="cell-text text-gray-300">{e(rest)}</span>' if rest else '')
    return f'<span class="cell-text text-gray-300">{e(v)}</span>'

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

# ── Tab sections ──────────────────────────────────────────────────────────────

def kpi_card(label, value, sub, color, small=False):
    size = 'text-2xl' if small else 'text-4xl'
    return (f'<div class="bg-gray-800 rounded-xl p-5 border border-gray-700">'
            f'<div class="text-gray-500 text-xs uppercase tracking-widest mb-2">{label}</div>'
            f'<div class="{size} font-bold {color}">{value}</div>'
            f'<div class="text-gray-600 text-xs mt-1">{sub}</div>'
            f'</div>')

def build_overview(devices):
    cats = list(dict.fromkeys(d['category'] for d in devices if d['category']))
    count = len(devices)
    cat_count = len(cats)
    td_count = sum(1 for d in devices if d.get('teardown_source') and any(is_url(src) for src in split_sources(d.get('teardown_source'))))
    dates = [d['date_added'] for d in devices if d.get('date_added')]
    latest = max(dates) if dates else 'N/A'

    # KPI
    html = '<section class="grid grid-cols-4 gap-4 mb-8">'
    html += kpi_card('競品總數', count, '已建檔產品', 'text-blue-400')
    html += kpi_card('涵蓋 Category', cat_count, '個產品類別', 'text-purple-400')
    html += kpi_card('有拆解資料', f'{td_count}/{count}', '產品有熱設計拆解', 'text-green-400')
    html += kpi_card('最新新增', latest, '最近 benchmark 日期', 'text-amber-400', small=True)
    html += '</section>'

    # Roster header
    html += '<section class="mb-8">'
    html += ('<div class="flex items-center justify-between mb-4">'
             '<h2 class="text-gray-500 text-xs font-semibold uppercase tracking-widest">競品名錄</h2>'
             '<button onclick="exportMarkdown()" '
             'class="text-xs bg-gray-700 hover:bg-gray-600 text-gray-300 px-3 py-1.5 rounded-lg transition-colors">'
             '↓ 匯出 Markdown</button>'
             '</div>')

    # Category summary cards
    html += '<div class="grid grid-cols-3 gap-4 mb-6">'
    for cat in cats:
        devs = [d for d in devices if d['category'] == cat]
        bg, fg = CAT_CLS.get(cat, ('bg-gray-700', 'text-gray-300'))
        html += f'<div class="bg-gray-800 rounded-xl border border-gray-700 p-4">'
        html += f'<div class="flex items-center justify-between mb-3">{cat_badge(cat)}<span class="text-2xl font-bold text-white">{len(devs)}</span></div>'
        html += '<ul class="space-y-3">'
        for d in devs:
            pct = completeness(d)
            html += f'<li><div class="flex items-center justify-between mb-1"><span class="text-sm text-gray-200 font-medium leading-tight">{e(d["product_name"])}</span></div>'
            html += bar(pct) + '</li>'
        html += '</ul></div>'
    html += '</div>'

    # Full product table
    html += '<div class="bg-gray-800 rounded-xl border border-gray-700 overflow-x-auto">'
    html += '<table class="w-full text-sm">'
    html += ('<thead><tr style="background:#1f2937" class="border-b border-gray-700">'
             '<th class="text-left px-4 py-3 text-gray-400 text-xs font-semibold">產品名稱</th>'
             '<th class="text-left px-4 py-3 text-gray-400 text-xs font-semibold">Category</th>'
             '<th class="text-left px-4 py-3 text-gray-400 text-xs font-semibold">Power</th>'
             '<th class="text-left px-4 py-3 text-gray-400 text-xs font-semibold">資料完整度</th>'
             '<th class="text-left px-4 py-3 text-gray-400 text-xs font-semibold">新增日期</th>'
             '<th class="text-left px-4 py-3 text-gray-400 text-xs font-semibold">連結</th>'
             '</tr></thead><tbody>')
    for d in devices:
        pct = completeness(d)
        links = ''
        if is_url(d.get('datasheet_url')):
            links += f'<a href="{e(d["datasheet_url"])}" target="_blank" class="text-xs text-blue-400 hover:text-blue-300 underline mr-2">Datasheet↗</a>'
        teardown_urls = [src for src in split_sources(d.get('teardown_source')) if is_url(src)]
        if teardown_urls:
            links += f'<a href="{e(teardown_urls[0])}" target="_blank" class="text-xs text-amber-400 hover:text-amber-300 underline">{source_link_label(teardown_urls[0])}</a>'
        html += (f'<tr class="border-b border-gray-700/50">'
                 f'<td class="px-4 py-3 text-gray-200 text-xs font-medium">{e(d["product_name"])}</td>'
                 f'<td class="px-4 py-3">{cat_badge(d["category"])}</td>'
                 f'<td class="px-4 py-3 text-gray-400 text-xs">{e(d.get("power_consumption") or "N/A")}</td>'
                 f'<td class="px-4 py-3">{bar(pct)}</td>'
                 f'<td class="px-4 py-3 text-gray-500 text-xs">{e(d.get("date_added") or "")}</td>'
                 f'<td class="px-4 py-3">{links}</td>'
                 f'</tr>')
    html += '</tbody></table></div>'
    html += '</section>'
    return html


def build_category_tab(cat, devs):
    html = ''

    # Product cards
    html += f'<section class="mb-8">'
    html += f'<h2 class="text-gray-500 text-xs font-semibold uppercase tracking-widest mb-4">產品總覽 — {e(cat)}</h2>'
    cols = min(len(devs), 3)
    html += f'<div class="grid grid-cols-{cols} gap-4">'
    for d in devs:
        pct = completeness(d)
        links = ''
        if is_url(d.get('datasheet_url')):
            links += f'<a href="{e(d["datasheet_url"])}" target="_blank" class="text-xs text-blue-400 hover:text-blue-300 underline">Datasheet↗</a>'
        teardown_urls = [src for src in split_sources(d.get('teardown_source')) if is_url(src)]
        if teardown_urls:
            links += f' <a href="{e(teardown_urls[0])}" target="_blank" class="text-xs text-amber-400 hover:text-amber-300 underline">{source_link_label(teardown_urls[0])}</a>'

        rows = ''
        for key, label in [('camera_system','Camera'), ('audio_system','Audio'),
                            ('power_consumption','Power'), ('dimensions','Size'),
                            ('teardown_thermal','Thermal')]:
            v = d.get(key, '')
            if v and v != 'N/A':
                color = 'text-amber-500' if key == 'teardown_thermal' else 'text-gray-500'
                rows += (f'<div class="cell-text">'
                         f'<span class="{color}">{label}: </span>'
                         f'<span class="text-gray-300">{e(str(v)[:90])}</span>'
                         f'</div>')

        html += (f'<div class="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">'
                 f'<div class="px-4 py-3 border-b border-gray-700 flex items-center justify-between">'
                 f'{cat_badge(d["category"])}{bar(pct, "w-16")}'
                 f'</div>'
                 f'<div class="px-4 py-4">'
                 f'<h3 class="font-semibold text-white text-sm mb-3 leading-snug">{e(d["product_name"])}</h3>'
                 f'<div class="space-y-1.5">{rows}</div>'
                 f'<div class="mt-3 flex gap-3">{links}</div>'
                 f'</div></div>')
    html += '</div></section>'

    # Feature matrix (only show if >1 device in this category)
    if len(devs) > 1:
        html += '<section class="mb-8">'
        html += '<h2 class="text-gray-500 text-xs font-semibold uppercase tracking-widest mb-3">功能比較矩陣</h2>'
        html += '<div class="bg-gray-800 rounded-xl border border-gray-700 overflow-x-auto"><table class="w-full text-sm border-collapse">'
        html += '<thead><tr style="background:#1f2937"><th class="text-left px-4 py-3 text-gray-400 text-xs font-semibold w-36 border-b border-gray-700">Feature</th>'
        for d in devs:
            html += (f'<th class="text-left px-4 py-3 text-xs font-medium min-w-52 border-b border-gray-700">'
                     f'{cat_badge(d["category"])}<br><span class="text-gray-200">{e(d["product_name"])}</span></th>')
        html += '</tr></thead><tbody>'
        for key, label in MATRIX_FIELDS:
            html += f'<tr><td class="px-4 py-2.5 text-gray-500 text-xs font-medium whitespace-nowrap align-top border-b border-gray-700/40">{label}</td>'
            for d in devs:
                html += f'<td class="px-4 py-2.5 align-top border-b border-gray-700/40 max-w-xs">{cell(d.get(key))}</td>'
            html += '</tr>'
        html += '</tbody></table></div></section>'

    # Teardown
    html += '<section class="mb-8">'
    html += '<h2 class="text-gray-500 text-xs font-semibold uppercase tracking-widest mb-3">拆解 / 熱設計分析</h2>'
    html += '<div class="space-y-4">'
    for d in devs:
        td_sections = [
            ('text-amber-400', 'Thermal Design',  d.get('teardown_thermal_design')),
            ('text-blue-400',  'Key ICs',          d.get('teardown_key_ics')),
            ('text-purple-400','PCB Overview',     d.get('teardown_pcb')),
            ('text-green-400', 'Build Quality',    d.get('teardown_build_quality')),
        ]
        td_html = ''
        for color, title, content in td_sections:
            td_html += (f'<div><h4 class="{color} text-xs font-bold uppercase tracking-widest mb-2">{title}</h4>'
                        f'<p class="text-gray-300 text-sm leading-relaxed mono">{e(content or "No data")}</p></div>')

        note_html = ''
        if d.get('notes'):
            note_html = (f'<div class="mt-4 bg-gray-700/40 rounded-lg p-3 text-xs text-gray-400 leading-relaxed">'
                         f'<span class="text-gray-500 font-semibold">Note: </span>{e(d["notes"])}</div>')

        src_html = ''
        if d.get('teardown_source'):
            for source in split_sources(d.get('teardown_source')):
                if is_url(source):
                    src_html += f'<a href="{e(source)}" target="_blank" class="text-xs text-amber-400 hover:text-amber-300 underline">Teardown Source↗</a> '
                elif not source.upper().startswith('N/A'):
                    src_html += f'<span class="text-xs text-gray-500">{e(source)}</span> '

        html += (f'<div class="bg-gray-800 rounded-xl border border-gray-700 p-5">'
                 f'<div class="flex items-center gap-3 mb-5">{cat_badge(d["category"])}'
                 f'<span class="font-semibold text-white text-sm">{e(d["product_name"])}</span></div>'
                 f'<div class="grid grid-cols-2 gap-6">{td_html}</div>'
                 f'{note_html}'
                 f'{"<div class=mt-4>" + src_html + "</div>" if src_html else ""}'
                 f'</div>')
    html += '</div></section>'

    # Dynamic specs (using <details>)
    html += '<section class="mb-8">'
    html += '<h2 class="text-gray-500 text-xs font-semibold uppercase tracking-widest mb-3">產品特規（Dynamic Columns）</h2>'
    html += '<div class="space-y-3">'
    for d in devs:
        dc = d.get('dynamic_columns') or {}
        if not dc:
            continue
        entries = list(dc.items())
        kv_rows = ''.join(
            f'<div class="kv-row px-5 py-2.5 flex gap-6">'
            f'<div class="text-gray-500 text-xs w-52 shrink-0 pt-0.5">{e(k)}</div>'
            f'<div class="text-gray-200 text-sm mono">{e(str(v))}</div>'
            f'</div>'
            for k, v in entries
        )
        html += (f'<details class="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">'
                 f'<summary class="px-5 py-3 flex items-center gap-3 cursor-pointer hover:bg-gray-700/40 transition-colors list-none">'
                 f'{cat_badge(d["category"])}'
                 f'<span class="text-sm font-medium text-gray-200">{e(d["product_name"])}</span>'
                 f'<span class="text-gray-600 text-xs">{len(entries)} specs</span>'
                 f'<span class="ml-auto text-gray-500">▸</span>'
                 f'</summary>'
                 f'<div class="border-t border-gray-700 divide-y divide-gray-700/50">{kv_rows}</div>'
                 f'</details>')
    html += '</div></section>'
    return html


# ── Main builder ─────────────────────────────────────────────────────────────

def build_html(devices):
    cats = list(dict.fromkeys(d['category'] for d in devices if d['category']))
    now  = datetime.now().strftime('%Y-%m-%d %H:%M')

    # Build tab labels and IDs
    tab_ids    = ['overview'] + [f'cat{i}' for i in range(len(cats))]
    tab_labels = ['Overview'] + cats

    # Tab bar HTML
    tab_bar = ''
    for i, (tid, label) in enumerate(zip(tab_ids, tab_labels)):
        active = ' active' if i == 0 else ''
        tab_bar += (f'<button id="tab-{tid}" class="main-tab{active}" '
                    f'onclick="showTab(\'{tid}\')">{_html.escape(label)}</button>')

    # Panel HTML
    panels = ''
    for i, (tid, label) in enumerate(zip(tab_ids, tab_labels)):
        style = '' if i == 0 else ' style="display:none"'
        if tid == 'overview':
            content = build_overview(devices)
        else:
            cat = cats[i - 1]
            cat_devs = [d for d in devices if d['category'] == cat]
            content = build_category_tab(cat, cat_devs)
        panels += f'<div id="panel-{tid}" class="tab-panel"{style}>{content}</div>'

    # Embed data for markdown export
    # Replace </script> so the inline script tag isn't closed prematurely
    data_json = json.dumps(
        [{k: (list(d['dynamic_columns'].items()) if k == 'dynamic_columns' else v)
          for k, v in d.items()} for d in devices],
        ensure_ascii=False
    ).replace('</', '<\\/')
    matrix_json = json.dumps([{'key': k, 'label': l} for k, l in MATRIX_FIELDS], ensure_ascii=False).replace('</', '<\\/')

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VC Competitor Benchmarker</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  body  {{ font-family:'Segoe UI',system-ui,sans-serif; background:#111827; color:#f9fafb; }}
  .mono {{ font-family:Consolas,'Courier New',monospace; }}
  .tag  {{ display:inline-block; padding:2px 10px; border-radius:9999px;
           font-size:0.7rem; font-weight:700; letter-spacing:0.04em; }}
  .cell-text {{ font-size:0.72rem; line-height:1.5; }}
  .bar-bg   {{ background:#1f2937; border-radius:9999px; height:6px; overflow:hidden; }}
  .bar-fill {{ height:6px; border-radius:9999px; }}
  .kv-row:nth-child(odd) {{ background:rgba(255,255,255,0.03); }}
  details summary::-webkit-details-marker {{ display:none; }}
  details[open] summary span.ml-auto {{ transform:rotate(90deg); }}

  .main-tab {{
    padding:10px 20px; font-size:0.85rem; font-weight:500; color:#6b7280;
    border-bottom:2px solid transparent; border-top:none; border-left:none; border-right:none;
    background:none; cursor:pointer; white-space:nowrap;
    transition:color .15s, border-color .15s;
  }}
  .main-tab:hover {{ color:#d1d5db; }}
  .main-tab.active {{ color:#fff; border-bottom-color:#60a5fa; }}

  body {{ background:#f8fafc; color:#111827; }}
  .bg-gray-800 {{ background:#ffffff !important; }}
  .bg-gray-700, .bg-gray-700\\/40 {{ background:#f1f5f9 !important; }}
  .bg-gray-900 {{ background:#f8fafc !important; }}
  .border-gray-700, .border-gray-700\\/40, .border-gray-700\\/50 {{ border-color:#e2e8f0 !important; }}
  .text-white, .text-gray-200, .text-gray-300 {{ color:#111827 !important; }}
  .text-gray-400, .text-gray-500, .text-gray-600 {{ color:#64748b !important; }}
  .bar-bg {{ background:#e2e8f0; }}
  .kv-row:nth-child(odd) {{ background:#f8fafc; }}
  .main-tab:hover {{ color:#111827; background:#f8fafc; }}
  .main-tab.active {{ color:#2563eb; border-bottom-color:#2563eb; background:#eff6ff; }}
  .tag {{ border:1px solid rgba(148,163,184,0.35); }}
</style>
</head>
<body class="min-h-screen">

<div class="sticky top-0 z-10">
<header class="bg-gray-800 border-b border-gray-700 px-8 py-4 flex items-center justify-between">
  <div>
    <h1 class="text-lg font-bold text-white tracking-tight">VC Competitor Benchmarker</h1>
    <p class="text-gray-400 text-xs mt-0.5">Logitech 競品分析儀表板</p>
  </div>
  <div class="flex items-center gap-3">
    <span class="text-gray-600 text-xs" id="gen-time">Generated {now}</span>
    <button id="update-btn" onclick="updateDashboard()"
      class="flex items-center gap-1.5 text-xs bg-blue-700 hover:bg-blue-600 disabled:opacity-50
             text-white px-3 py-1.5 rounded-lg transition-colors font-medium">
      <span id="update-icon">&#x21BB;</span> 更新資料
    </button>
  </div>
</header>
<nav class="bg-gray-800 border-b border-gray-700 px-8 flex gap-1 overflow-x-auto">
  {tab_bar}
</nav>
</div>

<main class="px-8 py-7 max-w-7xl mx-auto">
  {panels}
</main>

<script>
function showTab(id) {{
  document.querySelectorAll('.tab-panel').forEach(function(p) {{ p.style.display = 'none'; }});
  document.querySelectorAll('.main-tab').forEach(function(t) {{ t.classList.remove('active'); }});
  document.getElementById('panel-' + id).style.display = '';
  document.getElementById('tab-' + id).classList.add('active');
}}

// ── Markdown export ──────────────────────────────────────────────────────────
var DEVICES = {data_json};
var MATRIX_FIELDS = {matrix_json};

function completeness(d) {{
  var keys = ['camera_system','audio_system','microphone_presence','video_inputs','video_outputs',
    'wireless_sharing','supported_applications','supported_os','power_consumption',
    'mounting_options','environmental_specs','teardown_thermal','teardown_thermal_design',
    'teardown_key_ics','teardown_build_quality'];
  var filled = keys.filter(function(k) {{
    var v = d[k]; return v && String(v).trim() && String(v) !== 'N/A' && String(v).length > 1;
  }}).length;
  return Math.round(filled / keys.length * 100);
}}

function exportMarkdown() {{
  var lines = ['# VC Competitor Benchmarker — 競品名錄', ''];
  lines.push('| 產品名稱 | Category | Power | 資料完整度 | 新增日期 |');
  lines.push('|---|---|---|---|---|');
  DEVICES.forEach(function(d) {{
    lines.push('| ' + d.product_name + ' | ' + d.category + ' | ' +
      (d.power_consumption||'N/A') + ' | ' + completeness(d) + '% | ' + (d.date_added||'') + ' |');
  }});
  lines.push('', '## 功能比較矩陣', '');
  var header = '| Feature |' + DEVICES.map(function(d) {{ return ' ' + d.product_name + ' |'; }}).join('');
  var sep    = '|---|'       + DEVICES.map(function()  {{ return '---|'; }}).join('');
  lines.push(header, sep);
  MATRIX_FIELDS.forEach(function(f) {{
    var row = '| ' + f.label + ' |';
    DEVICES.forEach(function(d) {{
      row += ' ' + String(d[f.key]||'N/A').replace(/\\n/g,' ').substring(0,60) + ' |';
    }});
    lines.push(row);
  }});
  var blob = new Blob([lines.join('\\n')], {{type:'text/markdown;charset=utf-8'}});
  var a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'vc_benchmark_' + new Date().toISOString().slice(0,10) + '.md';
  a.click();
}}

// ── Update from SQLite ───────────────────────────────────────────────────────
function updateDashboard() {{
  var btn  = document.getElementById('update-btn');
  var icon = document.getElementById('update-icon');
  btn.disabled = true;
  icon.textContent = '⏳';

  fetch('/api/refresh')
    .then(function(r) {{
      if (!r.ok) throw new Error('HTTP ' + r.status);
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
