from __future__ import annotations

from fastapi.testclient import TestClient

from src.web.app import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_index_is_app_shell() -> None:
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    assert "Auto Board" in html
    assert 'id="view-board"' in html
    assert 'id="view-saved"' in html
    assert 'rel="manifest"' in html
    assert "/sw.js" in html


def test_manifest_and_service_worker() -> None:
    manifest = client.get("/manifest.webmanifest")
    assert manifest.status_code == 200
    assert "application/manifest+json" in manifest.headers["content-type"]
    body = manifest.json()
    assert body["name"] == "Auto Board"
    assert body["display"] == "standalone"

    sw = client.get("/sw.js")
    assert sw.status_code == 200
    assert "auto-board-v1" in sw.text
