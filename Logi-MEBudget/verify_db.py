import sqlite3
conn = sqlite3.connect(r"C:\Users\skuan1\Desktop\Logi AI\Logi-MEBudget\me_budget.db")

print("=== budget_overview (Q1, 有預算的項目) ===")
for r in conn.execute("""
    SELECT budget_code, category, category_content, budget_usd, remaining
    FROM budget_overview WHERE quarter='Q1' AND budget_usd IS NOT NULL
"""):
    print(r)

print("\n=== transactions (Q1) ===")
for r in conn.execute("""
    SELECT buyer_name, budget_code, substr(item,1,45), cost_usd, purchase_plan
    FROM transactions WHERE quarter='Q1'
"""):
    print(r)

print("\n=== Q1 Summary ===")
row = conn.execute("""
    SELECT SUM(budget_usd), SUM(remaining)
    FROM budget_overview WHERE quarter='Q1' AND budget_usd IS NOT NULL
""").fetchone()
print(f"Total Budget: ${row[0]:,.0f}   Remaining: ${row[1]:,.0f}")

conn.close()
