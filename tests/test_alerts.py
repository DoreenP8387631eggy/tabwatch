"""Tests for the alerts feature."""

import time
import pytest
from backend.app import create_app
from backend.storage.session_store import SessionStore


@pytest.fixture
def tmp_store(tmp_path):
    return SessionStore(str(tmp_path))


@pytest.fixture
def client(tmp_store):
    app = create_app(tmp_store)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _create_session_with_events(client, events):
    rv = client.post("/sessions", json={"label": "test"})
    sid = rv.get_json()["session_id"]
    for ev in events:
        client.post(f"/sessions/{sid}/events", json=ev)
    return sid


def test_alerts_not_found(client):
    rv = client.get("/sessions/missing/alerts")
    assert rv.status_code == 404


def test_alerts_summary_not_found(client):
    rv = client.get("/sessions/missing/alerts/summary")
    assert rv.status_code == 404


def test_alerts_empty_session(client):
    rv = client.post("/sessions", json={"label": "empty"})
    sid = rv.get_json()["session_id"]
    rv = client.get(f"/sessions/{sid}/alerts")
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["alert_count"] == 0
    assert data["alerts"] == []


def test_alerts_no_issues(client):
    now = time.time()
    events = [
        {"url": "https://github.com/user/repo", "title": "GitHub", "timestamp": now},
        {"url": "https://docs.python.org/3/", "title": "Python Docs", "timestamp": now + 600},
    ]
    sid = _create_session_with_events(client, events)
    rv = client.get(f"/sessions/{sid}/alerts")
    assert rv.status_code == 200
    data = rv.get_json()
    assert isinstance(data["alerts"], list)
    assert data["session_id"] == sid


def test_alerts_high_distraction(client):
    now = time.time()
    events = [
        {"url": "https://twitter.com/home", "title": "Twitter", "timestamp": now},
        {"url": "https://twitter.com/explore", "title": "Twitter Explore", "timestamp": now + 2100},
    ]
    sid = _create_session_with_events(client, events)
    rv = client.get(f"/sessions/{sid}/alerts")
    assert rv.status_code == 200
    data = rv.get_json()
    types = [a["type"] for a in data["alerts"]]
    assert "high_distraction" in types


def test_alerts_summary_has_warnings(client):
    now = time.time()
    events = [
        {"url": "https://twitter.com/home", "title": "Twitter", "timestamp": now},
        {"url": "https://twitter.com/explore", "title": "Twitter Explore", "timestamp": now + 2100},
    ]
    sid = _create_session_with_events(client, events)
    rv = client.get(f"/sessions/{sid}/alerts/summary")
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["has_warnings"] is True
    assert data["total_alerts"] >= 1
    assert "warning" in data["by_severity"]
