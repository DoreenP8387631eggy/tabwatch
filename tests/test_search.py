"""Tests for the search feature (unit + API)."""

from __future__ import annotations

import time
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


def _create_session_with_events(client):
    rv = client.post("/sessions")
    sid = rv.get_json()["session_id"]
    events = [
        {"url": "https://github.com/user/repo", "title": "GitHub Repo", "duration": 120},
        {"url": "https://news.ycombinator.com", "title": "Hacker News", "duration": 60},
        {"url": "https://docs.python.org/3/", "title": "Python Docs", "duration": 90},
    ]
    for evt in events:
        client.post(f"/sessions/{sid}/events", json=evt)
    return sid


def test_search_missing_query(client):
    sid = _create_session_with_events(client)
    rv = client.get(f"/sessions/{sid}/search")
    assert rv.status_code == 400
    assert "required" in rv.get_json()["error"]


def test_search_invalid_field(client):
    sid = _create_session_with_events(client)
    rv = client.get(f"/sessions/{sid}/search?q=github&field=bogus")
    assert rv.status_code == 400


def test_search_not_found(client):
    rv = client.get("/sessions/no-such-id/search?q=python")
    assert rv.status_code == 404


def test_search_by_url(client):
    sid = _create_session_with_events(client)
    rv = client.get(f"/sessions/{sid}/search?q=github&field=url")
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["match_count"] == 1
    assert "github" in data["events"][0]["url"]


def test_search_by_title(client):
    sid = _create_session_with_events(client)
    rv = client.get(f"/sessions/{sid}/search?q=hacker&field=title")
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["match_count"] == 1
    assert data["events"][0]["title"] == "Hacker News"


def test_search_by_domain(client):
    sid = _create_session_with_events(client)
    rv = client.get(f"/sessions/{sid}/search?q=python.org&field=domain")
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["match_count"] == 1


def test_search_all_sessions(client):
    _create_session_with_events(client)
    _create_session_with_events(client)
    rv = client.get("/search?q=github")
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["session_count"] == 2
    for result in data["results"]:
        assert result["match_count"] >= 1


def test_search_no_matches(client):
    sid = _create_session_with_events(client)
    rv = client.get(f"/sessions/{sid}/search?q=noresultsxyz")
    assert rv.status_code == 200
    assert rv.get_json()["match_count"] == 0
