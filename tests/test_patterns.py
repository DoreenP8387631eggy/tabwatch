"""Tests for the patterns detection feature."""

import time
import pytest
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


def _create_closed_session(store: SessionStore, urls: list, base_ts: float = None) -> str:
    if base_ts is None:
        base_ts = time.time()
    session = BrowsingSession()
    session.start_time = base_ts
    for i, url in enumerate(urls):
        event = TabEvent(url=url, title="Page", timestamp=base_ts + i * 60)
        session.add_event(event)
    session.close()
    store.save(session)
    return session.session_id


def test_patterns_no_sessions(client):
    resp = client.get("/patterns")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["session_count"] == 0
    assert data["patterns"]["recurring_domains"] == []


def test_patterns_with_sessions(client, tmp_store):
    base = time.time()
    _create_closed_session(
        tmp_store,
        ["https://github.com/foo", "https://news.ycombinator.com/"],
        base_ts=base,
    )
    _create_closed_session(
        tmp_store,
        ["https://github.com/bar", "https://stackoverflow.com/q/1"],
        base_ts=base + 86400,
    )
    _create_closed_session(
        tmp_store,
        ["https://github.com/baz", "https://news.ycombinator.com/item"],
        base_ts=base + 172800,
    )
    resp = client.get("/patterns")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["session_count"] == 3
    assert "github.com" in data["patterns"]["recurring_domains"]
    assert data["patterns"]["avg_session_duration"] > 0


def test_recurring_domains_endpoint(client, tmp_store):
    base = time.time()
    for _ in range(3):
        _create_closed_session(
            tmp_store, ["https://docs.python.org/3/"], base_ts=base
        )
        base += 86400
    resp = client.get("/patterns/recurring-domains")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "docs.python.org" in data["recurring_domains"]


def test_peak_hours_endpoint(client, tmp_store):
    base = time.time()
    _create_closed_session(
        tmp_store,
        ["https://example.com/", "https://example.com/page"],
        base_ts=base,
    )
    resp = client.get("/patterns/peak-hours")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data["peak_hours"], list)


def test_open_sessions_excluded(client, tmp_store):
    """Open (unclosed) sessions should not affect pattern results."""
    session = BrowsingSession()
    session.start_time = time.time()
    event = TabEvent(url="https://reddit.com/", title="Reddit", timestamp=time.time())
    session.add_event(event)
    # intentionally NOT closing the session
    tmp_store.save(session)

    resp = client.get("/patterns")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["session_count"] == 0
