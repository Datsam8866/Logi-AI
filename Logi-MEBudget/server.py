"""
ME Budget local server.
Start : python server.py
Browser: http://localhost:5173

Endpoints:
  GET  /              → serve dashboard.html
  GET  /api/ping      → {"ok": true}  (used by JS to detect server mode)
  POST /api/txn       → insert transaction → re-export dashboard
  DELETE /api/txn/<id>→ delete transaction → re-export dashboard
"""
from flask import Flask, request, jsonify, send_file
import sqlite3
from pathlib import Path
import export_dashboard

BASE    = Path(__file__).parent
DB_PATH = str(BASE / 'me_budget.db')
DASH    = BASE / 'dashboard.html'

app = Flask(__name__)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    return send_file(DASH)


@app.route('/api/ping')
def ping():
    return jsonify(ok=True)


@app.route('/api/txn', methods=['POST'])
def add_txn():
    d = request.json or {}
    required = ('quarter', 'buyer_name', 'budget_code', 'item', 'cost_usd', 'purchase_plan')
    if not all(d.get(k) is not None for k in required):
        return jsonify(error='Missing required fields'), 400

    conn = get_db()
    conn.execute("""
        INSERT INTO transactions
          (quarter, buyer_name, budget_code, item,
           cost_usd, currency, project, supplier,
           purchase_plan, pr_expensify_date)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (
        d['quarter'],
        d['buyer_name'],
        int(d['budget_code']),
        d['item'],
        float(d['cost_usd']),
        d.get('currency', 'TWD'),
        d.get('project') or None,
        d.get('supplier') or None,
        d['purchase_plan'],
        d.get('pr_expensify_date') or None,
    ))
    conn.commit()
    conn.close()

    export_dashboard.export()
    return jsonify(ok=True)


@app.route('/api/txn/<int:txn_id>', methods=['DELETE'])
def delete_txn(txn_id):
    conn = get_db()
    cur = conn.execute('SELECT id FROM transactions WHERE id = ?', (txn_id,))
    if not cur.fetchone():
        conn.close()
        return jsonify(error='Not found'), 404

    conn.execute('DELETE FROM transactions WHERE id = ?', (txn_id,))
    conn.commit()
    conn.close()

    export_dashboard.export()
    return jsonify(ok=True)


if __name__ == '__main__':
    print('ME Budget Server → http://localhost:5173')
    print('Press Ctrl+C to stop.')
    app.run(host='127.0.0.1', port=5173, debug=False)
