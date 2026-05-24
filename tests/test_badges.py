"""Integration tests for the badges API."""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta

from backend.app import create_app
from backend.storage.session_store import SessionStore
from backend.models.session import BrowsingSession, TabEvent
from backend.api.badges import init_badges


@pytest.fixture
def tmp_store(tmp_path):
    return SessionStore(str(tmp_path))


@pytest.fixture
def client(tmp_store):
    app = create_app(tmp_store)
    init_badges(app)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _make_closed_session(tmp_store, urls=None, duration_minutes=10):
    """Create and persist a closed session with given URLs."""
    s = BrowsingSession()
    base = datetime(2024, 6, 1, 10, 0, 0)
    urls = urls or ["https://github.com/user/repo"]
    for i, url in enumerate(urls):
        evt = TabEvent(url=url, title=url, timestamp=base + timedelta(minutes=i))
        s.add_event(evt)
    s.close(end_time=base + timedelta(minutes=duration_minutes))
    tmp_store.save(s)
    return s


def test_badges_empty_store(client):
    resp = client.get("/badges")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["badges"] == []
    assert data["count"] == 0


def test_badge_count_empty_store(client):
    resp = client.get("/badges/count")
    assert resp.status_code == 200
    assert resp.get_json()["count"] == 0


def test_first_session_badge_earned(tmp_store, client):
    _make_closed_session(tmp_store)
    resp = client.get("/badges")
    assert resp.status_code == 200
    data = resp.get_json()
    ids = [b["id"] for b in data["badges"]]
    assert "first_session" in ids


def test_power_user_badge_not_earned_below_threshold(tmp_store, client):
    for _ in range(5):
        _make_closed_session(tmp_store)
    resp = client.get("/badges")
    ids = [b["id"] for b in resp.get_json()["badges"]]
    assert "power_user" not in ids


def test_power_user_badge_earned_at_ten(tmp_store, client):
    for _ in range(10):
        _make_closed_session(tmp_store)
    resp = client.get("/badges")
    ids = [b["id"] for b in resp.get_json()["badges"]]
    assert "power_user" in ids


def test_clean_session_badge_no_social(tmp_store, client):
    _make_closed_session(tmp_store, urls=["https://github.com/x", "https://docs.python.org/"])
    resp = client.get("/badges")
    ids = [b["id"] for b in resp.get_json()["badges"]]
    assert "clean_session" in ids


def test_badge_count_matches_badges_list(tmp_store, client):
    _make_closed_session(tmp_store)
    badges_resp = client.get("/badges").get_json()
    count_resp = client.get("/badges/count").get_json()
    assert badges_resp["count"] == count_resp["count"]
    assert len(badges_resp["badges"]) == count_resp["count"]
