"""Tests for the session replay API and summarizer."""

import pytest
from datetime import datetime, timedelta

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


def _create_session_with_events(client, n=3):
    r = client.post("/sessions")
    sid = r.get_json()["session_id"]
    base = datetime(2024, 6, 1, 10, 0, 0)
    for i in range(n):
        ts = (base + timedelta(minutes=i * 5)).strftime("%Y-%m-%dT%H:%M:%S")
        client.post(f"/sessions/{sid}/events", json={
            "url": f"https://example{i}.com/page",
            "title": f"Page {i}",
            "event_type": "visit",
            "timestamp": ts,
        })
    return sid


def test_replay_not_found(client):
    r = client.get("/sessions/ghost/replay")
    assert r.status_code == 404
    assert "error" in r.get_json()


def test_replay_empty_session(client):
    r = client.post("/sessions")
    sid = r.get_json()["session_id"]
    r = client.get(f"/sessions/{sid}/replay")
    assert r.status_code == 200
    data = r.get_json()
    assert data["total_frames"] == 0
    assert data["frames"] == []


def test_replay_frame_count(client):
    sid = _create_session_with_events(client, n=4)
    r = client.get(f"/sessions/{sid}/replay")
    assert r.status_code == 200
    data = r.get_json()
    assert data["total_frames"] == 4
    assert len(data["frames"]) == 4


def test_replay_frame_fields(client):
    sid = _create_session_with_events(client, n=2)
    r = client.get(f"/sessions/{sid}/replay")
    frame = r.get_json()["frames"][0]
    for key in ("index", "timestamp", "url", "domain", "title", "event_type", "duration_since_prev"):
        assert key in frame


def test_replay_first_frame_no_gap(client):
    sid = _create_session_with_events(client, n=3)
    r = client.get(f"/sessions/{sid}/replay")
    first = r.get_json()["frames"][0]
    assert first["duration_since_prev"] is None


def test_replay_subsequent_frame_has_gap(client):
    sid = _create_session_with_events(client, n=3)
    r = client.get(f"/sessions/{sid}/replay")
    second = r.get_json()["frames"][1]
    assert second["duration_since_prev"] is not None
    assert second["duration_since_prev"] > 0


def test_replay_frame_gap_value(client):
    """Verify that duration_since_prev reflects the actual time delta between events."""
    sid = _create_session_with_events(client, n=3)
    r = client.get(f"/sessions/{sid}/replay")
    frames = r.get_json()["frames"]
    # Events are spaced 5 minutes (300 seconds) apart
    for frame in frames[1:]:
        assert frame["duration_since_prev"] == pytest.approx(300, abs=1)


def test_get_single_frame(client):
    sid = _create_session_with_events(client, n=3)
    r = client.get(f"/sessions/{sid}/replay/1")
    assert r.status_code == 200
    assert r.get_json()["index"] == 1


def test_get_frame_out_of_range(client):
    sid = _create_session_with_events(client, n=2)
    r = client.get(f"/sessions/{sid}/replay/99")
    assert r.status_code == 404


def test_get_frame_session_not_found(client):
    r = client.get("/sessions/missing/replay/0")
    assert r.status_code == 404
