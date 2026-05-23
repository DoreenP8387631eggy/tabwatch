"""Tests for generate_recommendations."""

import pytest
from datetime import datetime, timedelta

from backend.models.session import BrowsingSession, TabEvent
from backend.summarizer.recommendations import generate_recommendations


def _make_session(events_spec, closed=True):
    """Helper: create a session with given (url, seconds) events."""
    session = BrowsingSession(session_id="rec-test")
    base = datetime(2024, 6, 1, 9, 0, 0)
    for i, (url, duration) in enumerate(events_spec):
        event = TabEvent(
            url=url,
            title=url,
            timestamp=base + timedelta(seconds=i * 60),
            duration_seconds=duration,
        )
        session.add_event(event)
    if closed:
        session.start_time = base
        session.end_time = base + timedelta(seconds=sum(d for _, d in events_spec) + 60)
    return session


def test_recommendations_open_session():
    session = BrowsingSession(session_id="open")
    session.start_time = datetime(2024, 6, 1, 9, 0, 0)
    recs = generate_recommendations(session)
    assert len(recs) == 1
    assert recs[0]["level"] == "info"
    assert "still open" in recs[0]["message"]


def test_recommendations_empty_session():
    session = BrowsingSession(session_id="empty")
    session.start_time = datetime(2024, 6, 1, 9, 0, 0)
    session.end_time = datetime(2024, 6, 1, 9, 5, 0)
    recs = generate_recommendations(session)
    assert any("No browsing events" in r["message"] for r in recs)


def test_recommendations_short_session():
    events = [("https://github.com", 120), ("https://github.com", 120)]
    session = _make_session(events)
    # Override end_time to make it short (< 10 min)
    session.end_time = session.start_time + timedelta(minutes=5)
    recs = generate_recommendations(session)
    assert any("Short session" in r["message"] for r in recs)


def test_recommendations_no_distraction():
    events = [
        ("https://github.com", 1200),
        ("https://stackoverflow.com", 600),
    ]
    session = _make_session(events)
    recs = generate_recommendations(session)
    messages = [r["message"] for r in recs]
    assert any("No time spent on distracting" in m for m in messages)


def test_recommendations_high_distraction():
    events = [
        ("https://twitter.com", 2400),
        ("https://facebook.com", 1200),
        ("https://github.com", 300),
    ]
    session = _make_session(events)
    recs = generate_recommendations(session)
    levels = [r["level"] for r in recs]
    messages = [r["message"] for r in recs]
    assert "warning" in levels
    assert any("distracting" in m for m in messages)


def test_recommendations_goals_met():
    events = [
        ("https://github.com", 3000),
        ("https://docs.python.org", 1800),
    ]
    session = _make_session(events)
    recs = generate_recommendations(session)
    assert any("goals met" in r["message"].lower() for r in recs)
