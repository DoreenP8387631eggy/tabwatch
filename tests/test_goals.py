"""Integration tests for the /sessions/<id>/goals endpoints."""

import pytest
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


def _create_session_with_events(client, events: list[tuple[str, int]]) -> str:
    resp = client.post("/sessions", json={"label": "test"})
    session_id = resp.get_json()["session_id"]
    t = 0
    for url, dur in events:
        client.post(f"/sessions/{session_id}/events", json={"url": url, "timestamp": t, "duration": dur})
        t += dur
    client.post(f"/sessions/{session_id}/close")
    return session_id


def test_goals_not_found(client):
    resp = client.get("/sessions/no-such-id/goals")
    assert resp.status_code == 404


def test_goals_open_session(client):
    resp = client.post("/sessions", json={"label": "open"})
    sid = resp.get_json()["session_id"]
    resp = client.get(f"/sessions/{sid}/goals")
    assert resp.status_code == 400


def test_goals_all_met(client):
    sid = _create_session_with_events(client, [("https://github.com", 4000), ("https://docs.python.org", 200)])
    resp = client.get(f"/sessions/{sid}/goals")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["all_met"] is True
    assert len(data["results"]) == 3


def test_goals_custom_query_param(client):
    sid = _create_session_with_events(client, [("https://twitter.com", 3000)])
    resp = client.get(f"/sessions/{sid}/goals?max_social_minutes=60")
    assert resp.status_code == 200
    data = resp.get_json()
    social = next(r for r in data["results"] if r["goal"] == "max_social_minutes")
    assert social["met"] is True


def test_goals_invalid_query_param(client):
    sid = _create_session_with_events(client, [("https://github.com", 100)])
    resp = client.get(f"/sessions/{sid}/goals?max_social_minutes=abc")
    assert resp.status_code == 400


def test_goals_summary_rating(client):
    sid = _create_session_with_events(client, [("https://github.com", 4000)])
    resp = client.get(f"/sessions/{sid}/goals/summary")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "rating" in data
    assert data["rating"] in ("excellent", "partial", "poor")
    assert "passed" in data
    assert "total" in data
