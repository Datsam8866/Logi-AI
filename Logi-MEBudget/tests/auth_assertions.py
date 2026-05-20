import os
import sys
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test-secret")
os.environ.setdefault("ALLOWED_VIEWERS", "viewer@example.com")
os.environ.setdefault("ALLOWED_EDITORS", "editor@example.com")

import server


assert server.app.secret_key
assert server.cloud_run_port({"PORT": "8080"}) == 8080
assert server.cloud_run_port({"PORT": "not-a-number"}) == 5173
assert server.cloud_run_port({}) == 5173

assert server.role_for_email("editor@example.com") == "editor"
assert server.role_for_email("EDITOR@example.com") == "editor"
assert server.role_for_email("viewer@example.com") == "viewer"
assert server.role_for_email("unknown@example.com") is None

client = server.app.test_client()

assert client.get("/api/me").status_code == 401

with client.session_transaction() as session:
    session["user"] = {"email": "viewer@example.com", "role": "viewer"}

viewer_me = client.get("/api/me")
assert viewer_me.status_code == 200
assert viewer_me.json["email"] == "viewer@example.com"
assert viewer_me.json["role"] == "viewer"
assert client.post("/api/txn", json={}).status_code == 403

with client.session_transaction() as session:
    session["user"] = {"email": "editor@example.com", "role": "editor"}

assert client.get("/api/me").json["role"] == "editor"
assert client.post("/api/txn", json={}).status_code == 400

login_resp = client.get(
    "/login",
    base_url="http://tramadol-faqs-quarter-motor.trycloudflare.com",
    headers={"Host": "tramadol-faqs-quarter-motor.trycloudflare.com"},
)
assert login_resp.status_code == 302
assert (
    "redirect_uri=https%3A%2F%2Ftramadol-faqs-quarter-motor.trycloudflare.com%2Fauth%2Fgoogle%2Fcallback"
    in login_resp.headers["Location"]
)

env = os.environ.copy()
env["MEBUDGET_SECRET_KEY"] = ""
empty_secret_check = subprocess.run(
    [
        sys.executable,
        "-c",
        (
            "import os;"
            "os.environ['GOOGLE_CLIENT_ID']='test-client';"
            "os.environ['GOOGLE_CLIENT_SECRET']='test-secret';"
            "os.environ['ALLOWED_EDITORS']='editor@example.com';"
            "import server;"
            "resp=server.app.test_client().get('/login');"
            "assert resp.status_code == 302, resp.status_code"
        ),
    ],
    cwd=os.path.dirname(os.path.dirname(__file__)),
    env=env,
)
assert empty_secret_check.returncode == 0

print("Auth assertions OK")
