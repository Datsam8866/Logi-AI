"""
ME Budget local server.
Start : python server.py
Browser: http://localhost:5173
LAN    : http://<this-computer-ip>:5173

Required OAuth env:
  GOOGLE_CLIENT_ID
  GOOGLE_CLIENT_SECRET
  ALLOWED_EDITORS     comma-separated emails
Optional:
  ALLOWED_VIEWERS     comma-separated emails
  MEBUDGET_SECRET_KEY stable Flask session key

Endpoints:
  GET  /              -> serve dashboard.html
  GET  /login         -> Google OAuth start
  GET  /auth/google/callback -> Google OAuth callback
  POST /logout        -> clear login session
  GET  /api/me        -> current user and role
  GET  /api/ping      -> {"ok": true}
  POST /api/txn       -> editor only
  DELETE /api/txn/<id>-> editor only
"""
from urllib.parse import urlencode
from pathlib import Path
import os
import secrets
import sqlite3

import requests
from flask import Flask, Response, jsonify, redirect, request, session, url_for

import export_dashboard

BASE = Path(__file__).parent
DB_PATH = str(BASE / "me_budget.db")
DASH = BASE / "dashboard.html"

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
ALLOWED_EDITORS = os.environ.get("ALLOWED_EDITORS", "")
ALLOWED_VIEWERS = os.environ.get("ALLOWED_VIEWERS", "")

app = Flask(__name__)
app.secret_key = os.environ.get("MEBUDGET_SECRET_KEY", secrets.token_hex(32))


def parse_emails(value):
    return {email.strip().lower() for email in value.split(",") if email.strip()}


EDITOR_EMAILS = parse_emails(ALLOWED_EDITORS)
VIEWER_EMAILS = parse_emails(ALLOWED_VIEWERS)


def role_for_email(email):
    normalized = (email or "").strip().lower()
    if normalized in EDITOR_EMAILS:
        return "editor"
    if normalized in VIEWER_EMAILS:
        return "viewer"
    return None


def current_user():
    return session.get("user")


def is_authenticated():
    return current_user() is not None


def is_editor():
    user = current_user()
    return bool(user and user.get("role") == "editor")


def oauth_configured():
    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET and EDITOR_EMAILS)


def external_base_url():
    forwarded_proto = request.headers.get("X-Forwarded-Proto")
    forwarded_host = request.headers.get("X-Forwarded-Host")
    if forwarded_proto and forwarded_host:
        return f"{forwarded_proto}://{forwarded_host}"
    return request.url_root.rstrip("/")


def oauth_redirect_uri():
    return f"{external_base_url()}/auth/google/callback"


@app.before_request
def require_login():
    public_paths = {"/login", "/auth/google/callback", "/api/ping"}
    if request.path in public_paths:
        return None
    if is_authenticated():
        return None
    if request.path.startswith("/api/"):
        return jsonify(error="Authentication required"), 401
    return redirect(url_for("login"))


def require_editor():
    if not is_editor():
        return jsonify(error="Editor permission required"), 403
    return None


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/login")
def login():
    if not oauth_configured():
        return Response(
            "Google OAuth is not configured. Set GOOGLE_CLIENT_ID, "
            "GOOGLE_CLIENT_SECRET, and ALLOWED_EDITORS before starting server.",
            status=500,
            content_type="text/plain; charset=utf-8",
        )

    state = secrets.token_urlsafe(24)
    session["oauth_state"] = state
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": oauth_redirect_uri(),
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "prompt": "select_account",
    }
    return redirect(f"{GOOGLE_AUTH_URL}?{urlencode(params)}")


@app.route("/auth/google/callback")
def google_callback():
    if request.args.get("state") != session.pop("oauth_state", None):
        return Response("Invalid OAuth state.", status=400)

    code = request.args.get("code")
    if not code:
        return Response("Missing OAuth code.", status=400)

    token_resp = requests.post(
        GOOGLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": oauth_redirect_uri(),
            "grant_type": "authorization_code",
        },
        timeout=15,
    )
    if token_resp.status_code != 200:
        return Response(f"Token exchange failed: {token_resp.text}", status=400)

    access_token = token_resp.json().get("access_token")
    user_resp = requests.get(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    if user_resp.status_code != 200:
        return Response(f"User lookup failed: {user_resp.text}", status=400)

    profile = user_resp.json()
    email = profile.get("email", "").lower()
    role = role_for_email(email)
    if not role:
        session.clear()
        return Response(f"{email} is not allowed to access this dashboard.", status=403)

    session["user"] = {
        "email": email,
        "name": profile.get("name") or email,
        "picture": profile.get("picture"),
        "role": role,
    }
    return redirect(url_for("index"))


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def index():
    content = DASH.read_text(encoding="utf-8")
    return Response(content, content_type="text/html; charset=utf-8")


@app.route("/api/me")
def me():
    user = current_user()
    if not user:
        return jsonify(error="Authentication required"), 401
    return jsonify(user)


@app.route("/api/ping")
def ping():
    return jsonify(ok=True)


@app.route("/api/txn", methods=["POST"])
def add_txn():
    denied = require_editor()
    if denied:
        return denied

    d = request.json or {}
    required = ("quarter", "buyer_name", "budget_code", "item", "cost_usd", "purchase_plan")
    if not all(d.get(k) is not None for k in required):
        return jsonify(error="Missing required fields"), 400

    conn = get_db()
    conn.execute(
        """
        INSERT INTO transactions
          (quarter, buyer_name, budget_code, item,
           cost_usd, currency, project, supplier,
           purchase_plan, pr_expensify_date)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """,
        (
            d["quarter"],
            d["buyer_name"],
            int(d["budget_code"]),
            d["item"],
            float(d["cost_usd"]),
            d.get("currency", "TWD"),
            d.get("project") or None,
            d.get("supplier") or None,
            d["purchase_plan"],
            d.get("pr_expensify_date") or None,
        ),
    )
    conn.commit()
    conn.close()

    export_dashboard.export()
    return jsonify(ok=True)


@app.route("/api/txn/<int:txn_id>", methods=["DELETE"])
def delete_txn(txn_id):
    denied = require_editor()
    if denied:
        return denied

    conn = get_db()
    cur = conn.execute("SELECT id FROM transactions WHERE id = ?", (txn_id,))
    if not cur.fetchone():
        conn.close()
        return jsonify(error="Not found"), 404

    conn.execute("DELETE FROM transactions WHERE id = ?", (txn_id,))
    conn.commit()
    conn.close()

    export_dashboard.export()
    return jsonify(ok=True)


if __name__ == "__main__":
    if not oauth_configured():
        print("WARNING: Google OAuth is not fully configured.")
        print("Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and ALLOWED_EDITORS.")
    print("ME Budget Server: http://localhost:5173")
    print("LAN access: http://<this-computer-ip>:5173")
    print("Press Ctrl+C to stop.")
    app.run(host="0.0.0.0", port=5173, debug=False)
