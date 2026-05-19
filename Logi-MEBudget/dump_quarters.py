import sqlite3, json, openpyxl

DB   = r"C:\Users\skuan1\Desktop\Logi AI\Logi-MEBudget\me_budget.db"
XLSX = r"C:\Users\skuan1\Desktop\Logi AI\Logi-MEBudget\FY27_ME_Budget.xlsx"

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

wb = openpyxl.load_workbook(XLSX, data_only=True)

result = {}
for q in ["Q1","Q2","Q3","Q4"]:
    ws   = wb[f"ME_{q}"]
    row1 = [c.value for c in ws[1]]   # deadline row

    # parse deadlines from row 1 text cells
    def dl(text):
        if not text: return None
        for cell in row1:
            if isinstance(cell, str) and text.lower() in cell.lower():
                # extract date portion after ':'
                parts = cell.split(":")
                return parts[-1].strip() if len(parts) > 1 else None
        return None

    deadlines = {
        "pr":         dl("create pr"),
        "po":         dl("received po") or dl("recevied po"),
        "expensify":  dl("expensify"),
    }

    overview = [dict(r) for r in conn.execute(f"""
        SELECT budget_code, category, category_content, budget_usd,
               will_pr, done_pr, will_expensify, done_expensify, remaining
        FROM budget_overview WHERE quarter=? ORDER BY budget_code
    """, (q,))]

    txns = [dict(r) for r in conn.execute(f"""
        SELECT buyer_name, budget_code, item, cost_usd, currency,
               project, supplier, purchase_plan, pr_expensify_date, received
        FROM transactions WHERE quarter=? ORDER BY budget_code
    """, (q,))]

    summary = dict(conn.execute("""
        SELECT
          SUM(budget_usd)                  AS total_budget,
          SUM(COALESCE(remaining,0))        AS total_remaining,
          SUM(COALESCE(done_pr,0))          AS total_done_pr,
          SUM(COALESCE(done_expensify,0))   AS total_done_exp,
          SUM(COALESCE(will_pr,0))          AS total_will_pr,
          SUM(COALESCE(will_expensify,0))   AS total_will_exp
        FROM budget_overview WHERE quarter=? AND budget_usd IS NOT NULL
    """, (q,)).fetchone())

    result[q] = {"deadlines": deadlines, "overview": overview,
                 "txns": txns, "summary": summary}

conn.close()
print(json.dumps(result, ensure_ascii=False, default=str))
