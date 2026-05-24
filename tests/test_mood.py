"""Integration tests for the mood API endpoints."""

import pytest
from backend.app import create_app
from backend.storage.session_store import SessionStore
from backend.models.session import TabEvent
import tempfile, os


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
    r = client.post("/sessions", json={"session_id": "s1"})
    assert r.status_code == 201
    events = [
        {"url": "https://github.com/user", "title": "GitHub",
         "timestamp": "2024-01-01T09:00:00", "event_type": "visit"},
        {"url": "https://stackoverflow.com/q/1", "title": "SO",
         "timestamp": "2024-01-01T09:15:00", "event_type": "visit"},
        {"url": "https://twitter.com/home", "title": "Twitter",
         "timestamp": "2024-01-01T09:30:00", "event_type": "visit"},
    ]
    for e in events:
        client.post("/sessions/s1/events", json=e)
    return "s1"


def test_mood_not_found(client):
    r = client.get("/sessions/missing/mood")
    assert r.status_code == 404
    assert "error" in r.get_json()


def test_dominant_mood_not_found(client):
    r = client.get("/sessions/missing/mood/dominant")
    assert r.status_code == 404


def test_mood_returns_structure(client):
    sid = _create_session_with_events(client)
    r = client.get(f"/sessions/{sid}/mood")
    assert r.status_code == 200
    data = r.get_json()
    assert "dominant_mood" in data
    assert "scores" in data
    assert "category_breakdown" in data
    assert data["session_id"] == sid


def test_dominant_mood_returns_label(client):
    sid = _create_session_with_events(client)
    r = client.get(f"/sessions/{sid}/mood/dominant")
    assert r.status_code == 200
    data = r.get_json()
    assert "dominant_mood" in data
    assert isinstance(data["dominant_mood"], str)


def test_mood_scores_are_normalised(client):
    sid = _create_session_with_events(client)
    r = client.get(f"/sessions/{sid}/mood")
    scores = r.get_json()["scores"]
    total = sum(scores.values())
    assert abs(total - 1.0) < 1e-4
