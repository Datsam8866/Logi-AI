"""Load forecasting based on project state typical curves."""
from __future__ import annotations

from datetime import date

import pandas as pd

from src.db import monthly_load, projects_with_meta

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Typical monthly load profile per state (12 values: month 1..12 from GO date).
STATE_CURVES: dict[str, list[float]] = {
    "PA1": [0.3, 0.4, 0.4, 0.3, 0.2, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "PB1": [0.2, 0.3, 0.3, 0.3, 0.3, 0.2, 0.2, 0.1, 0.0, 0.0, 0.0, 0.0],
    "PQR": [0.1, 0.1, 0.2, 0.2, 0.1, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "RFQ": [0.1, 0.1, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "Engineering Response": [0.2, 0.2, 0.3, 0.3, 0.2, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "TBD": [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
}
DEFAULT_CURVE = [0.1] * 4 + [0.0] * 8


def _ym(y: int, m: int) -> str:
    return f"{y}-{m:02d}"


def _add_months(y: int, m: int, delta: int) -> tuple[int, int]:
    m += delta
    y += (m - 1) // 12
    m = ((m - 1) % 12) + 1
    return y, m


def current_load_series(engineer: str, year: int) -> pd.DataFrame:
    """Return ym | total_load for existing DB data."""
    df = monthly_load(year, engineers=[engineer])
    if df.empty:
        return pd.DataFrame(columns=["ym", "total_load"])
    df = df[df["engineer"] == engineer].copy()
    df["ym"] = df.apply(lambda r: _ym(int(year), int(r["month"])), axis=1)
    return df[["ym", "total_load"]].sort_values("ym").reset_index(drop=True)


def forecast_load(engineer: str, from_year: int, months_ahead: int = 6) -> pd.DataFrame:
    """Project future load for the next N months from today using active projects.

    Strategy: for each project whose target_mp is still in the future (or unknown),
    apply the STATE_CURVE starting from TODAY (or from go_date if it's in the future).
    This gives a forward-looking view regardless of when GO Date was.
    """
    today = date.today()
    today_ym = _ym(today.year, today.month)

    projects = projects_with_meta()
    projects = projects[projects["state"].notna() & projects["state"].ne("")].copy()
    projects["go_date"] = pd.to_datetime(projects["go_date"], errors="coerce")

    # Determine project end from target_mp or assign a generous default
    def _end_ym(row) -> str:
        mp = str(row.get("target_mp") or "")
        import re
        m = re.search(r"Q([1-4])[-\s]*(\d{4})", mp)
        if m:
            q, y = int(m.group(1)), int(m.group(2))
            end_month = q * 3
            return _ym(y, end_month)
        # Default: 12 months from go_date or from today
        if pd.notna(row.get("go_date")):
            y, mo = _add_months(row["go_date"].year, row["go_date"].month, 12)
        else:
            y, mo = _add_months(today.year, today.month, 12)
        return _ym(y, mo)

    projects["end_ym"] = projects.apply(_end_ym, axis=1)

    # Keep only projects still active (end in the future)
    active = projects[projects["end_ym"] >= today_ym]
    if active.empty:
        return pd.DataFrame(columns=["ym", "total_load"])

    load_map: dict[str, float] = {}
    cutoff_y, cutoff_m = _add_months(today.year, today.month, months_ahead)
    cutoff_ym = _ym(cutoff_y, cutoff_m)

    for _, proj in active.iterrows():
        curve = STATE_CURVES.get(str(proj["state"]), DEFAULT_CURVE)
        # Start applying curve from today (not from go_date)
        for offset, load in enumerate(curve):
            if load == 0:
                continue
            y, m = _add_months(today.year, today.month, offset)
            ym = _ym(y, m)
            if ym > cutoff_ym:
                break
            if ym > proj["end_ym"]:
                break
            load_map[ym] = load_map.get(ym, 0.0) + load

    if not load_map:
        return pd.DataFrame(columns=["ym", "total_load"])

    rows = [{"ym": ym, "total_load": v} for ym, v in sorted(load_map.items())]
    return pd.DataFrame(rows)
