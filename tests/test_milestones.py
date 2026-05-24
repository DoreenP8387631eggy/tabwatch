"""Integration tests for the milestones API endpoints."""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

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


def _create_session_with_events(tmp_store: SessionStore) -> str:
    s = BrowsingSession(
        session_id="ms-001",
        start_time=datetime.now(timezone.utc).isoformat(),
    )
    s.add_event(TabEvent(
        url="https://github.com/repo",
        title="GitHub",
        timestamp=datetime.now(timezone.utc).isoformat(),
        duration=3700,
    ))
    s.add_event(TabEvent(
        url="https://twitter.com/home",
        title="Twitter",
        timestamp=datetime.now(timezone.utc).isoformat(),
        duration=30,
    ))
    s.close()
    tmp_store.save(s)
    return s.session_id


def test_milestones_not_found(client):
    resp = client.get("/sessions/no-such-id/milestones")
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "session not found"


def test_milestone_count_not_found(client):
    resp = client.get("/sessions/no-such-id/milestones/count")
    assert resp.status_code == 404


def test_milestones_returns_list(client, tmp_store):
    sid = _create_session_with_events(tmp_store)
    resp = client.get(f"/sessions/{sid}/milestones")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["session_id"] == sid
    assert isinstance(data["milestones"], list)
    ids = [m["id"] for m in data["milestones"]]
    assert "first_session" in ids


def test_milestone_count_positive(client, tmp_store):
    sid = _create_session_with_events(tmp_store)
    resp = client.get(f"/sessions/{sid}/milestones/count")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] >= 1


def test_milestones_all_have_required_fields(client, tmp_store):
    sid = _create_session_with_events(tmp_store)
    resp = client.get(f"/sessions/{sid}/milestones")
    for m in resp.get_json()["milestones"]:
        assert "id" in m
        assert "title" in m
        assert "description" in m
        assert m["achieved"] is True
