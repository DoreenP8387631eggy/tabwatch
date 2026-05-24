"""Integration tests for the /api/digest endpoints."""

import pytest
from datetime import datetime, timedelta

from backend.app import create_app
from backend.storage.session_store import SessionStore
from backend.models.session import BrowsingSession, TabEvent


@pytest.fixture()
def tmp_store(tmp_path):
    return SessionStore(str(tmp_path))


@pytest.fixture()
def client(tmp_store):
    app = create_app(tmp_store)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _create_closed_session(tmp_store, date_str="2024-06-15", duration_h=1):
    start = datetime.fromisoformat(f"{date_str}T09:00:00")
    s = BrowsingSession(session_id=None, start_time=start.isoformat())
    s.add_event(TabEvent(url="https://github.com", title="GitHub", timestamp=start.isoformat()))
    s.add_event(TabEvent(url="https://stackoverflow.com", title="SO",
                         timestamp=(start + timedelta(minutes=30)).isoformat()))
    s.close((start + timedelta(hours=duration_h)).isoformat())
    tmp_store.save(s)
    return s


def test_digest_no_sessions(client):
    resp = client.get("/api/digest?date=2024-06-15")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["session_count"] == 0
    assert data["date"] == "2024-06-15"


def test_digest_invalid_date(client):
    resp = client.get("/api/digest?date=not-a-date")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_digest_with_sessions(client, tmp_store):
    _create_closed_session(tmp_store, date_str="2024-06-15")
    resp = client.get("/api/digest?date=2024-06-15")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["session_count"] == 1
    assert data["total_duration_seconds"] == 3600
    assert len(data["top_domains"]) > 0


def test_digest_today_endpoint(client, tmp_store):
    resp = client.get("/api/digest/today")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "date" in data
    assert "session_count" in data
    assert "tag_totals" in data
    assert "highlights" in data


def test_digest_excludes_other_dates(client, tmp_store):
    _create_closed_session(tmp_store, date_str="2024-06-14")
    resp = client.get("/api/digest?date=2024-06-15")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["session_count"] == 0
