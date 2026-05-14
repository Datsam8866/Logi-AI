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
        SELECT l.id, l.month, l.project_name, l.sub_category, l.category, l.load, l.block
        FROM loadings l JOIN engineers e ON e.id = l.engineer_id
        WHERE l.year = ? AND e.name = ?
        ORDER BY l.month, l.project_name
    """
    return query(sql, (year, engineer), db_path=db_path)


def list_columns(table: str, db_path: Path = DB_PATH) -> list[str]:
    """Return all column names for a table."""
    with get_conn(db_path) as con:
        rows = con.execute(f"PRAGMA table_info({table})").fetchall()
    return [r[1] for r in rows]


def add_column(table: str, col_name: str, col_type: str = "TEXT", db_path: Path = DB_PATH) -> None:
    """Add a new column to a table (ALTER TABLE ADD COLUMN)."""
    with sqlite3.connect(db_path) as con:
        con.execute(f'ALTER TABLE {table} ADD COLUMN "{col_name}" {col_type}')
        con.commit()


def drop_column(table: str, col_name: str, db_path: Path = DB_PATH) -> None:
    """Drop a column. Falls back to full table rebuild if ALTER TABLE is blocked by constraints."""
    with sqlite3.connect(db_path) as con:
        try:
            con.execute(f'ALTER TABLE "{table}" DROP COLUMN "{col_name}"')
            con.commit()
            return
        except Exception:
            pass  # column may be part of a UNIQUE/INDEX — rebuild instead

        # Rebuild table without the column (drops all constraints referencing it)
        info = con.execute(f'PRAGMA table_info("{table}")').fetchall()
        keep = [r[1] for r in info if r[1] != col_name]
        if not keep:
            raise ValueError(f"Cannot drop all columns from {table}")
        col_defs = []
        for _, name, typ, notnull, dflt, pk in info:
            if name == col_name:
                continue
            part = f'"{name}" {typ or "TEXT"}'
            if pk:
                part += " PRIMARY KEY AUTOINCREMENT"
            elif notnull:
                part += " NOT NULL"
            if dflt is not None and not pk:
                part += f" DEFAULT {dflt}"
            col_defs.append(part)
        sel = ", ".join(f'"{c}"' for c in keep)
        tmp = f"_rebuild_{table}"
        con.execute(f'CREATE TABLE "{tmp}" ({", ".join(col_defs)})')
        con.execute(f'INSERT INTO "{tmp}" ({sel}) SELECT {sel} FROM "{table}"')
        con.execute(f'DROP TABLE "{table}"')
        con.execute(f'ALTER TABLE "{tmp}" RENAME TO "{table}"')
        con.commit()


def rename_column(table: str, old_name: str, new_name: str, db_path: Path = DB_PATH) -> None:
    """Rename a column (requires SQLite >= 3.25)."""
    with sqlite3.connect(db_path) as con:
        con.execute(f'ALTER TABLE {table} RENAME COLUMN "{old_name}" TO "{new_name}"')
        con.commit()


def projects_all_columns(db_path: Path = DB_PATH) -> pd.DataFrame:
    """Return all project rows with every column (dynamic schema)."""
    return query("SELECT * FROM projects ORDER BY display_order NULLS LAST, go_date NULLS LAST", db_path=db_path)


def insert_project(row: dict, db_path: Path = DB_PATH) -> int:
    """Insert a new project. Returns new id."""
    import math
    cols = [c for c in row if c != "id"
            and row[c] is not None
            and not (isinstance(row[c], float) and math.isnan(row[c]))
            and str(row[c]) != ""]
    if not cols:
        return 0
    ph = ",".join("?" * len(cols))
    col_str = ",".join(f'"{c}"' for c in cols)
    vals = [row[c] for c in cols]
    with sqlite3.connect(db_path) as con:
        cur = con.execute(
            f"INSERT INTO projects ({col_str}) VALUES ({ph})", vals
        )
        con.commit()
        return cur.lastrowid


def delete_projects(ids: list[int], db_path: Path = DB_PATH) -> int:
    """Delete projects and their loadings."""
    if not ids:
        return 0
    ph = ",".join("?" * len(ids))
    with sqlite3.connect(db_path) as con:
        con.execute(f"DELETE FROM loadings WHERE project_id IN ({ph})", ids)
        cur = con.execute(f"DELETE FROM projects WHERE id IN ({ph})", ids)
        con.commit()
        return cur.rowcount


def insert_loading(engineer_name: str, year: int, month: int, project_name: str,
                   load: float, block: int = 1, db_path: Path = DB_PATH) -> int:
    """Insert a new loading row. Returns new id."""
    with sqlite3.connect(db_path) as con:
        row = con.execute("SELECT id FROM engineers WHERE name=?", (engineer_name,)).fetchone()
        engineer_id = row[0] if row else None

        # Detect the project name column (may have been renamed from 'name' to 'Project')
        proj_cols = [r[1] for r in con.execute("PRAGMA table_info(projects)").fetchall()]
        name_col = "Project" if "Project" in proj_cols else "name"
        want = ["id"]
        if "sub_category" in proj_cols:
            want.append("sub_category")
        if "vendor" in proj_cols:
            want.append("vendor")
        sel = ", ".join(f'"{c}"' for c in want)
        prow = con.execute(f'SELECT {sel} FROM projects WHERE "{name_col}"=?',
                           (project_name,)).fetchone()
        project_id = prow[0] if prow else None
        sub_cat = prow[want.index("sub_category")] if prow and "sub_category" in want else None
        vendor = prow[want.index("vendor")] if prow and "vendor" in want else None

        cur = con.execute(
            """INSERT INTO loadings
               (engineer_id, project_id, category, year, month, block, load,
                project_name, sub_category, vendor, source_sheet)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (engineer_id, project_id, "", year, month, block, load,
             project_name, sub_cat, vendor, "manual"),
        )
        con.commit()
        return cur.lastrowid


def delete_loadings(ids: list[int], db_path: Path = DB_PATH) -> int:
    """Delete loading rows by id list."""
    if not ids:
        return 0
    ph = ",".join("?" * len(ids))
    with sqlite3.connect(db_path) as con:
        cur = con.execute(f"DELETE FROM loadings WHERE id IN ({ph})", ids)
        con.commit()
        return cur.rowcount


def save_projects(df: pd.DataFrame, db_path: Path = DB_PATH) -> int:
    """Update project rows for all non-id columns present in df."""
    cols = [c for c in df.columns if c != "id"]
    rows = 0
    with sqlite3.connect(db_path) as con:
        for _, row in df.iterrows():
            if not cols:
                continue
            sets = ", ".join(f'"{c}"=?' for c in cols)
            vals = [row.get(c) for c in cols] + [int(row["id"])]
            con.execute(f"UPDATE projects SET {sets} WHERE id=?", vals)
            rows += 1
        con.commit()
    return rows


def save_loadings(df: pd.DataFrame, db_path: Path = DB_PATH) -> int:
    """Update load values from a data_editor DataFrame (must contain id and load columns)."""
    rows = 0
    with sqlite3.connect(db_path) as con:
        for _, row in df.iterrows():
            con.execute("UPDATE loadings SET load=? WHERE id=?",
                        (float(row["load"]), int(row["id"])))
            rows += 1
        con.commit()
    return rows


def projects_with_meta(db_path: Path = DB_PATH) -> pd.DataFrame:
    return query(
        "SELECT * FROM projects ORDER BY display_order NULLS LAST, go_date NULLS LAST",
        db_path=db_path,
    )


def projects_for_gantt(db_path: Path = DB_PATH) -> pd.DataFrame:
    """Projects with parsed start/end suitable for Gantt rendering."""
    df = projects_with_meta(db_path=db_path)
    if "go_date" not in df.columns:
        return pd.DataFrame()
    df = df[df["go_date"].notna()].copy()
    df["start"] = pd.to_datetime(df["go_date"], errors="coerce")
    target_mp_series = df["target_mp"] if "target_mp" in df.columns else pd.Series([None] * len(df))
    df["end"] = target_mp_series.apply(_parse_target_mp)
    df = df.dropna(subset=["start", "end"])
    df["state"] = df["state"].fillna("Unknown").replace("", "Unknown") if "state" in df.columns else "Unknown"
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
