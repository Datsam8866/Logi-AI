import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test-secret")
os.environ.setdefault("ALLOWED_VIEWERS", "viewer@example.com")
os.environ.setdefault("ALLOWED_EDITORS", "editor@example.com")

import server


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

print("Auth assertions OK")
