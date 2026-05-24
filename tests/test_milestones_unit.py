"""Unit tests for backend/summarizer/milestones.py"""

from __future__ import annotations

from datetime import datetime, timezone

from backend.models.session import BrowsingSession, TabEvent
from backend.summarizer.milestones import evaluate_milestones


def _make_session(events: list[TabEvent] | None = None) -> BrowsingSession:
    s = BrowsingSession(session_id="test-unit", start_time=datetime.now(timezone.utc).isoformat())
    for e in (events or []):
        s.add_event(e)
    s.close()
    return s


def _evt(url: str, duration: int = 60) -> TabEvent:
    return TabEvent(url=url, title=url, timestamp=datetime.now(timezone.utc).isoformat(), duration=duration)


def test_evaluate_milestones_first_session():
    s = _make_session([_evt("https://github.com/repo")])
    result = evaluate_milestones(s, total_sessions=1)
    ids = [m["id"] for m in result]
    assert "first_session" in ids


def test_evaluate_milestones_ten_sessions():
    s = _make_session([_evt("https://github.com/repo")])
    result = evaluate_milestones(s, total_sessions=10)
    ids = [m["id"] for m in result]
    assert "ten_sessions" in ids
    assert "first_session" in ids


def test_evaluate_milestones_focus_hour():
    events = [_evt("https://github.com/repo", duration=3700)]
    s = _make_session(events)
    result = evaluate_milestones(s, total_sessions=1)
    ids = [m["id"] for m in result]
    assert "focus_hour" in ids


def test_evaluate_milestones_low_distraction():
    events = [
        _evt("https://github.com/repo", duration=500),
        _evt("https://twitter.com/feed", duration=10),
    ]
    s = _make_session(events)
    result = evaluate_milestones(s, total_sessions=1)
    ids = [m["id"] for m in result]
    assert "low_distraction" in ids


def test_evaluate_milestones_domain_explorer():
    events = [_evt(f"https://site{i}.com/page", duration=10) for i in range(22)]
    s = _make_session(events)
    result = evaluate_milestones(s, total_sessions=1)
    ids = [m["id"] for m in result]
    assert "domain_explorer" in ids


def test_evaluate_milestones_empty_session():
    s = _make_session([])
    result = evaluate_milestones(s, total_sessions=1)
    ids = [m["id"] for m in result]
    # first_session and low_distraction (0% distraction) should trigger
    assert "first_session" in ids
    assert "focus_hour" not in ids
