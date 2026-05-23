"""Tests for category time-breakdown endpoints and summarizer."""

import pytest
from datetime import datetime, timedelta

from backend.app import create_app
from backend.storage.session_store import SessionStore
from backend.models.session import BrowsingSession, TabEvent


@pytest.fixture
def tmp_store(tmp_path):
    return SessionStore(str(tmp_path))


@pytest.fixture
def client(tmp_store):
    app = create_app(tmp_store)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _create_session_with_events(client, tmp_store):
    r = client.post("/sessions")
    sid = r.get_json()["session_id"]
    base = datetime(2024, 6, 1, 10, 0, 0)
    events = [
        {"url": "https://github.com/user/repo", "title": "GitHub",
         "timestamp": (base).isoformat()},
        {"url": "https://twitter.com/home", "title": "Twitter",
         "timestamp": (base + timedelta(minutes=20)).isoformat()},
        {"url": "https://docs.python.org/3/", "title": "Python Docs",
         "timestamp": (base + timedelta(minutes=35)).isoformat()},
    ]
    for ev in events:
        client.post(f"/sessions/{sid}/events", json=ev)
    client.post(f"/sessions/{sid}/close")
    return sid


def test_categories_not_found(client):
    r = client.get("/sessions/nonexistent/categories")
    assert r.status_code == 404
    assert "error" in r.get_json()


def test_top_categories_not_found(client):
    r = client.get("/sessions/nonexistent/categories/top")
    assert r.status_code == 404


def test_categories_empty_session(client, tmp_store):
    r = client.post("/sessions")
    sid = r.get_json()["session_id"]
    client.post(f"/sessions/{sid}/close")
    r = client.get(f"/sessions/{sid}/categories")
    assert r.status_code == 200
    data = r.get_json()
    assert data["categories"] == {}
    assert data["total_seconds"] == 0.0


def test_categories_returns_breakdown(client, tmp_store):
    sid = _create_session_with_events(client, tmp_store)
    r = client.get(f"/sessions/{sid}/categories")
    assert r.status_code == 200
    data = r.get_json()
    assert "categories" in data
    assert "total_seconds" in data
    # github -> development, twitter -> social — both should appear
    cats = data["categories"]
    assert isinstance(cats, dict)
    assert len(cats) >= 1


def test_top_categories_structure(client, tmp_store):
    sid = _create_session_with_events(client, tmp_store)
    r = client.get(f"/sessions/{sid}/categories/top")
    assert r.status_code == 200
    data = r.get_json()
    assert "top_categories" in data
    for item in data["top_categories"]:
        assert "category" in item
        assert "seconds" in item


def test_top_categories_sorted(client, tmp_store):
    sid = _create_session_with_events(client, tmp_store)
    r = client.get(f"/sessions/{sid}/categories/top")
    items = r.get_json()["top_categories"]
    seconds = [i["seconds"] for i in items]
    assert seconds == sorted(seconds, reverse=True)
