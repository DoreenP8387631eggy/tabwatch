"""Tests for session tag classification API and logic."""

import pytest
from backend.app import create_app
from backend.storage.session_store import SessionStore
import tempfile
import os


@pytest.fixture
def tmp_store(tmp_path):
    return SessionStore(store_dir=str(tmp_path))


@pytest.fixture
def client(tmp_store):
    app = create_app(store=tmp_store)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _create_session_with_events(client, urls):
    resp = client.post("/sessions", json={"label": "tag-test"})
    session_id = resp.get_json()["session_id"]
    for url in urls:
        client.post(f"/sessions/{session_id}/events", json={
            "url": url,
            "title": "Page",
            "event_type": "visit",
        })
    return session_id


def test_tags_not_found(client):
    resp = client.get("/sessions/nonexistent/tags")
    assert resp.status_code == 404


def test_tags_empty_session(client):
    resp = client.post("/sessions", json={"label": "empty"})
    session_id = resp.get_json()["session_id"]
    resp = client.get(f"/sessions/{session_id}/tags")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["tags"] == ["other"] or data["tags"] == []
    assert data["domain_count"] == 0


def test_tags_coding_session(client):
    urls = [
        "https://github.com/user/repo",
        "https://github.com/user/repo/issues",
        "https://stackoverflow.com/questions/123",
    ]
    session_id = _create_session_with_events(client, urls)
    resp = client.get(f"/sessions/{session_id}/tags")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "coding" in data["tags"]
    assert data["tags"][0] == "coding"
    assert data["domain_count"] == 3


def test_tags_mixed_session(client):
    urls = [
        "https://github.com/user/repo",
        "https://youtube.com/watch?v=abc",
        "https://youtube.com/watch?v=xyz",
        "https://reddit.com/r/python",
    ]
    session_id = _create_session_with_events(client, urls)
    resp = client.get(f"/sessions/{session_id}/tags")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "entertainment" in data["tags"]
    assert data["tags"][0] == "entertainment"  # most visited


def test_tags_breakdown(client):
    urls = [
        "https://github.com/user/repo",
        "https://mail.google.com/inbox",
    ]
    session_id = _create_session_with_events(client, urls)
    resp = client.get(f"/sessions/{session_id}/tags/breakdown")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "breakdown" in data
    assert data["breakdown"].get("github.com") == "coding"
    assert data["breakdown"].get("mail.google.com") == "email"


def test_tags_breakdown_not_found(client):
    resp = client.get("/sessions/ghost/tags/breakdown")
    assert resp.status_code == 404
