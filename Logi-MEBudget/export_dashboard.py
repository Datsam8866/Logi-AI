"""
Reads me_budget.db and rewrites the QUARTERS data block in dashboard.html.
Run standalone: python export_dashboard.py
Called automatically by server.py after every add / delete.
"""
import sqlite3
import json
import re
from pathlib import Path

BASE      = Path(__file__).parent
DB_PATH   = BASE / "me_budget.db"
DASH_PATH = BASE / "dashboard.html"

DEADLINES = {
    'Q1': {'pr': '2026/06/12', 'po': '2026/06/24', 'expensify': '2026/06/25'},
    'Q2': {'pr': '2026/09/11', 'po': '2026/09/23', 'expensify': '2026/09/24'},
    'Q3': {'pr': '2026/12/11', 'po': '2026/12/23', 'expensify': '2026/12/24'},
    'Q4': {'pr': '2027/03/19', 'po': '2027/03/26', 'expensify': '2027/03/30'},
}

PLAN_MAP = {
    'Done - PR':        'done_pr',
    'Done - Expensify': 'done_expensify',
    'Will PR':          'will_pr',
    'Will Expensify':   'will_expensify',
}


def export():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    quarters = {}
    for q in ['Q1', 'Q2', 'Q3', 'Q4']:
        ov_rows = conn.execute("""
            SELECT budget_code, category, category_content, budget_usd
            FROM budget_overview WHERE quarter = ?
            ORDER BY budget_code
        """, (q,)).fetchall()

        tx_rows = conn.execute("""
            SELECT id, buyer_name, budget_code, item, cost_usd, currency,
                   project, supplier, purchase_plan, pr_expensify_date
            FROM transactions WHERE quarter = ?
            ORDER BY id
        """, (q,)).fetchall()

        # Per-code spending sums derived from transactions (source of truth)
        actuals = {}
        for t in tx_rows:
            c = t['budget_code']
            if c not in actuals:
                actuals[c] = {v: 0.0 for v in PLAN_MAP.values()}
            field = PLAN_MAP.get(t['purchase_plan'] or '')
            if field:
                actuals[c][field] += t['cost_usd'] or 0.0

        # Build overview list
        overview = []
        for row in ov_rows:
            code = row['budget_code']
            act  = actuals.get(code, {v: 0.0 for v in PLAN_MAP.values()})
            bud  = row['budget_usd']
            spent = act['done_pr'] + act['done_expensify'] + act['will_pr'] + act['will_expensify']
            if bud is None:
                remaining = None
            else:
                remaining = None if spent > bud else round(bud - spent, 2)
            overview.append({
                'budget_code':      code,
                'category':         row['category'],
                'category_content': row['category_content'],
                'budget_usd':       bud,
                'will_pr':          round(act['will_pr'], 2),
                'done_pr':          round(act['done_pr'], 2),
                'will_expensify':   round(act['will_expensify'], 2),
                'done_expensify':   round(act['done_expensify'], 2),
                'remaining':        remaining,
            })

        # Build txns list (include DB id so frontend can delete by id)
        txns = [
            {
                'id':                t['id'],
                'buyer_name':        t['buyer_name'],
                'budget_code':       t['budget_code'],
                'item':              t['item'],
                'cost_usd':          t['cost_usd'],
                'currency':          t['currency'],
                'project':           t['project'],
                'supplier':          t['supplier'],
                'purchase_plan':     t['purchase_plan'],
                'pr_expensify_date': t['pr_expensify_date'],
            }
            for t in tx_rows
        ]

        # Summary
        total_budget = sum(r['budget_usd'] for r in ov_rows if r['budget_usd'])
        done_pr  = sum(t['cost_usd'] or 0 for t in tx_rows if t['purchase_plan'] == 'Done - PR')
        done_exp = sum(t['cost_usd'] or 0 for t in tx_rows if t['purchase_plan'] == 'Done - Expensify')
        will_pr  = sum(t['cost_usd'] or 0 for t in tx_rows if t['purchase_plan'] == 'Will PR')
        will_exp = sum(t['cost_usd'] or 0 for t in tx_rows if t['purchase_plan'] == 'Will Expensify')
        spent_total = done_pr + done_exp + will_pr + will_exp

        quarters[q] = {
            'deadlines': DEADLINES[q],
            'summary': {
                'total_budget':    round(total_budget, 2),
                'total_remaining': round(max(total_budget - spent_total, 0), 2),
                'total_done_pr':   round(done_pr, 2),
                'total_done_exp':  round(done_exp, 2),
                'total_will_pr':   round(will_pr, 2),
                'total_will_exp':  round(will_exp, 2),
            },
            'overview': overview,
            'txns':     txns,
        }

    conn.close()

    # Replace QUARTERS block in dashboard.html
    html   = DASH_PATH.read_text(encoding='utf-8')
    new_js = f'const QUARTERS = {json.dumps(quarters, ensure_ascii=False, indent=2)};'
    updated = re.sub(
        r'// ── Quarter Data ──\nconst QUARTERS = \{.*?\n\};',
        f'// ── Quarter Data ──\n{new_js}',
        html,
        flags=re.DOTALL,
    )
    if updated == html:
        print('[export] WARNING: QUARTERS block not found — dashboard.html unchanged')
        return False
    DASH_PATH.write_text(updated, encoding='utf-8')
    print(f'[export] dashboard.html updated OK '
          f'(Q1:{len(quarters["Q1"]["txns"])} Q2:{len(quarters["Q2"]["txns"])} '
          f'Q3:{len(quarters["Q3"]["txns"])} Q4:{len(quarters["Q4"]["txns"])} txns)')
    return True


if __name__ == '__main__':
    export()
