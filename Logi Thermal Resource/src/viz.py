"""Plotly chart factories used by app.py."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

STATE_COLORS = {
    "PA1": "#4F8BF9",
    "PB1": "#9C27B0",
    "PQR": "#43A047",
    "RFQ": "#FB8C00",
    "Engineering Response": "#039BE5",
    "TBD": "#9E9E9E",
    "Unknown": "#BDBDBD",
}


def heatmap_engineer_month(monthly: pd.DataFrame, year: int) -> go.Figure:
    """monthly columns: engineer, month, total_load."""
    if monthly.empty:
        return _empty_fig(f"{year} 無資料")
    pivot = monthly.pivot(index="engineer", columns="month", values="total_load").fillna(0)
    pivot = pivot.reindex(columns=range(1, 13), fill_value=0)
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=MONTH_LABELS,
        y=pivot.index.tolist(),
        colorscale="RdYlGn_r",
        zmin=0, zmax=1.5,
        colorbar=dict(title="Load"),
        text=pivot.values,
        texttemplate="%{text:.1f}",
        hovertemplate="%{y} | %{x} | load=%{z:.2f}<extra></extra>",
    ))
    fig.update_layout(
        title=f"{year} 工程師 × 月份 熱負載",
        height=320,
        margin=dict(l=80, r=20, t=50, b=40),
    )
    return fig


def stacked_bar_projects(breakdown: pd.DataFrame, engineer: str, year: int) -> go.Figure:
    """breakdown columns: month, project_name, load (already filtered for engineer)."""
    if breakdown.empty:
        return _empty_fig(f"{engineer} {year} 無分配")
    g = breakdown.groupby(["month", "project_name"], as_index=False)["load"].sum()
    g["month_label"] = g["month"].map(lambda m: MONTH_LABELS[m - 1])
    fig = px.bar(g, x="month_label", y="load", color="project_name",
                 category_orders={"month_label": MONTH_LABELS},
                 labels={"month_label": "Month", "load": "Load", "project_name": "Project"})
    fig.add_hline(y=1.0, line_dash="dash", line_color="red",
                  annotation_text="overload 1.0", annotation_position="top right")
    fig.add_hline(y=0.8, line_dash="dot", line_color="orange")
    fig.update_layout(
        title=f"{engineer} {year} 月度負載分解",
        height=420, barmode="stack",
        margin=dict(l=60, r=20, t=50, b=40),
    )
    return fig


def line_total_load(monthly: pd.DataFrame, year: int) -> go.Figure:
    if monthly.empty:
        return _empty_fig(f"{year} 無資料")
    df = monthly.copy()
    df["month_label"] = df["month"].map(lambda m: MONTH_LABELS[m - 1])
    fig = px.line(df, x="month_label", y="total_load", color="engineer", markers=True,
                  category_orders={"month_label": MONTH_LABELS})
    fig.add_hline(y=1.0, line_dash="dash", line_color="red")
    fig.add_hline(y=0.8, line_dash="dot", line_color="orange")
    fig.update_layout(
        title=f"{year} 工程師月負載趨勢",
        height=380, yaxis_title="Total load",
        margin=dict(l=60, r=20, t=50, b=40),
    )
    return fig


def gantt_projects(df: pd.DataFrame) -> go.Figure:
    """df columns: name, state, start, end."""
    if df.empty:
        return _empty_fig("尚無含日期的專案")
    df = df.sort_values("start")
    fig = px.timeline(df, x_start="start", x_end="end", y="name", color="state",
                      color_discrete_map=STATE_COLORS,
                      hover_data=["sub_category", "vendor", "target_mp"])
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        title="專案時程 (GO Date → Target MP)",
        height=max(320, 30 * len(df) + 80),
        margin=dict(l=140, r=20, t=50, b=40),
    )
    return fig


def state_pie(df: pd.DataFrame) -> go.Figure:
    if df.empty or "state" not in df.columns:
        return _empty_fig("無 State 資料")
    counts = df["state"].fillna("Unknown").replace("", "Unknown").value_counts().reset_index()
    counts.columns = ["state", "count"]
    fig = px.pie(counts, names="state", values="count", color="state",
                 color_discrete_map=STATE_COLORS, hole=0.4)
    fig.update_layout(title="專案 State 分布", height=320,
                      margin=dict(l=20, r=20, t=50, b=20))
    return fig


def forecast_line(forecast: pd.DataFrame, current: pd.DataFrame, engineer: str) -> go.Figure:
    """forecast & current both have columns: ym, total_load."""
    if forecast.empty and current.empty:
        return _empty_fig("無資料")
    fig = go.Figure()
    if not current.empty:
        fig.add_trace(go.Scatter(x=current["ym"], y=current["total_load"],
                                  name="目前負載", mode="lines+markers",
                                  line=dict(color="#1f77b4")))
    if not forecast.empty:
        fig.add_trace(go.Scatter(x=forecast["ym"], y=forecast["total_load"],
                                  name="預測負載", mode="lines+markers",
                                  line=dict(color="#d62728", dash="dash")))
    fig.add_hline(y=1.0, line_dash="dash", line_color="red")
    fig.add_hline(y=0.8, line_dash="dot", line_color="orange")
    fig.update_layout(
        title=f"{engineer} 負載預測",
        height=380, yaxis_title="Total load",
        margin=dict(l=60, r=20, t=50, b=40),
    )
    return fig


def _empty_fig(text: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=text, x=0.5, y=0.5, xref="paper", yref="paper",
                       showarrow=False, font=dict(size=14, color="#888"))
    fig.update_layout(height=200, xaxis=dict(visible=False), yaxis=dict(visible=False),
                      margin=dict(l=20, r=20, t=20, b=20))
    return fig
