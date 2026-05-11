"""Read-only DB helpers for the Streamlit app."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

import pandas as pd

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "thermal.db"


def get_conn(db_path: Path = DB_PATH) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(f"DB not found at {db_path}. Run `python -m src.etl` first.")
    return sqlite3.connect(db_path)


def query(sql: str, params: Iterable | None = None, db_path: Path = DB_PATH) -> pd.DataFrame:
    with get_conn(db_path) as con:
        return pd.read_sql_query(sql, con, params=tuple(params) if params else None)


def list_engineers(db_path: Path = DB_PATH) -> list[str]:
    return query("SELECT name FROM engineers ORDER BY name", db_path=db_path)["name"].tolist()


def list_years(db_path: Path = DB_PATH) -> list[int]:
    return query("SELECT DISTINCT year FROM loadings ORDER BY year", db_path=db_path)["year"].tolist()


def list_categories(db_path: Path = DB_PATH) -> list[str]:
    return query(
        "SELECT DISTINCT category FROM loadings WHERE category IS NOT NULL ORDER BY category",
        db_path=db_path,
    )["category"].tolist()


def list_states(db_path: Path = DB_PATH) -> list[str]:
    return query(
        "SELECT DISTINCT state FROM projects WHERE state IS NOT NULL AND state <> '' ORDER BY state",
        db_path=db_path,
    )["state"].tolist()


def monthly_load(year: int, engineers: list[str] | None = None,
                  categories: list[str] | None = None, db_path: Path = DB_PATH) -> pd.DataFrame:
    """Long-format: engineer | month | total_load."""
    where = ["l.year = ?"]
    params: list = [year]
    if engineers:
        where.append("e.name IN (" + ",".join("?" * len(engineers)) + ")")
        params.extend(engineers)
    if categories:
        where.append("l.category IN (" + ",".join("?" * len(categories)) + ")")
        params.extend(categories)
    sql = f"""
        SELECT e.name AS engineer, l.month, SUM(l.load) AS total_load
        FROM loadings l JOIN engineers e ON e.id = l.engineer_id
        WHERE {' AND '.join(where)}
        GROUP BY e.name, l.month
        ORDER BY e.name, l.month
    """
    return query(sql, params, db_path=db_path)


def engineer_project_breakdown(year: int, engineer: str, db_path: Path = DB_PATH) -> pd.DataFrame:
    sql = """
        SELECT l.month, l.project_name, l.sub_category, l.category, l.load, l.block
        FROM loadings l JOIN engineers e ON e.id = l.engineer_id
        WHERE l.year = ? AND e.name = ?
        ORDER BY l.month, l.project_name
    """
    return query(sql, (year, engineer), db_path=db_path)


def projects_with_meta(db_path: Path = DB_PATH) -> pd.DataFrame:
    return query(
        """
        SELECT id, name, sub_category, vendor, state, go_date, target_mp,
               thermal_task, odm_jdm
        FROM projects ORDER BY go_date NULLS LAST, name
        """,
        db_path=db_path,
    )


def projects_for_gantt(db_path: Path = DB_PATH) -> pd.DataFrame:
    """Projects with parsed start/end suitable for Gantt rendering."""
    df = projects_with_meta(db_path=db_path)
    df = df[df["go_date"].notna()].copy()
    df["start"] = pd.to_datetime(df["go_date"], errors="coerce")
    df["end"] = df["target_mp"].apply(_parse_target_mp)
    df = df.dropna(subset=["start", "end"])
    df["state"] = df["state"].fillna("Unknown").replace("", "Unknown")
    return df


def _parse_target_mp(s) -> pd.Timestamp | None:
    """Parse strings like 'Q2-2026 (June)' or 'Q4-2026' into a Timestamp at quarter end."""
    if not isinstance(s, str) or not s.strip():
        return None
    import re
    m = re.search(r"Q([1-4])[-\s]*(\d{4})", s)
    if not m:
        return None
    q = int(m.group(1))
    y = int(m.group(2))
    end_month = q * 3
    end_day = {3: 31, 6: 30, 9: 30, 12: 31}[end_month]
    return pd.Timestamp(year=y, month=end_month, day=end_day)


def thermal_indicator(db_path: Path = DB_PATH) -> pd.DataFrame:
    return query("SELECT score, description, applies_to FROM thermal_indicator", db_path=db_path)


def overload_summary(year: int, threshold_high: float = 1.0, threshold_low: float = 0.3,
                      db_path: Path = DB_PATH) -> pd.DataFrame:
    """Per engineer-month total load with overload/idle flags."""
    df = monthly_load(year, db_path=db_path)
    df["status"] = "ok"
    df.loc[df["total_load"] > threshold_high, "status"] = "overload"
    df.loc[df["total_load"] < threshold_low, "status"] = "idle"
    return df


def safe_select(sql: str, db_path: Path = DB_PATH, limit: int = 1000) -> pd.DataFrame:
    """SELECT-only query gate used by the AI Q&A tool."""
    s = sql.strip().rstrip(";")
    lower = s.lower()
    if not lower.startswith("select") and not lower.startswith("with"):
        raise ValueError("Only SELECT/WITH queries are allowed.")
    forbidden = ["insert ", "update ", "delete ", "drop ", "alter ", "attach ", "pragma ", "create "]
    if any(tok in lower for tok in forbidden):
        raise ValueError("Forbidden keyword detected in query.")
    if " limit " not in lower:
        s = f"{s} LIMIT {limit}"
    return query(s, db_path=db_path)


SCHEMA_DESCRIPTION = """
Tables:

engineers(id, name)
  - name examples: 'Sam Kuan', 'Vincent Chen', 'Unassigned (Vision)'

projects(id, name, sub_category, vendor, state, go_date, target_mp, thermal_task, odm_jdm)
  - state: PA1, PB1, PQR, RFQ, Engineering Response, TBD
  - go_date: ISO date (YYYY-MM-DD)
  - target_mp: free text like 'Q2-2026 (June)'

loadings(id, engineer_id, project_id, category, year, month, block, load,
         project_name, sub_category, vendor, source_sheet)
  - category examples: B2B, L4B Vision Project Planning, Techno Bricks, PWS
  - month: 1-12
  - block: 1 or 2 (some sheets have two Jan-Dec blocks; block 1 may be carry-over or planning,
           block 2 is current execution. For simple totals just SUM(load).)
  - load: 0.1-0.4 per Thermal loading Indicator scoring scale.
  - project_name / sub_category / vendor are denormalised copies for fast filtering.

thermal_indicator(score, description, applies_to)
  - dictionary explaining what each load score means.

Common joins:
  loadings l JOIN engineers e ON e.id = l.engineer_id
  loadings l LEFT JOIN projects p ON p.id = l.project_id
""".strip()
