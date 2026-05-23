"""Tests for the productivity scoring feature."""

from __future__ import annotations

import pytest

from backend.app import create_app
from backend.storage.session_store import SessionStore


@pytest.fixture()
def tmp_store(tmp_path):
    return SessionStore(str(tmp_path))


@pytest.fixture()
def client(tmp_store):
    app = create_app(tmp_store)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _create_session_with_events(client, urls: list[str]) -> str:
    resp = client.post("/sessions", json={"label": "test"})
    session_id = resp.get_json()["id"]
    for url in urls:
        client.post(
            f"/sessions/{session_id}/events",
            json={"url": url, "title": url, "event_type": "visit"},
        )
    client.post(f"/sessions/{session_id}/close")
    return session_id


def test_productivity_not_found(client):
    resp = client.get("/sessions/missing/productivity")
    assert resp.status_code == 404


def test_productivity_score_not_found(client):
    resp = client.get("/sessions/missing/productivity/score")
    assert resp.status_code == 404


def test_productivity_empty_session(client):
    resp = client.post("/sessions", json={"label": "empty"})
    sid = resp.get_json()["id"]
    client.post(f"/sessions/{sid}/close")

    resp = client.get(f"/sessions/{sid}/productivity")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["score"] == 0
    assert data["label"] == "no data"
    assert data["total_events"] == 0


def test_productivity_productive_session(client):
    urls = [
        "https://github.com/user/repo",
        "https://stackoverflow.com/questions/123",
        "https://docs.python.org/3/",
        "https://jira.example.com/browse/PROJ-1",
    ]
    sid = _create_session_with_events(client, urls)

    resp = client.get(f"/sessions/{sid}/productivity")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["score"] >= 50
    assert data["label"] in {"productive", "neutral"}
    assert "breakdown" in data
    assert data["total_events"] == len(urls)


def test_productivity_distracted_session(client):
    urls = [
        "https://twitter.com/feed",
        "https://facebook.com/home",
        "https://youtube.com/watch?v=abc",
        "https://reddit.com/r/funny",
        "https://instagram.com/explore",
    ]
    sid = _create_session_with_events(client, urls)

    resp = client.get(f"/sessions/{sid}/productivity")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["score"] < 60


def test_productivity_score_endpoint(client):
    urls = ["https://github.com/user/repo", "https://docs.python.org/3/"]
    sid = _create_session_with_events(client, urls)

    resp = client.get(f"/sessions/{sid}/productivity/score")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "score" in data
    assert "label" in data
    assert "breakdown" not in data
    assert 0 <= data["score"] <= 100
