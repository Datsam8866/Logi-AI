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

RISK_COLORS = {
    "overload": "#EF4444",
    "warning":  "#F59E0B",
    "healthy":  "#22C55E",
    "idle":     "#3B82F6",
    "neutral":  "#9CA3AF",
}


def heatmap_engineer_month(monthly: pd.DataFrame, year: int) -> go.Figure:
    """monthly columns: engineer, month, total_load."""
    if monthly.empty:
        return _empty_fig(f"{year} 無資料")
    pivot = monthly.pivot(index="engineer", columns="month", values="total_load").fillna(0)
    pivot = pivot.reindex(columns=range(1, 13), fill_value=0)

    # 4-zone risk colorscale mapped to zmin=0, zmax=1.5
    colorscale = [
        [0.000, "#EFF6FF"],  # 0.0  → near-zero / white-blue
        [0.200, "#22C55E"],  # 0.3  → healthy green
        [0.533, "#F59E0B"],  # 0.8  → warning amber
        [0.667, "#EF4444"],  # 1.0  → overload red
        [1.000, "#7F1D1D"],  # 1.5+ → critical dark red
    ]

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=MONTH_LABELS,
        y=pivot.index.tolist(),
        colorscale=colorscale,
        zmin=0, zmax=1.5,
        colorbar=dict(
            title="負載",
            tickvals=[0, 0.3, 0.8, 1.0, 1.5],
            ticktext=["0", "0.3 閒置", "0.8 警戒", "1.0 滿載", "1.5+"],
        ),
        text=pivot.values,
        texttemplate="%{text:.1f}",
        hovertemplate="%{y} | %{x} | load=%{z:.2f}<extra></extra>",
    ))

    # Annotate the single highest-load cell
    max_val = float(pivot.values.max())
    if max_val >= 0.8:
        flat_idx = int(pivot.values.argmax())
        row_idx, col_idx = divmod(flat_idx, pivot.shape[1])
        fig.add_annotation(
            x=MONTH_LABELS[col_idx],
            y=pivot.index[row_idx],
            text=f"▲{max_val:.2f}",
            showarrow=False,
            font=dict(size=9, color="white"),
            yshift=8,
        )

    fig.update_layout(
        title=f"{year} 工程師月度負載（紅 > 1.0 過載 ／ 橘 ≥ 0.8 警戒）",
        height=max(280, 42 * len(pivot) + 100),
        margin=dict(l=80, r=20, t=50, b=40),
    )
    return fig


def peak_load_bar(monthly: pd.DataFrame) -> go.Figure:
    """Horizontal bar: each engineer's peak (max monthly) load, sorted descending."""
    if monthly.empty:
        return _empty_fig("無資料")
    peak = (
        monthly.groupby("engineer")["total_load"]
        .max()
        .reset_index()
        .rename(columns={"total_load": "peak_load"})
        .sort_values("peak_load", ascending=True)  # ascending → highest at top in h-bar
    )
    peak["margin"] = (1.0 - peak["peak_load"]).round(2)
    peak["color"] = peak["peak_load"].apply(
        lambda v: RISK_COLORS["overload"] if v > 1.0
        else RISK_COLORS["warning"] if v >= 0.8
        else RISK_COLORS["healthy"]
    )
    peak["label"] = peak["margin"].apply(
        lambda m: f"超載 {-m:.2f}" if m < 0 else f"餘 {m:.2f}"
    )

    fig = go.Figure(go.Bar(
        y=peak["engineer"],
        x=peak["peak_load"],
        orientation="h",
        marker_color=peak["color"].tolist(),
        text=peak["label"],
        textposition="outside",
        hovertemplate="%{y}: 峰值=%{x:.2f}<extra></extra>",
    ))
    fig.add_vline(x=1.0, line_dash="dash", line_color=RISK_COLORS["overload"],
                  annotation_text="滿載 1.0", annotation_position="top right")
    fig.add_vline(x=0.8, line_dash="dot", line_color=RISK_COLORS["warning"])

    max_x = max(1.6, float(peak["peak_load"].max()) + 0.25)
    fig.update_layout(
        title="工程師年度峰值負載",
        xaxis=dict(title="Peak Load", range=[0, max_x]),
        height=max(200, 40 * len(peak) + 80),
        margin=dict(l=100, r=90, t=50, b=40),
    )
    return fig


def state_bar(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar: project state counts, sorted by count (replaces pie)."""
    if df.empty or "state" not in df.columns:
        return _empty_fig("無 State 資料")
    counts = (
        df["state"].fillna("Unknown").replace("", "Unknown")
        .value_counts()
        .reset_index()
    )
    counts.columns = ["state", "count"]
    counts = counts.sort_values("count", ascending=True)
    colors = [STATE_COLORS.get(s, "#9E9E9E") for s in counts["state"]]

    fig = go.Figure(go.Bar(
        y=counts["state"],
        x=counts["count"],
        orientation="h",
        marker_color=colors,
        text=counts["count"],
        textposition="outside",
        hovertemplate="%{y}: %{x} 個<extra></extra>",
    ))
    fig.update_layout(
        title="專案 State 分布",
        xaxis_title="專案數",
        height=max(200, 40 * len(counts) + 80),
        margin=dict(l=140, r=50, t=50, b=40),
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
    fig.add_hline(y=1.0, line_dash="dash", line_color=RISK_COLORS["overload"],
                  annotation_text="過載 1.0", annotation_position="top right")
    fig.add_hline(y=0.8, line_dash="dot", line_color=RISK_COLORS["warning"],
                  annotation_text="警戒 0.8", annotation_position="top left")
    fig.update_layout(
        title=f"{engineer} {year} 月度負載分解",
        height=420, barmode="stack",
        margin=dict(l=60, r=20, t=50, b=40),
    )
    return fig


def gantt_projects(df: pd.DataFrame) -> go.Figure:
    """df columns: name, state, start, end."""
    if df.empty:
        return _empty_fig("尚無含日期的專案")
    df = df.sort_values("start")
    hover_cols = [c for c in ["sub_category", "vendor", "target_mp"] if c in df.columns]
    y_col = "Project" if "Project" in df.columns else "name"
    fig = px.timeline(df, x_start="start", x_end="end", y=y_col, color="state",
                      color_discrete_map=STATE_COLORS,
                      hover_data=hover_cols or None)
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        title="專案時程 (GO Date → Target MP)",
        height=max(320, 30 * len(df) + 80),
        margin=dict(l=140, r=20, t=50, b=40),
    )
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
                                  line=dict(color=RISK_COLORS["overload"], dash="dash")))
    fig.add_hline(y=1.0, line_dash="dash", line_color=RISK_COLORS["overload"],
                  annotation_text="過載 1.0", annotation_position="top right")
    fig.add_hline(y=0.8, line_dash="dot", line_color=RISK_COLORS["warning"],
                  annotation_text="警戒 0.8", annotation_position="top left")
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
