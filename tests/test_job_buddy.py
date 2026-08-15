from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1] / "job-buddy"
sys.path.insert(0, str(ROOT))


def make_client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("JOB_BUDDY_HOME", str(tmp_path))
    import store
    import server

    store.init_db()
    return TestClient(server.app)


def test_landing_page_asks_for_account(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    page = client.get("/")
    assert page.status_code == 200
    assert "Create an account to begin" in page.text
    assert "Create account" in page.text
    assert "Continue with LinkedIn" in page.text
    me = client.get("/api/me")
    assert me.json()["user"] is None
    assert client.get("/api/config").json()["linkedin"] is False


def test_register_saves_account_then_needs_resume(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    res = client.post(
        "/api/register",
        data={"name": "Ada Chen", "email": "ada@example.com", "password": "secret123"},
    )
    body = res.json()
    assert res.status_code == 200
    assert body["ok"] is True
    assert body["next"] == "resume"
    assert body["user"]["email"] == "ada@example.com"
    assert body["user"]["has_resume"] is False
    me = client.get("/api/me")
    assert me.json()["user"]["name"] == "Ada Chen"


def test_duplicate_email_is_rejected(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    payload = {"name": "Ada Chen", "email": "ada@example.com", "password": "secret123"}
    assert client.post("/api/register", data=payload).status_code == 200
    again = client.post("/api/register", data=payload)
    assert again.status_code == 400
    assert "already exists" in again.json()["error"]


def test_weak_password_rejected(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    res = client.post(
        "/api/register",
        data={"name": "Ada", "email": "ada@example.com", "password": "short"},
    )
    assert res.status_code == 400


def test_login_and_resume_upload(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    client.post(
        "/api/register",
        data={"name": "Ada Chen", "email": "ada@example.com", "password": "secret123"},
    )
    upload = client.post(
        "/api/resume",
        files={"file": ("Ada_Chen.pdf", b"%PDF-1.4 resume bytes", "application/pdf")},
    )
    body = upload.json()
    assert upload.status_code == 200
    assert body["next"] == "desk"
    assert body["user"]["has_resume"] is True
    assert body["user"]["resume"]["filename"] == "Ada_Chen.pdf"

    client.post("/api/logout")
    denied = client.post(
        "/api/resume",
        files={"file": ("x.pdf", b"abc", "application/pdf")},
    )
    assert denied.status_code == 401

    login = client.post(
        "/api/login",
        data={"email": "ada@example.com", "password": "secret123"},
    )
    assert login.json()["next"] == "desk"
    tips = client.get("/api/tips")
    assert tips.status_code == 200
    assert len(tips.json()["tips"]) >= 8


def test_resume_rejects_bad_type(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    client.post(
        "/api/register",
        data={"name": "Ada Chen", "email": "ada@example.com", "password": "secret123"},
    )
    res = client.post(
        "/api/resume",
        files={"file": ("photo.exe", b"MZ", "application/octet-stream")},
    )
    assert res.status_code == 400


def test_tips_require_account(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    assert client.get("/api/tips").status_code == 401


def test_wrong_password(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    client.post(
        "/api/register",
        data={"name": "Ada Chen", "email": "ada@example.com", "password": "secret123"},
    )
    client.post("/api/logout")
    res = client.post(
        "/api/login",
        data={"email": "ada@example.com", "password": "nope-nope"},
    )
    assert res.status_code == 401


def test_linkedin_start_without_credentials_explains(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    res = client.get("/api/auth/linkedin", follow_redirects=False)
    assert res.status_code == 302
    assert "auth_error=" in res.headers["location"]
    assert "not%20configured" in res.headers["location"] or "not configured" in res.headers["location"]


def test_linkedin_callback_creates_account_then_needs_resume(tmp_path, monkeypatch):
    from urllib.parse import parse_qs, urlparse

    monkeypatch.setenv("LINKEDIN_CLIENT_ID", "test-id")
    monkeypatch.setenv("LINKEDIN_CLIENT_SECRET", "test-secret")
    client = make_client(tmp_path, monkeypatch)
    assert client.get("/api/config").json()["linkedin"] is True

    start = client.get("/api/auth/linkedin", follow_redirects=False)
    assert start.status_code == 302
    location = start.headers["location"]
    assert "linkedin.com/oauth/v2/authorization" in location
    query = parse_qs(urlparse(location).query)
    assert query["client_id"] == ["test-id"]
    assert "openid" in query["scope"][0]
    state = query["state"][0]

    import server

    monkeypatch.setattr(
        server.linkedin_auth,
        "exchange_code",
        lambda code: {"access_token": "tok"} if code == "good-code" else {},
    )
    monkeypatch.setattr(
        server.linkedin_auth,
        "fetch_userinfo",
        lambda _token: {
            "sub": "li-99",
            "name": "Ada Chen",
            "email": "ada@linkedin.example",
            "picture": "https://example.com/ada.jpg",
        },
    )

    res = client.get(
        f"/api/auth/linkedin/callback?code=good-code&state={state}",
        follow_redirects=False,
    )
    assert res.status_code == 302
    me = client.get("/api/me").json()["user"]
    assert me["email"] == "ada@linkedin.example"
    assert me["name"] == "Ada Chen"
    assert me["linkedin"] is True
    assert me["has_resume"] is False

    denied = client.post(
        "/api/login",
        data={"email": "ada@linkedin.example", "password": "secret123"},
    )
    assert denied.status_code == 401
    assert "LinkedIn" in denied.json()["error"]


def test_linkedin_links_existing_email_account(tmp_path, monkeypatch):
    from urllib.parse import parse_qs, urlparse

    monkeypatch.setenv("LINKEDIN_CLIENT_ID", "test-id")
    monkeypatch.setenv("LINKEDIN_CLIENT_SECRET", "test-secret")
    client = make_client(tmp_path, monkeypatch)
    client.post(
        "/api/register",
        data={"name": "Ada Chen", "email": "ada@example.com", "password": "secret123"},
    )
    client.post("/api/logout")

    start = client.get("/api/auth/linkedin", follow_redirects=False)
    state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
    import server

    monkeypatch.setattr(server.linkedin_auth, "exchange_code", lambda _code: {"access_token": "tok"})
    monkeypatch.setattr(
        server.linkedin_auth,
        "fetch_userinfo",
        lambda _token: {
            "sub": "li-99",
            "name": "Ada Chen",
            "email": "ada@example.com",
        },
    )
    client.get(f"/api/auth/linkedin/callback?code=good-code&state={state}", follow_redirects=False)
    me = client.get("/api/me").json()["user"]
    assert me["linkedin"] is True
    client.post("/api/logout")
    login = client.post(
        "/api/login",
        data={"email": "ada@example.com", "password": "secret123"},
    )
    assert login.status_code == 200
    assert login.json()["user"]["linkedin"] is True


def test_linkedin_rejects_bad_state(tmp_path, monkeypatch):
    monkeypatch.setenv("LINKEDIN_CLIENT_ID", "test-id")
    monkeypatch.setenv("LINKEDIN_CLIENT_SECRET", "test-secret")
    client = make_client(tmp_path, monkeypatch)
    res = client.get(
        "/api/auth/linkedin/callback?code=good-code&state=nope",
        follow_redirects=False,
    )
    assert res.status_code == 302
    assert "auth_error=" in res.headers["location"]
    assert client.get("/api/me").json()["user"] is None
