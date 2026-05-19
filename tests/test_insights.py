"""Tests for the insights API and insight generation logic."""

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


def _create_session_with_events(client, urls: list[str], close: bool = True) -> str:
    resp = client.post("/sessions", json={"label": "insight-test"})
    sid = resp.get_json()["session_id"]
    base_time = datetime(2024, 6, 1, 9, 0, 0)
    for i, url in enumerate(urls):
        ts = (base_time + timedelta(minutes=i * 5)).isoformat()
        client.post(f"/sessions/{sid}/events", json={"url": url, "timestamp": ts})
    if close:
        client.post(f"/sessions/{sid}/close")
    return sid


def test_insights_not_found(client):
    resp = client.get("/sessions/nonexistent/insights")
    assert resp.status_code == 404


def test_insights_open_session(client):
    sid = _create_session_with_events(
        client, ["https://github.com"], close=False
    )
    resp = client.get(f"/sessions/{sid}/insights")
    assert resp.status_code == 400
    assert "open" in resp.get_json()["error"].lower()


def test_insights_empty_session(client):
    resp = client.post("/sessions", json={"label": "empty"})
    sid = resp.get_json()["session_id"]
    client.post(f"/sessions/{sid}/close")
    resp = client.get(f"/sessions/{sid}/insights")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["score"] is None
    assert data["insights"] == []


def test_insights_productive_session(client):
    urls = [
        "https://github.com/repo",
        "https://stackoverflow.com/questions/1",
        "https://docs.python.org/3/",
        "https://github.com/issues",
    ]
    sid = _create_session_with_events(client, urls)
    resp = client.get(f"/sessions/{sid}/insights")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "score" in data
    assert isinstance(data["score"], int)
    assert len(data["insights"]) >= 1
    assert len(data["top_domains"]) >= 1
    assert "tag_breakdown" in data


def test_score_endpoint(client):
    urls = ["https://github.com", "https://news.ycombinator.com"]
    sid = _create_session_with_events(client, urls)
    resp = client.get(f"/sessions/{sid}/insights/score")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "score" in data
    assert "duration_seconds" in data
    assert data["session_id"] == sid


def test_insights_distracted_session(client):
    urls = [
        "https://twitter.com/feed",
        "https://instagram.com/explore",
        "https://youtube.com/watch?v=abc",
        "https://reddit.com/r/funny",
    ]
    sid = _create_session_with_events(client, urls)
    resp = client.get(f"/sessions/{sid}/insights")
    assert resp.status_code == 200
    data = resp.get_json()
    assert any("distraction" in i.lower() for i in data["insights"])
