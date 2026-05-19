"""Tests for the heatmap API endpoints and heatmap builder logic."""

import pytest
from datetime import datetime, timezone
from backend.app import create_app
from backend.storage.session_store import SessionStore


@pytest.fixture
def tmp_store(tmp_path):
    return SessionStore(storage_dir=str(tmp_path))


@pytest.fixture
def client(tmp_store):
    app = create_app(store=tmp_store)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _create_session_with_events(client, events):
    """Helper: create a session and post a list of (url, ts_iso) events."""
    resp = client.post("/sessions", json={"label": "test"})
    sid = resp.get_json()["session_id"]
    for url, ts in events:
        client.post(f"/sessions/{sid}/events", json={"url": url, "timestamp": ts})
    return sid


def test_heatmap_not_found(client):
    resp = client.get("/sessions/missing/heatmap")
    assert resp.status_code == 404


def test_peak_not_found(client):
    resp = client.get("/sessions/missing/heatmap/peak")
    assert resp.status_code == 404


def test_heatmap_empty_session(client):
    resp = client.post("/sessions", json={"label": "empty"})
    sid = resp.get_json()["session_id"]
    resp = client.get(f"/sessions/{sid}/heatmap")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["cells"] == []
    assert data["max_count"] == 0


def test_heatmap_cells_populated(client):
    # Monday 2024-01-01 09:00 UTC and Tuesday 2024-01-02 14:00 UTC
    events = [
        ("https://github.com", "2024-01-01T09:00:00"),
        ("https://github.com", "2024-01-01T09:30:00"),
        ("https://news.ycombinator.com", "2024-01-02T14:00:00"),
    ]
    sid = _create_session_with_events(client, events)
    resp = client.get(f"/sessions/{sid}/heatmap")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["max_count"] == 2
    assert any(c["count"] == 2 and c["hour"] == 9 for c in data["cells"])
    assert any(c["count"] == 1 and c["hour"] == 14 for c in data["cells"])


def test_peak_slot(client):
    events = [
        ("https://github.com", "2024-01-01T09:00:00"),
        ("https://github.com", "2024-01-01T09:15:00"),
        ("https://github.com", "2024-01-01T09:45:00"),
        ("https://news.ycombinator.com", "2024-01-02T14:00:00"),
    ]
    sid = _create_session_with_events(client, events)
    resp = client.get(f"/sessions/{sid}/heatmap/peak")
    assert resp.status_code == 200
    peak = resp.get_json()["peak"]
    assert peak["hour"] == 9
    assert peak["count"] == 3


def test_peak_empty_session(client):
    resp = client.post("/sessions", json={"label": "empty"})
    sid = resp.get_json()["session_id"]
    resp = client.get(f"/sessions/{sid}/heatmap/peak")
    assert resp.status_code == 200
    assert resp.get_json()["peak"] is None
