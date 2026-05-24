"""Integration tests for /sessions/<id>/rhythm endpoints."""

import pytest
from datetime import datetime, timedelta
from backend.app import create_app
from backend.storage.session_store import SessionStore
from backend.models.session import BrowsingSession, TabEvent


@pytest.fixture()
def tmp_store(tmp_path):
    return SessionStore(str(tmp_path))


@pytest.fixture()
def client(tmp_store):
    app = create_app(tmp_store)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _create_session_with_events(tmp_store: SessionStore, n: int = 5, gap: int = 30) -> str:
    s = BrowsingSession(session_id="test-rhythm")
    base = datetime(2024, 1, 10, 9, 0, 0)
    urls = ["https://github.com", "https://docs.python.org", "https://news.ycombinator.com"]
    for i in range(n):
        ts = (base + timedelta(seconds=i * gap)).isoformat()
        s.events.append(TabEvent(url=urls[i % len(urls)], title="T", timestamp=ts, event_type="visit"))
    s.end_time = (base + timedelta(seconds=n * gap)).isoformat()
    tmp_store.save(s)
    return s.session_id


def test_rhythm_not_found(client):
    r = client.get("/sessions/missing/rhythm")
    assert r.status_code == 404


def test_rhythm_label_not_found(client):
    r = client.get("/sessions/missing/rhythm/label")
    assert r.status_code == 404


def test_rhythm_bursts_not_found(client):
    r = client.get("/sessions/missing/rhythm/bursts")
    assert r.status_code == 404


def test_rhythm_full(client, tmp_store):
    sid = _create_session_with_events(tmp_store, n=6, gap=30)
    r = client.get(f"/sessions/{sid}/rhythm")
    assert r.status_code == 200
    data = r.get_json()
    assert "rhythm_label" in data
    assert "avg_gap_seconds" in data
    assert "event_count" in data
    assert data["event_count"] == 6


def test_rhythm_label_endpoint(client, tmp_store):
    sid = _create_session_with_events(tmp_store, n=4, gap=5)
    r = client.get(f"/sessions/{sid}/rhythm/label")
    assert r.status_code == 200
    data = r.get_json()
    assert data["session_id"] == sid
    assert data["rhythm_label"] in {"frantic", "steady", "relaxed", "idle"}


def test_rhythm_bursts_endpoint(client, tmp_store):
    sid = _create_session_with_events(tmp_store, n=8, gap=2)
    r = client.get(f"/sessions/{sid}/rhythm/bursts")
    assert r.status_code == 200
    data = r.get_json()
    assert "burst_count" in data
    assert "idle_count" in data
    assert data["burst_count"] >= 0
