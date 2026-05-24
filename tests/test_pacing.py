"""Tests for pacing summarizer and API."""

import pytest
from datetime import datetime, timezone, timedelta
from backend.app import create_app
from backend.storage.session_store import SessionStore
from backend.models.session import BrowsingSession, TabEvent
from backend.summarizer.pacing import compute_pacing


@pytest.fixture
def tmp_store(tmp_path):
    return SessionStore(str(tmp_path))


@pytest.fixture
def client(tmp_store):
    app = create_app(tmp_store)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _ts(offset_seconds: int) -> str:
    base = datetime(2024, 6, 1, 9, 0, 0, tzinfo=timezone.utc)
    return (base + timedelta(seconds=offset_seconds)).isoformat()


def _make_session(event_offsets):
    s = BrowsingSession()
    for offset in event_offsets:
        s.add_event(TabEvent(url="https://example.com", title="Page", timestamp=_ts(offset)))
    return s


# --- Unit tests ---

def test_compute_pacing_empty_session():
    s = _make_session([])
    result = compute_pacing(s)
    assert result["label"] == "sparse"
    assert result["events_per_minute"] == 0.0
    assert result["coverage_ratio"] == 0.0


def test_compute_pacing_steady():
    # One event per minute for 10 minutes
    offsets = [i * 60 for i in range(10)]
    s = _make_session(offsets)
    result = compute_pacing(s)
    assert result["active_minutes"] == 10
    assert result["label"] == "steady"
    assert result["variance"] == 0.0


def test_compute_pacing_bursty():
    # Many events crammed into one minute, then silence
    offsets = [i * 5 for i in range(20)] + [600]
    s = _make_session(offsets)
    result = compute_pacing(s)
    assert result["label"] == "bursty"


def test_compute_pacing_coverage_ratio():
    # Events in 3 out of 10 minutes
    offsets = [0, 60, 120]  # minutes 0, 1, 2 only
    s = _make_session(offsets)
    result = compute_pacing(s)
    assert result["active_minutes"] == 3
    assert 0 < result["coverage_ratio"] <= 1.0


# --- API tests ---

def test_pacing_not_found(client):
    r = client.get("/sessions/missing/pacing")
    assert r.status_code == 404


def test_pacing_label_not_found(client):
    r = client.get("/sessions/missing/pacing/label")
    assert r.status_code == 404


def test_pacing_coverage_not_found(client):
    r = client.get("/sessions/missing/pacing/coverage")
    assert r.status_code == 404


def test_pacing_api_returns_label(client, tmp_store):
    s = _make_session([i * 60 for i in range(8)])
    tmp_store.save(s)
    r = client.get(f"/sessions/{s.id}/pacing/label")
    assert r.status_code == 200
    data = r.get_json()
    assert "label" in data
    assert data["label"] in ("steady", "bursty", "sparse")


def test_pacing_api_full(client, tmp_store):
    s = _make_session([0, 60, 120, 180])
    tmp_store.save(s)
    r = client.get(f"/sessions/{s.id}/pacing")
    assert r.status_code == 200
    data = r.get_json()
    for key in ("events_per_minute", "active_minutes", "total_minutes", "coverage_ratio", "variance", "label"):
        assert key in data
