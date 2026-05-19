import sqlite3, json
conn = sqlite3.connect(r"C:\Users\skuan1\Desktop\Logi AI\Logi-MEBudget\me_budget.db")
conn.row_factory = sqlite3.Row

overview = [dict(r) for r in conn.execute("""
    SELECT budget_code, category, category_content, budget_usd,
           will_pr, done_pr, will_expensify, done_expensify, remaining
    FROM budget_overview WHERE quarter='Q1' ORDER BY budget_code
""")]

txns = [dict(r) for r in conn.execute("""
    SELECT buyer_name, budget_code, item, cost_usd, currency,
           project, supplier, purchase_plan, pr_expensify_date, received
    FROM transactions WHERE quarter='Q1' ORDER BY budget_code
""")]

summary = dict(conn.execute("""
    SELECT
        SUM(budget_usd)                                        AS total_budget,
        SUM(CASE WHEN budget_usd IS NOT NULL THEN COALESCE(remaining,0) ELSE 0 END) AS total_remaining,
        SUM(COALESCE(done_pr,0))                               AS total_done_pr,
        SUM(COALESCE(done_expensify,0))                        AS total_done_expensify,
        SUM(COALESCE(will_pr,0))                               AS total_will_pr,
        SUM(COALESCE(will_expensify,0))                        AS total_will_expensify
    FROM budget_overview WHERE quarter='Q1'
""").fetchone())

print("OVERVIEW:", json.dumps(overview, ensure_ascii=False, default=str))
print("TXNS:", json.dumps(txns, ensure_ascii=False, default=str))
print("SUMMARY:", json.dumps(summary, ensure_ascii=False, default=str))
conn.close()
