"""Tests for the session summary feature."""

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


def _create_session_with_events(client, urls: list[str]) -> str:
    resp = client.post("/sessions", json={"label": "test"})
    session_id = resp.get_json()["session_id"]
    for url in urls:
        client.post(f"/sessions/{session_id}/events", json={"url": url, "title": url})
    return session_id


def test_summary_not_found(client):
    resp = client.get("/sessions/nonexistent/summary")
    assert resp.status_code == 404


def test_summary_empty_session(client):
    resp = client.post("/sessions", json={"label": "empty"})
    session_id = resp.get_json()["session_id"]
    resp = client.get(f"/sessions/{session_id}/summary")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total_events"] == 0
    assert data["verdict"] == "no data"


def test_summary_focused_session(client):
    urls = [
        "https://github.com/user/repo",
        "https://stackoverflow.com/questions/1",
        "https://github.com/user/repo/issues",
        "https://docs.python.org/3/library/",
        "https://github.com/trending",
    ]
    session_id = _create_session_with_events(client, urls)
    resp = client.get(f"/sessions/{session_id}/summary")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total_events"] == 5
    assert data["verdict"] == "focused"
    assert data["productive_time_pct"] >= 60.0


def test_summary_distracted_session(client):
    urls = [
        "https://twitter.com/home",
        "https://reddit.com/r/python",
        "https://youtube.com/watch?v=abc",
        "https://twitter.com/explore",
        "https://github.com/user/repo",
    ]
    session_id = _create_session_with_events(client, urls)
    resp = client.get(f"/sessions/{session_id}/summary")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["verdict"] == "distracted"
    assert data["distracting_time_pct"] >= 50.0


def test_list_summaries(client):
    _create_session_with_events(client, ["https://github.com/a"])
    _create_session_with_events(client, ["https://reddit.com/b"])
    resp = client.get("/sessions/summaries")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 2
    assert all("verdict" in s for s in data)
