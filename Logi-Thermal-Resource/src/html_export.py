"""Generate a standalone HTML dashboard from current SQLite data."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from src import db, viz

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _div(fig, div_id: str = "") -> str:
    return fig.to_html(full_html=False, include_plotlyjs=False, div_id=div_id or None)


def generate(year: int) -> str:
    """Return a self-contained HTML string for the given year."""
    monthly = db.monthly_load(year)
    projects_meta = db.projects_with_meta()
    overload_df = db.overload_summary(year)
    engineers = db.list_engineers()

    n_overload = int((overload_df["status"] == "overload").sum()) if not overload_df.empty else 0
    n_idle = int((overload_df["status"] == "idle").sum()) if not overload_df.empty else 0
    max_load = float(overload_df["total_load"].max()) if not overload_df.empty else 0.0
    peak_eng = (
        overload_df.loc[overload_df["total_load"].idxmax(), "engineer"]
        if not overload_df.empty and max_load > 0 else "—"
    )

    banner_cls = "overload" if n_overload > 0 else "ok"
    banner_txt = (
        f"⚠️ {n_overload} 個工程師-月份過載（負載 > 1.0）　最高：{peak_eng} = {max_load:.2f}"
        if n_overload > 0
        else f"✅ {year} 無過載月份　閒置月份：{n_idle}"
    )
    delta_cls = "delta-bad" if max_load > 1.0 else "delta-ok"

    heatmap_div = _div(viz.heatmap_engineer_month(monthly, year), "heatmap")
    peak_div = _div(viz.peak_load_bar(monthly), "peak")
    state_div = _div(viz.state_bar(projects_meta), "state")

    # Per-engineer stacked bar tabs
    fc_engineers = [e for e in engineers if e != "Unassigned (Vision)"]
    tab_nav_html = ""
    tab_content_html = ""
    for i, eng in enumerate(fc_engineers):
        breakdown = db.engineer_project_breakdown(year, eng)
        fig = viz.stacked_bar_projects(breakdown, eng, year)
        tab_id = f"eng{i}"
        active = "active" if i == 0 else ""
        display = "block" if i == 0 else "none"
        tab_nav_html += f'<button class="tab-btn {active}" onclick="showTab(\'{tab_id}\', this)">{eng}</button>\n'
        tab_content_html += f'<div id="{tab_id}" class="tab-pane" style="display:{display}">{_div(fig, tab_id + "_c")}</div>\n'

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Logi Thermal Resource Dashboard {year}</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#F3F4F6;padding:24px;color:#111827}}
    .header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}}
    .header h1{{font-size:1.4rem;font-weight:700}}
    .ts{{font-size:.8rem;color:#9CA3AF}}
    .banner{{border-radius:8px;padding:12px 16px;margin-bottom:16px;font-weight:500;font-size:.95rem}}
    .overload{{background:#FEE2E2;color:#991B1B;border-left:4px solid #EF4444}}
    .ok{{background:#D1FAE5;color:#065F46;border-left:4px solid #22C55E}}
    .kpi-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px}}
    .kpi{{background:white;border-radius:8px;padding:16px;box-shadow:0 1px 3px rgba(0,0,0,.1)}}
    .kpi-label{{font-size:.78rem;color:#6B7280;margin-bottom:4px}}
    .kpi-value{{font-size:1.6rem;font-weight:700}}
    .kpi-delta{{font-size:.78rem;margin-top:2px}}
    .delta-bad{{color:#EF4444}}
    .delta-ok{{color:#22C55E}}
    .card{{background:white;border-radius:8px;padding:16px;box-shadow:0 1px 3px rgba(0,0,0,.1);margin-bottom:16px}}
    .two-col{{display:grid;grid-template-columns:3fr 2fr;gap:16px;margin-bottom:16px}}
    .section-title{{font-size:1rem;font-weight:600;color:#374151;margin-bottom:12px;border-bottom:1px solid #E5E7EB;padding-bottom:8px}}
    .tab-btn{{padding:7px 14px;border:none;background:#E5E7EB;cursor:pointer;border-radius:6px;margin:0 4px 12px 0;font-size:.875rem;color:#374151}}
    .tab-btn:hover{{background:#D1D5DB}}
    .tab-btn.active{{background:#3B82F6;color:white}}
    footer{{margin-top:24px;text-align:center;color:#9CA3AF;font-size:.8rem}}
    @media(max-width:768px){{.kpi-row,.two-col{{grid-template-columns:1fr 1fr}}}}
    @media(max-width:480px){{.kpi-row{{grid-template-columns:1fr 1fr}}}}
  </style>
</head>
<body>
  <div class="header">
    <h1>🌡️ Logi Thermal Resource Dashboard {year}</h1>
    <span class="ts">匯出：{now}</span>
  </div>

  <div class="banner {banner_cls}">{banner_txt}</div>

  <div class="kpi-row">
    <div class="kpi">
      <div class="kpi-label">最高月負載</div>
      <div class="kpi-value">{max_load:.2f}</div>
      <div class="kpi-delta {delta_cls}">{max_load - 1.0:+.2f} vs 滿載</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">⚠️ 過載月份</div>
      <div class="kpi-value">{n_overload}</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">最忙工程師</div>
      <div class="kpi-value" style="font-size:1.1rem;padding-top:6px">{peak_eng}</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">💤 閒置月份</div>
      <div class="kpi-value">{n_idle}</div>
    </div>
  </div>

  <div class="card">
    <div class="section-title">工程師月度負載 Heatmap</div>
    {heatmap_div}
  </div>

  <div class="two-col">
    <div class="card">
      <div class="section-title">工程師年度峰值負載</div>
      {peak_div}
    </div>
    <div class="card">
      <div class="section-title">專案 State 分布</div>
      {state_div}
    </div>
  </div>

  <div class="card">
    <div class="section-title">工程師月度負載分解</div>
    <div>{tab_nav_html}</div>
    {tab_content_html}
  </div>

  <footer>Powered by Claude Sonnet 4.6 &nbsp;·&nbsp; Logi Thermal Resource Dashboard</footer>

  <script>
    function showTab(id, btn) {{
      document.querySelectorAll('.tab-pane').forEach(p => p.style.display = 'none');
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.getElementById(id).style.display = 'block';
      btn.classList.add('active');
    }}
  </script>
</body>
</html>"""
