"""Tests for the bookmarks feature."""

import time
import pytest

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


def _create_session_with_events(client, domains_visits: list[tuple[str, int]]):
    """Create a session and add visit events for each (domain, count) pair."""
    r = client.post("/sessions")
    sid = r.get_json()["session_id"]
    now = time.time()
    offset = 0
    for domain, count in domains_visits:
        for _ in range(count):
            client.post(f"/sessions/{sid}/events", json={
                "url": f"https://{domain}/page",
                "title": domain,
                "event_type": "visit",
                "timestamp": now + offset,
            })
            offset += 30
    return sid


def test_bookmarks_not_found(client):
    r = client.get("/sessions/nonexistent/bookmarks")
    assert r.status_code == 404


def test_top_bookmark_not_found(client):
    r = client.get("/sessions/nonexistent/bookmarks/top")
    assert r.status_code == 404


def test_bookmarks_empty_session(client):
    r = client.post("/sessions")
    sid = r.get_json()["session_id"]
    r = client.get(f"/sessions/{sid}/bookmarks")
    assert r.status_code == 200
    data = r.get_json()
    assert data["bookmark_candidates"] == []
    assert data["total_candidates"] == 0


def test_bookmarks_below_threshold(client):
    sid = _create_session_with_events(client, [("example.com", 2)])
    r = client.get(f"/sessions/{sid}/bookmarks")
    assert r.status_code == 200
    data = r.get_json()
    # default threshold is 3, so 2 visits should not qualify
    assert data["total_candidates"] == 0


def test_bookmarks_above_threshold(client):
    sid = _create_session_with_events(client, [
        ("github.com", 5),
        ("stackoverflow.com", 3),
        ("news.ycombinator.com", 1),
    ])
    r = client.get(f"/sessions/{sid}/bookmarks")
    assert r.status_code == 200
    data = r.get_json()
    assert data["total_candidates"] == 2
    domains = [c["domain"] for c in data["bookmark_candidates"]]
    assert "github.com" in domains
    assert "stackoverflow.com" in domains
    # ordered by visits descending
    assert data["bookmark_candidates"][0]["domain"] == "github.com"


def test_top_bookmark(client):
    sid = _create_session_with_events(client, [
        ("github.com", 6),
        ("docs.python.org", 4),
    ])
    r = client.get(f"/sessions/{sid}/bookmarks/top")
    assert r.status_code == 200
    data = r.get_json()
    assert data["top_bookmark"]["domain"] == "github.com"
    assert data["top_bookmark"]["visits"] == 6


def test_top_bookmark_no_candidates(client):
    sid = _create_session_with_events(client, [("once.com", 1)])
    r = client.get(f"/sessions/{sid}/bookmarks/top")
    assert r.status_code == 200
    data = r.get_json()
    assert data["top_bookmark"] is None
