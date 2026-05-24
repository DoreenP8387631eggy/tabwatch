"""Unit tests for backend/summarizer/rhythm.py"""

import pytest
from datetime import datetime, timedelta
from backend.models.session import BrowsingSession, TabEvent
from backend.summarizer.rhythm import compute_rhythm, _inter_event_gaps


def _make_session(events=None) -> BrowsingSession:
    s = BrowsingSession(session_id="s1")
    for e in (events or []):
        s.events.append(e)
    return s


def _evt(url: str, offset_seconds: float) -> TabEvent:
    ts = (datetime(2024, 1, 10, 9, 0, 0) + timedelta(seconds=offset_seconds)).isoformat()
    return TabEvent(url=url, title="T", timestamp=ts, event_type="visit")


def test_compute_rhythm_empty_session():
    s = _make_session()
    r = compute_rhythm(s)
    assert r["rhythm_label"] == "idle"
    assert r["event_count"] == 0
    assert r["burst_count"] == 0


def test_compute_rhythm_single_event():
    s = _make_session([_evt("https://example.com", 0)])
    r = compute_rhythm(s)
    assert r["event_count"] == 1
    assert r["rhythm_label"] == "idle"
    assert r["avg_gap_seconds"] == 0


def test_compute_rhythm_frantic():
    events = [_evt(f"https://site{i}.com", i * 2) for i in range(10)]
    s = _make_session(events)
    r = compute_rhythm(s)
    assert r["rhythm_label"] == "frantic"
    assert r["burst_count"] > 0


def test_compute_rhythm_steady():
    events = [_evt(f"https://site{i}.com", i * 30) for i in range(6)]
    s = _make_session(events)
    r = compute_rhythm(s)
    assert r["rhythm_label"] == "steady"


def test_compute_rhythm_relaxed():
    events = [_evt(f"https://site{i}.com", i * 80) for i in range(5)]
    s = _make_session(events)
    r = compute_rhythm(s)
    assert r["rhythm_label"] == "relaxed"


def test_compute_rhythm_idle_label():
    events = [_evt(f"https://site{i}.com", i * 300) for i in range(4)]
    s = _make_session(events)
    r = compute_rhythm(s)
    assert r["rhythm_label"] == "idle"
    assert r["idle_count"] >= 1


def test_inter_event_gaps_ordering():
    events = [
        {"timestamp": "2024-01-10T09:00:00"},
        {"timestamp": "2024-01-10T09:00:10"},
        {"timestamp": "2024-01-10T09:00:25"},
    ]
    gaps = _inter_event_gaps(events)
    assert len(gaps) == 2
    assert gaps[0] == pytest.approx(10.0)
    assert gaps[1] == pytest.approx(15.0)
