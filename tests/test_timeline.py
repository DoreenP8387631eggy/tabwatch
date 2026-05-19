"""Tests for the timeline feature."""

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


def _create_session_with_events(client, urls_with_offsets):
    """Create a session and add events at given timestamp offsets (seconds)."""
    resp = client.post("/sessions", json={"label": "timeline-test"})
    assert resp.status_code == 201
    session_id = resp.get_json()["session_id"]

    base_ts = 1_700_000_000.0  # fixed base for deterministic bucket keys
    for url, offset in urls_with_offsets:
        client.post(f"/sessions/{session_id}/events", json={
            "url": url,
            "title": url,
            "timestamp": base_ts + offset,
            "event_type": "visit",
        })

    return session_id


def test_timeline_not_found(client):
    resp = client.get("/sessions/missing/timeline")
    assert resp.status_code == 404


def test_peak_not_found(client):
    resp = client.get("/sessions/missing/timeline/peak")
    assert resp.status_code == 404


def test_timeline_empty_session(client):
    resp = client.post("/sessions", json={"label": "empty"})
    session_id = resp.get_json()["session_id"]
    resp = client.get(f"/sessions/{session_id}/timeline")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["timeline"] == []


def test_timeline_groups_into_buckets(client):
    # All three events fall within the same 5-min bucket
    urls = [
        ("https://github.com/a", 0),
        ("https://github.com/b", 60),
        ("https://news.ycombinator.com", 120),
    ]
    session_id = _create_session_with_events(client, urls)
    resp = client.get(f"/sessions/{session_id}/timeline")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["timeline"]) >= 1
    total_events = sum(b["event_count"] for b in data["timeline"])
    assert total_events == 3


def test_timeline_domain_counts(client):
    urls = [
        ("https://github.com/x", 0),
        ("https://github.com/y", 30),
        ("https://stackoverflow.com/q", 60),
    ]
    session_id = _create_session_with_events(client, urls)
    resp = client.get(f"/sessions/{session_id}/timeline")
    data = resp.get_json()
    all_domains = {}
    for bucket in data["timeline"]:
        for domain, count in bucket["domains"].items():
            all_domains[domain] = all_domains.get(domain, 0) + count
    assert all_domains.get("github.com", 0) == 2
    assert all_domains.get("stackoverflow.com", 0) == 1


def test_peak_bucket(client):
    urls = [
        ("https://github.com/a", 0),
        ("https://github.com/b", 30),
        ("https://github.com/c", 60),
        ("https://news.ycombinator.com", 700),  # different bucket
    ]
    session_id = _create_session_with_events(client, urls)
    resp = client.get(f"/sessions/{session_id}/timeline/peak")
    assert resp.status_code == 200
    peak = resp.get_json()["peak"]
    assert peak is not None
    assert peak["event_count"] >= 3
