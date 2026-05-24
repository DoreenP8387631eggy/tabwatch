"""Tests for the interruptions feature (unit + API)."""

import pytest
from datetime import datetime, timezone, timedelta
from backend.app import create_app
from backend.storage.session_store import SessionStore
from backend.models.session import BrowsingSession, TabEvent
from backend.summarizer.interruptions import compute_interruptions


@pytest.fixture()
def tmp_store(tmp_path):
    return SessionStore(str(tmp_path))


@pytest.fixture()
def client(tmp_store):
    app = create_app(tmp_store)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _ts(base: datetime, offset_seconds: int = 0) -> str:
    return (base + timedelta(seconds=offset_seconds)).isoformat()


def _make_session(tmp_store, events):
    s = BrowsingSession()
    for e in events:
        s.add_event(e)
    s.close()
    tmp_store.save(s)
    return s


def _evt(url: str, ts: str) -> TabEvent:
    return TabEvent(url=url, title="T", timestamp=ts, event_type="visit")


def test_compute_interruptions_empty_session():
    s = BrowsingSession()
    result = compute_interruptions(s)
    assert result["interruption_count"] == 0
    assert result["most_interrupted_domain"] is None


def test_compute_interruptions_no_interruptions():
    base = datetime(2024, 1, 10, 9, 0, tzinfo=timezone.utc)
    s = BrowsingSession()
    for i, url in enumerate([
        "https://github.com/repo",
        "https://github.com/issues",
        "https://github.com/pulls",
    ]):
        s.add_event(_evt(url, _ts(base, i * 300)))
    result = compute_interruptions(s)
    assert result["interruption_count"] == 0


def test_compute_interruptions_detects_interruption():
    base = datetime(2024, 1, 10, 9, 0, tzinfo=timezone.utc)
    events = [
        _evt("https://github.com/repo", _ts(base, 0)),
        _evt("https://twitter.com/home", _ts(base, 60)),   # quick diversion
        _evt("https://github.com/repo", _ts(base, 120)),   # quick return
    ]
    s = BrowsingSession()
    for e in events:
        s.add_event(e)
    result = compute_interruptions(s)
    assert result["interruption_count"] == 1
    assert "github.com" in result["interrupted_domains"]
    assert result["most_interrupted_domain"] == "github.com"


def test_compute_interruptions_rate():
    base = datetime(2024, 1, 10, 9, 0, tzinfo=timezone.utc)
    events = [
        _evt("https://docs.python.org", _ts(base, 0)),
        _evt("https://reddit.com", _ts(base, 60)),
        _evt("https://docs.python.org", _ts(base, 120)),
        _evt("https://docs.python.org", _ts(base, 3720)),  # 1h+ later
    ]
    s = BrowsingSession()
    for e in events:
        s.add_event(e)
    result = compute_interruptions(s)
    assert result["interruption_rate_per_hour"] > 0


def test_api_interruptions_not_found(client):
    r = client.get("/sessions/missing-id/interruptions")
    assert r.status_code == 404


def test_api_interruption_count_not_found(client):
    r = client.get("/sessions/missing-id/interruptions/count")
    assert r.status_code == 404


def test_api_interruptions_returns_data(client, tmp_store):
    base = datetime(2024, 1, 10, 9, 0, tzinfo=timezone.utc)
    events = [
        _evt("https://github.com/repo", _ts(base, 0)),
        _evt("https://twitter.com/home", _ts(base, 60)),
        _evt("https://github.com/repo", _ts(base, 120)),
    ]
    s = _make_session(tmp_store, events)
    r = client.get(f"/sessions/{s.id}/interruptions")
    assert r.status_code == 200
    data = r.get_json()
    assert data["interruption_count"] == 1
    assert "github.com" in data["interrupted_domains"]


def test_api_most_interrupted(client, tmp_store):
    base = datetime(2024, 1, 10, 9, 0, tzinfo=timezone.utc)
    events = [
        _evt("https://github.com/repo", _ts(base, 0)),
        _evt("https://twitter.com/home", _ts(base, 60)),
        _evt("https://github.com/repo", _ts(base, 120)),
    ]
    s = _make_session(tmp_store, events)
    r = client.get(f"/sessions/{s.id}/interruptions/most-interrupted")
    assert r.status_code == 200
    data = r.get_json()
    assert data["most_interrupted_domain"] == "github.com"
