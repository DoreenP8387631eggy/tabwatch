"""Tests for the session comparison API and summarizer."""

import pytest
from datetime import datetime, timezone
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


def _create_closed_session(client, urls):
    """Helper: create, populate, and close a session. Returns session_id."""
    r = client.post("/sessions")
    sid = r.get_json()["session_id"]
    for i, url in enumerate(urls):
        client.post(f"/sessions/{sid}/events", json={
            "url": url,
            "title": url,
            "timestamp": f"2024-01-01T10:0{i}:00Z",
            "duration_seconds": 60,
        })
    client.post(f"/sessions/{sid}/close")
    return sid


def test_compare_not_found_a(client):
    r = client.get("/sessions/missing-a/compare/missing-b")
    assert r.status_code == 404


def test_compare_not_found_b(client):
    sid_a = _create_closed_session(client, ["https://github.com"])
    r = client.get(f"/sessions/{sid_a}/compare/missing-b")
    assert r.status_code == 404


def test_compare_open_session(client):
    r = client.post("/sessions")
    sid_open = r.get_json()["session_id"]
    sid_closed = _create_closed_session(client, ["https://github.com"])
    r = client.get(f"/sessions/{sid_closed}/compare/{sid_open}")
    assert r.status_code == 400
    assert "open" in r.get_json()["error"].lower()


def test_compare_two_sessions(client):
    sid_a = _create_closed_session(client, [
        "https://github.com", "https://github.com/explore"
    ])
    sid_b = _create_closed_session(client, [
        "https://news.ycombinator.com", "https://reddit.com"
    ])
    r = client.get(f"/sessions/{sid_a}/compare/{sid_b}")
    assert r.status_code == 200
    data = r.get_json()
    assert data["session_a_id"] == sid_a
    assert data["session_b_id"] == sid_b
    assert "duration_diff_seconds" in data
    assert "visits_diff" in data
    assert "category_percentage_delta" in data
    assert "summary_a" in data
    assert "summary_b" in data


def test_compare_delta_endpoint(client):
    sid_a = _create_closed_session(client, ["https://github.com"])
    sid_b = _create_closed_session(client, ["https://reddit.com"])
    r = client.get(f"/sessions/{sid_a}/compare/{sid_b}/delta")
    assert r.status_code == 200
    data = r.get_json()
    assert "summary_a" not in data
    assert "summary_b" not in data
    assert "visits_diff" in data
    assert "new_top_domains" in data
    assert "dropped_top_domains" in data


def test_compare_same_session(client):
    sid = _create_closed_session(client, ["https://github.com"])
    r = client.get(f"/sessions/{sid}/compare/{sid}")
    assert r.status_code == 200
    data = r.get_json()
    assert data["visits_diff"] == 0
    assert data["duration_diff_seconds"] == 0
