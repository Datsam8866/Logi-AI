"""Load forecasting based on project state typical curves."""
from __future__ import annotations

import calendar
from datetime import date

import pandas as pd

from src.db import engineer_project_breakdown, monthly_load, projects_with_meta

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Typical monthly load per state (relative to 1.0 = full-time thermal).
# Shape: list of 12 values representing month 1..12 from project GO date.
STATE_CURVES: dict[str, list[float]] = {
    "PA1": [0.3, 0.4, 0.4, 0.3, 0.2, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "PB1": [0.2, 0.3, 0.3, 0.3, 0.3, 0.2, 0.2, 0.1, 0.0, 0.0, 0.0, 0.0],
    "PQR": [0.1, 0.1, 0.2, 0.2, 0.1, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "RFQ": [0.1, 0.1, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "Engineering Response": [0.2, 0.2, 0.3, 0.3, 0.2, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "TBD": [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
}
DEFAULT_CURVE = [0.1] * 6 + [0.0] * 6


def _ym(y: int, m: int) -> str:
    return f"{y}-{m:02d}"


def current_load_series(engineer: str, year: int) -> pd.DataFrame:
    """Return ym | total_load for existing data."""
    df = monthly_load(year, engineers=[engineer])
    df = df[df["engineer"] == engineer].copy()
    df["ym"] = df.apply(lambda r: _ym(int(year), int(r["month"])), axis=1)
    return df[["ym", "total_load"]].sort_values("ym")


def forecast_load(engineer: str, from_year: int, months_ahead: int = 6) -> pd.DataFrame:
    """Project future load from unfinished projects onto the next N months.

    Returns DataFrame: ym | total_load
    """
    today = date.today()
    start_ym = _ym(today.year, today.month)

    # Collect projects not yet done (those with go_date set)
    projects = projects_with_meta()
    projects = projects[projects["go_date"].notna() & projects["state"].notna()].copy()
    projects["go_date"] = pd.to_datetime(projects["go_date"], errors="coerce")
    projects = projects.dropna(subset=["go_date"])

    load_map: dict[str, float] = {}

    for _, proj in projects.iterrows():
        curve = STATE_CURVES.get(str(proj["state"]), DEFAULT_CURVE)
        go = proj["go_date"]
        for offset, load in enumerate(curve):
            if load == 0:
                continue
            m = go.month + offset
            y = go.year + (m - 1) // 12
            m = ((m - 1) % 12) + 1
            ym = _ym(y, m)
            if ym < start_ym:
                continue
            load_map[ym] = load_map.get(ym, 0.0) + load

    if not load_map:
        return pd.DataFrame(columns=["ym", "total_load"])

    rows = [{"ym": ym, "total_load": v} for ym, v in sorted(load_map.items())]
    df = pd.DataFrame(rows)
    # Trim to months_ahead from today
    cutoff = _ym(today.year + (today.month + months_ahead - 1) // 12,
                 ((today.month + months_ahead - 1) % 12) + 1)
    df = df[df["ym"] <= cutoff]
    return df
