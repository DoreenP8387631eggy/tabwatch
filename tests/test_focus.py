"""Integration tests for focus API endpoints."""

import pytest
from datetime import datetime, timedelta

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


def _create_session_with_events(client):
    """Helper: create a session and add events spaced apart for focus testing."""
    r = client.post("/sessions")
    assert r.status_code == 201
    sid = r.get_json()["session_id"]

    base = datetime(2024, 6, 1, 9, 0, 0)
    events = [
        {"url": "https://github.com/repo", "title": "GitHub",
         "timestamp": (base).isoformat()},
        {"url": "https://github.com/repo/issues", "title": "Issues",
         "timestamp": (base + timedelta(seconds=150)).isoformat()},
        {"url": "https://twitter.com", "title": "Twitter",
         "timestamp": (base + timedelta(seconds=160)).isoformat()},
        {"url": "https://docs.python.org", "title": "Docs",
         "timestamp": (base + timedelta(seconds=400)).isoformat()},
    ]
    for e in events:
        r2 = client.post(f"/sessions/{sid}/events", json=e)
        assert r2.status_code == 201

    client.post(f"/sessions/{sid}/close")
    return sid


def test_focus_not_found(client):
    r = client.get("/sessions/missing-id/focus")
    assert r.status_code == 404


def test_focus_score_not_found(client):
    r = client.get("/sessions/missing-id/focus/score")
    assert r.status_code == 404


def test_focus_returns_expected_keys(client):
    sid = _create_session_with_events(client)
    r = client.get(f"/sessions/{sid}/focus")
    assert r.status_code == 200
    data = r.get_json()
    for key in ("focused_visits", "shallow_visits", "deep_focus_visits",
                "focus_ratio", "top_focus_domains", "session_id"):
        assert key in data, f"missing key: {key}"


def test_focus_score_in_range(client):
    sid = _create_session_with_events(client)
    r = client.get(f"/sessions/{sid}/focus/score")
    assert r.status_code == 200
    data = r.get_json()
    assert "focus_score" in data
    assert 0 <= data["focus_score"] <= 100


def test_focus_ratio_between_0_and_1(client):
    sid = _create_session_with_events(client)
    r = client.get(f"/sessions/{sid}/focus")
    data = r.get_json()
    assert 0.0 <= data["focus_ratio"] <= 1.0
