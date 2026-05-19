import openpyxl
import sqlite3
import re
from datetime import datetime

EXCEL_PATH = r"C:\Users\skuan1\Desktop\Logi AI\Logi-MEBudget\FY27_ME_Budget.xlsx"
DB_PATH    = r"C:\Users\skuan1\Desktop\Logi AI\Logi-MEBudget\me_budget.db"

SHEETS = ["ME_Q1", "ME_Q2", "ME_Q3", "ME_Q4"]


def parse_budget(val):
    """'$20,000' -> 20000.0, 0/''/'-'/'#VALUE!' -> None"""
    if val is None or val == "-" or str(val).strip() in ("", "#VALUE!"):
        return None
    if isinstance(val, (int, float)):
        return float(val) if val != 0 else None
    s = re.sub(r"[$,\s]", "", str(val))
    try:
        return float(s)
    except ValueError:
        return None


def parse_num(val):
    """Convert numeric / '-' / '#VALUE!' cell to float or None."""
    if val is None or val == "-" or str(val).strip() in ("", "#VALUE!"):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    try:
        return float(val)
    except ValueError:
        return None


def to_date(val):
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d")
    if isinstance(val, str) and val.strip():
        return val.strip()
    return None


def create_tables(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS budget_overview (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        quarter             TEXT NOT NULL,
        budget_code         INTEGER,
        type                TEXT,
        category            TEXT,
        category_content    TEXT,
        budget_usd          REAL,
        will_pr             REAL,
        done_pr             REAL,
        will_expensify      REAL,
        done_expensify      REAL,
        remaining           REAL
    );

    CREATE TABLE IF NOT EXISTS transactions (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        quarter             TEXT NOT NULL,
        dept_manager        TEXT,
        buyer_name          TEXT,
        budget_code         INTEGER,
        manager_confirmed   TEXT,
        item                TEXT,
        cost_original       REAL,
        currency            TEXT,
        cost_usd            REAL,
        project             TEXT,
        supplier            TEXT,
        quotation           TEXT,
        type                TEXT,
        purchase_plan       TEXT,
        pr_expensify_date   TEXT,
        pr_expensify_no     TEXT,
        po_no               TEXT,
        received            TEXT,
        date_of_receiving   TEXT
    );
    """)
    conn.commit()


def import_sheet(ws, quarter, conn):
    overview_rows = []
    tx_rows = []

    for row in ws.iter_rows(min_row=4, values_only=True):
        r = list(row)

        # --- transactions (left side, col B-S = index 1-18) ---
        buyer = r[2] if len(r) > 2 else None
        item  = r[5] if len(r) > 5 else None
        if buyer or item:
            tx_rows.append((
                quarter,
                r[1],               # dept_manager
                r[2],               # buyer_name
                int(r[3]) if isinstance(r[3], float) else r[3],  # budget_code
                r[4],               # manager_confirmed
                r[5],               # item
                parse_num(r[6]),    # cost_original
                r[7],               # currency
                parse_num(r[8]),    # cost_usd
                r[9],               # project
                r[10],              # supplier
                str(r[11]) if r[11] else None,  # quotation
                r[12],              # type
                r[13],              # purchase_plan
                to_date(r[14]),     # pr_expensify_date
                str(r[15]) if r[15] else None,  # pr_expensify_no
                str(r[16]) if r[16] else None,  # po_no
                str(r[17]) if r[17] else None,  # received
                to_date(r[18]),     # date_of_receiving
            ))

        # --- budget overview (right side, col U-AE = index 20-30) ---
        if len(r) < 31:
            continue
        bcode = r[20]
        if bcode is None:
            continue
        try:
            bcode_int = int(bcode)
        except (TypeError, ValueError):
            continue

        overview_rows.append((
            quarter,
            bcode_int,
            r[21],                  # type
            r[22],                  # category
            r[23],                  # category_content
            parse_budget(r[24]),    # budget_usd
            parse_num(r[25]),       # will_pr
            parse_num(r[26]),       # done_pr
            parse_num(r[27]),       # will_expensify
            parse_num(r[28]),       # done_expensify
            parse_num(r[30]),       # remaining  (index 30 = col AE)
        ))

    conn.executemany("""
        INSERT INTO budget_overview
          (quarter, budget_code, type, category, category_content,
           budget_usd, will_pr, done_pr, will_expensify, done_expensify, remaining)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, overview_rows)

    conn.executemany("""
        INSERT INTO transactions
          (quarter, dept_manager, buyer_name, budget_code, manager_confirmed,
           item, cost_original, currency, cost_usd, project, supplier, quotation,
           type, purchase_plan, pr_expensify_date, pr_expensify_no, po_no,
           received, date_of_receiving)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, tx_rows)

    conn.commit()
    print(f"  {quarter}: {len(tx_rows)} transactions, {len(overview_rows)} budget lines")


def main():
    wb   = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    conn = sqlite3.connect(DB_PATH)
    create_tables(conn)

    for sheet_name in SHEETS:
        ws      = wb[sheet_name]
        quarter = sheet_name.split("_")[1]  # "Q1" ~ "Q4"
        import_sheet(ws, quarter, conn)

    # Quick sanity check
    print("\n=== Sanity check ===")
    for tbl in ("budget_overview", "transactions"):
        c = conn.execute(f"SELECT quarter, COUNT(*) FROM {tbl} GROUP BY quarter")
        rows = c.fetchall()
        print(f"{tbl}: {rows}")

    conn.close()
    print(f"\nDone → {DB_PATH}")


if __name__ == "__main__":
    main()
