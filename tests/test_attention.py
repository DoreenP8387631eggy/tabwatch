"""Integration tests for /sessions/<id>/attention endpoints."""

import pytest
from backend.app import create_app
from backend.storage.session_store import SessionStore
from backend.api.attention import init_attention


@pytest.fixture()
def tmp_store(tmp_path):
    return SessionStore(str(tmp_path))


@pytest.fixture()
def client(tmp_store):
    app = create_app(tmp_store)
    init_attention(app, tmp_store)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _create_session_with_events(client):
    r = client.post("/sessions", json={"session_id": "test-attn"})
    assert r.status_code == 201
    sid = r.get_json()["session_id"]
    events = [
        {"url": "https://github.com",       "title": "GitHub",  "timestamp": "2024-01-01T09:00:00"},
        {"url": "https://docs.python.org",   "title": "Docs",    "timestamp": "2024-01-01T09:05:00"},
        {"url": "https://twitter.com",       "title": "Twitter", "timestamp": "2024-01-01T09:17:00"},
        {"url": "https://twitter.com/feed",  "title": "Feed",    "timestamp": "2024-01-01T09:17:08"},
    ]
    for ev in events:
        client.post(f"/sessions/{sid}/events", json=ev)
    client.post(f"/sessions/{sid}/close")
    return sid


def test_attention_not_found(client):
    r = client.get("/sessions/missing/attention")
    assert r.status_code == 404


def test_attention_score_not_found(client):
    r = client.get("/sessions/missing/attention/score")
    assert r.status_code == 404


def test_attention_longest_not_found(client):
    r = client.get("/sessions/missing/attention/longest")
    assert r.status_code == 404


def test_attention_full(client):
    sid = _create_session_with_events(client)
    r = client.get(f"/sessions/{sid}/attention")
    assert r.status_code == 200
    data = r.get_json()
    assert "total_visits" in data
    assert "attention_score" in data
    assert data["total_visits"] == 4


def test_attention_score_endpoint(client):
    sid = _create_session_with_events(client)
    r = client.get(f"/sessions/{sid}/attention/score")
    assert r.status_code == 200
    data = r.get_json()
    assert "attention_score" in data
    assert 0 <= data["attention_score"] <= 100


def test_attention_longest_endpoint(client):
    sid = _create_session_with_events(client)
    r = client.get(f"/sessions/{sid}/attention/longest")
    assert r.status_code == 200
    data = r.get_json()
    assert "longest_visit" in data
    assert "domain" in data["longest_visit"]
    assert "seconds" in data["longest_visit"]
