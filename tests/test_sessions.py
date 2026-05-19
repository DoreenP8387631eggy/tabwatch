import json
import pytest
from pathlib import Path
import tempfile

from backend.app import create_app
import backend.storage.session_store as ss_module
from backend.storage.session_store import SessionStore


@pytest.fixture
def tmp_store(tmp_path):
    store = SessionStore(data_dir=tmp_path)
    ss_module.store = store  # patch module-level store
    import backend.api.sessions as api_mod
    api_mod.store = store
    return store


@pytest.fixture
def client(tmp_store):
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200


def test_create_and_get_session(client):
    resp = client.post("/api/sessions/")
    assert resp.status_code == 201
    data = resp.get_json()
    session_id = data["session_id"]
    assert session_id

    resp2 = client.get(f"/api/sessions/{session_id}")
    assert resp2.status_code == 200
    assert resp2.get_json()["session_id"] == session_id


def test_add_event(client):
    session_id = client.post("/api/sessions/").get_json()["session_id"]
    payload = {"url": "https://example.com", "title": "Example", "event_type": "open"}
    resp = client.post(f"/api/sessions/{session_id}/events", json=payload)
    assert resp.status_code == 201
    event = resp.get_json()
    assert event["url"] == "https://example.com"
    assert event["event_type"] == "open"


def test_close_session(client):
    session_id = client.post("/api/sessions/").get_json()["session_id"]
    resp = client.post(f"/api/sessions/{session_id}/close")
    assert resp.status_code == 200
    assert resp.get_json()["ended_at"] is not None


def test_missing_event_fields(client):
    session_id = client.post("/api/sessions/").get_json()["session_id"]
    resp = client.post(f"/api/sessions/{session_id}/events", json={"url": "https://x.com"})
    assert resp.status_code == 400


def test_session_not_found(client):
    resp = client.get("/api/sessions/nonexistent-id")
    assert resp.status_code == 404
