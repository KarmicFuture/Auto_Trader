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
    me = client.get("/api/me")
    assert me.json()["user"] is None


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
