"""Excel -> SQLite ETL for Logi Thermal Resource Dashboard.

Handles two sheet schemas:
- Pre-2025 (28 cols): Category | Project | Engineer | Vendor | Jan..Dec | Jan..Dec
- 2025+ (29 cols):    Category | Project | Sub-Category | Engineer | Vendor | Jan..Dec | Jan..Dec

For 2022, row 1 is a year-band header (2021 / 2022) and row 2 holds month names.
For other year sheets, row 1 holds the column header.

Vision-planning rows have an empty engineer; we keep them under "Unassigned (Vision)".
Subtotal rows (no project AND no engineer) are dropped.
"""
from __future__ import annotations

import argparse
import sqlite3
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
EXCEL_PATH = ROOT / "Logi Thermal Resource Dashboard.xlsx"
DB_PATH = ROOT / "data" / "thermal.db"

YEAR_SHEETS = ["2022", "2023", "2024", "2025", "2026"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
UNASSIGNED = "Unassigned (Vision)"


def excel_serial_to_date(serial) -> str | None:
    if serial is None or pd.isna(serial):
        return None
    if isinstance(serial, pd.Timestamp):
        return serial.date().isoformat()
    if hasattr(serial, "isoformat"):
        try:
            return serial.date().isoformat() if hasattr(serial, "date") else serial.isoformat()
        except Exception:
            pass
    try:
        s = float(serial)
    except (TypeError, ValueError):
        return None
    return (date(1899, 12, 30) + timedelta(days=int(s))).isoformat()


def _coerce_load(v) -> float | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    try:
        return float(s)
    except ValueError:
        return None


def _str(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip()


def _detect_schema(raw: pd.DataFrame, sheet_name: str) -> dict:
    """Find header row and column indices.

    Returns dict with: header_row, col_category, col_project, col_sub (or None),
    col_engineer, col_vendor, block1_start, block2_start, block1_year, block2_year.
    """
    # Search first 3 rows for a header containing 'Project' and 'Engineer' and 'Jan'
    header_row = None
    for r in range(min(3, len(raw))):
        cells = [_str(raw.iloc[r, c]).lower() for c in range(min(raw.shape[1], 30))]
        if "project" in cells and "engineer" in cells and "jan" in cells:
            header_row = r
            break
    if header_row is None:
        raise ValueError(f"Could not detect header row in sheet {sheet_name}")

    headers = [_str(raw.iloc[header_row, c]) for c in range(raw.shape[1])]
    lower = [h.lower() for h in headers]

    col_project = lower.index("project")
    col_engineer = lower.index("engineer")
    col_vendor = lower.index("vendor")
    col_sub = lower.index("category") if "category" in lower else None
    # First "Jan" position after vendor
    jan_positions = [i for i, h in enumerate(lower) if h == "jan"]
    if not jan_positions:
        raise ValueError(f"No Jan column found in sheet {sheet_name}")
    block1_start = jan_positions[0]
    block2_start = jan_positions[1] if len(jan_positions) > 1 else None
    col_category = 0  # always col A

    # Determine block years. Default: block1 = sheet year, block2 = sheet year + 1.
    # 2022 has explicit "2021" / "2022" header band on row 0 → use that.
    sheet_year = int(sheet_name)
    block1_year = sheet_year
    block2_year = sheet_year + 1
    if header_row >= 1:
        band = raw.iloc[header_row - 1]
        v1 = _coerce_load(band.iloc[block1_start]) if block1_start < len(band) else None
        v2 = _coerce_load(band.iloc[block2_start]) if block2_start and block2_start < len(band) else None
        if v1 and 1990 < v1 < 2100:
            block1_year = int(v1)
        if v2 and 1990 < v2 < 2100:
            block2_year = int(v2)

    return {
        "header_row": header_row,
        "col_category": col_category,
        "col_project": col_project,
        "col_sub": col_sub,
        "col_engineer": col_engineer,
        "col_vendor": col_vendor,
        "block1_start": block1_start,
        "block2_start": block2_start,
        "block1_year": block1_year,
        "block2_year": block2_year,
    }


def parse_year_sheet(xl: pd.ExcelFile, sheet_name: str) -> pd.DataFrame:
    raw = xl.parse(sheet_name, header=None)
    schema = _detect_schema(raw, sheet_name)
    records = []
    current_category = None

    for idx in range(schema["header_row"] + 1, len(raw)):
        row = raw.iloc[idx]
        cat = _str(row.iloc[schema["col_category"]])
        proj = _str(row.iloc[schema["col_project"]])
        sub = _str(row.iloc[schema["col_sub"]]) if schema["col_sub"] is not None else ""
        eng = _str(row.iloc[schema["col_engineer"]])
        vendor = _str(row.iloc[schema["col_vendor"]])

        if cat:
            current_category = cat

        # Drop subtotal rows: empty project AND empty engineer.
        if not proj and not eng:
            continue

        engineer_label = eng if eng else UNASSIGNED

        for block, start, year in (
            (1, schema["block1_start"], schema["block1_year"]),
            (2, schema["block2_start"], schema["block2_year"]),
        ):
            if start is None:
                continue
            for m_idx, _month in enumerate(MONTHS):
                col = start + m_idx
                if col >= raw.shape[1]:
                    break
                load = _coerce_load(row.iloc[col])
                if load is None or load == 0:
                    continue
                records.append({
                    "year": year,
                    "month": m_idx + 1,
                    "block": block,
                    "category": current_category,
                    "project": proj or UNASSIGNED,
                    "sub_category": sub,
                    "engineer": engineer_label,
                    "vendor": vendor,
                    "load": load,
                    "source_sheet": sheet_name,
                })
    return pd.DataFrame(records)


def parse_projects_sheet(xl: pd.ExcelFile) -> pd.DataFrame:
    raw = xl.parse("Sheet14", header=0)
    raw = raw.rename(columns=lambda c: str(c).strip())
    rename = {
        "Project": "name",
        "Category": "sub_category",
        "ODM / JDM": "odm_jdm",
        "State": "state",
        "Thermal Task": "thermal_task",
        "GO Date": "go_date_serial",
        "Target MP Date": "target_mp",
    }
    cols = {k: v for k, v in rename.items() if k in raw.columns}
    df = raw[list(cols.keys())].rename(columns=cols)
    df = df.dropna(how="all")
    df = df[df["name"].notna() & df["name"].astype(str).str.strip().ne("")]
    df["go_date"] = df["go_date_serial"].apply(excel_serial_to_date)
    for col in ("name", "sub_category", "odm_jdm", "state", "thermal_task", "target_mp"):
        if col in df.columns:
            df[col] = df[col].apply(lambda x: str(x).strip() if isinstance(x, str) else x)
    return df.drop(columns=["go_date_serial"])


def parse_indicator_sheet(xl: pd.ExcelFile) -> pd.DataFrame:
    raw = xl.parse("Thermal loading Indicator", header=None)
    rows = []
    for idx in range(2, len(raw)):
        score = raw.iloc[idx, 0]
        desc = raw.iloc[idx, 1]
        remark = raw.iloc[idx, 2] if raw.shape[1] > 2 else None
        if pd.isna(score):
            continue
        rows.append({
            "score": str(score).strip(),
            "description": str(desc).strip() if isinstance(desc, str) else "",
            "applies_to": str(remark).strip() if isinstance(remark, str) else "",
        })
    return pd.DataFrame(rows)


def write_to_sqlite(loadings: pd.DataFrame, projects: pd.DataFrame, indicator: pd.DataFrame, db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys = ON")
    cur = con.cursor()
    cur.executescript("""
    CREATE TABLE engineers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );
    CREATE TABLE projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        sub_category TEXT,
        vendor TEXT,
        state TEXT,
        go_date TEXT,
        target_mp TEXT,
        thermal_task TEXT,
        odm_jdm TEXT,
        UNIQUE(name, sub_category)
    );
    CREATE TABLE loadings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        engineer_id INTEGER NOT NULL REFERENCES engineers(id),
        project_id INTEGER REFERENCES projects(id),
        category TEXT,
        year INTEGER NOT NULL,
        month INTEGER NOT NULL,
        block INTEGER NOT NULL,
        load REAL NOT NULL,
        project_name TEXT,
        sub_category TEXT,
        vendor TEXT,
        source_sheet TEXT
    );
    CREATE TABLE thermal_indicator (
        score TEXT,
        description TEXT,
        applies_to TEXT
    );
    CREATE INDEX idx_loadings_year_month ON loadings(year, month);
    CREATE INDEX idx_loadings_engineer ON loadings(engineer_id);
    """)

    engineers = sorted(loadings["engineer"].dropna().unique().tolist())
    cur.executemany("INSERT INTO engineers(name) VALUES(?)", [(e,) for e in engineers])
    eng_map = dict(cur.execute("SELECT name, id FROM engineers").fetchall())

    proj_rows = []
    seen = set()
    for _, r in projects.iterrows():
        key = (r["name"], r.get("sub_category") or "")
        if key in seen:
            continue
        seen.add(key)
        proj_rows.append((
            r["name"], r.get("sub_category"), None,
            r.get("state"), r.get("go_date"), r.get("target_mp"),
            r.get("thermal_task"), r.get("odm_jdm"),
        ))
    load_keys = loadings[["project", "sub_category", "vendor"]].drop_duplicates()
    for _, r in load_keys.iterrows():
        key = (r["project"], r["sub_category"] or "")
        if key in seen:
            continue
        seen.add(key)
        proj_rows.append((r["project"], r["sub_category"], r["vendor"], None, None, None, None, None))

    cur.executemany("""
        INSERT INTO projects(name, sub_category, vendor, state, go_date, target_mp, thermal_task, odm_jdm)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?)
    """, proj_rows)
    proj_map = {(n, s or ""): pid for n, s, pid in cur.execute("SELECT name, sub_category, id FROM projects")}

    load_rows = []
    for _, r in loadings.iterrows():
        eng_id = eng_map.get(r["engineer"])
        if eng_id is None:
            continue
        pid = proj_map.get((r["project"], r["sub_category"] or ""))
        load_rows.append((
            eng_id, pid, r["category"], int(r["year"]), int(r["month"]), int(r["block"]), float(r["load"]),
            r["project"], r["sub_category"], r["vendor"], r["source_sheet"],
        ))
    cur.executemany("""
        INSERT INTO loadings(engineer_id, project_id, category, year, month, block, load,
                             project_name, sub_category, vendor, source_sheet)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, load_rows)

    cur.executemany(
        "INSERT INTO thermal_indicator(score, description, applies_to) VALUES(?, ?, ?)",
        [(r["score"], r["description"], r["applies_to"]) for _, r in indicator.iterrows()],
    )

    con.commit()
    con.close()


def run(excel_path: Path = EXCEL_PATH, db_path: Path = DB_PATH, verbose: bool = False) -> dict:
    if not excel_path.exists():
        raise FileNotFoundError(f"Excel not found: {excel_path}")
    xl = pd.ExcelFile(excel_path)

    all_loadings = []
    for sheet in YEAR_SHEETS:
        if sheet not in xl.sheet_names:
            continue
        df = parse_year_sheet(xl, sheet)
        if not df.empty:
            all_loadings.append(df)
    loadings = pd.concat(all_loadings, ignore_index=True) if all_loadings else pd.DataFrame()

    projects = parse_projects_sheet(xl)
    indicator = parse_indicator_sheet(xl)

    write_to_sqlite(loadings, projects, indicator, db_path)

    summary = {
        "loadings_rows": len(loadings),
        "projects_rows": len(projects),
        "indicator_rows": len(indicator),
        "engineers": sorted(loadings["engineer"].dropna().unique().tolist()),
        "categories": sorted(loadings["category"].dropna().unique().tolist()),
        "years": sorted(loadings["year"].dropna().unique().astype(int).tolist()) if len(loadings) else [],
        "db_path": str(db_path),
    }
    if verbose:
        print("ETL summary:")
        for k, v in summary.items():
            print(f"  {k}: {v}")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    run(verbose=True)
