"""Tests for context switch computation."""
import pytest
from datetime import datetime, timedelta
from backend.models.session import BrowsingSession, TabEvent
from backend.summarizer.context import compute_context_switches


def _evt(url: str, offset_seconds: int = 0) -> TabEvent:
    base = datetime(2024, 6, 1, 9, 0, 0)
    ts = (base + timedelta(seconds=offset_seconds)).strftime("%Y-%m-%dT%H:%M:%S")
    return TabEvent(url=url, title=url, timestamp=ts, event_type="visit")


def _make_session(events=None) -> BrowsingSession:
    s = BrowsingSession(session_id="test-ctx")
    for e in (events or []):
        s.add_event(e)
    return s


def test_compute_context_empty_session():
    s = _make_session()
    result = compute_context_switches(s)
    assert result["switches"] == 0
    assert result["sequence"] == []
    assert result["dominant_context"] is None
    assert result["switch_rate_per_minute"] == 0.0


def test_compute_context_no_switches():
    events = [
        _evt("https://github.com/repo", 0),
        _evt("https://github.com/issues", 60),
        _evt("https://github.com/pulls", 120),
    ]
    result = compute_context_switches(_make_session(events))
    assert result["switches"] == 0
    assert len(result["sequence"]) == 1


def test_compute_context_single_switch():
    events = [
        _evt("https://github.com/repo", 0),
        _evt("https://twitter.com/feed", 120),
    ]
    result = compute_context_switches(_make_session(events))
    assert result["switches"] == 1
    assert len(result["sequence"]) == 2


def test_compute_context_multiple_switches():
    events = [
        _evt("https://github.com/repo", 0),
        _evt("https://twitter.com/feed", 60),
        _evt("https://news.ycombinator.com", 120),
        _evt("https://github.com/issues", 180),
    ]
    result = compute_context_switches(_make_session(events))
    assert result["switches"] >= 2
    assert "context_frequency" in result
    assert result["dominant_context"] is not None


def test_compute_context_dominant_context():
    events = [
        _evt("https://github.com/a", 0),
        _evt("https://twitter.com", 60),
        _evt("https://github.com/b", 120),
        _evt("https://github.com/c", 180),
        _evt("https://twitter.com", 240),
        _evt("https://github.com/d", 300),
    ]
    result = compute_context_switches(_make_session(events))
    # dev/work context should dominate
    assert result["dominant_context"] is not None
    assert result["switches"] > 0


def test_compute_context_switch_rate_increases_with_more_switches():
    few_events = [
        _evt("https://github.com", 0),
        _evt("https://twitter.com", 300),
    ]
    many_events = [
        _evt("https://github.com", 0),
        _evt("https://twitter.com", 60),
        _evt("https://github.com", 120),
        _evt("https://twitter.com", 180),
        _evt("https://github.com", 240),
        _evt("https://twitter.com", 300),
    ]
    few_result = compute_context_switches(_make_session(few_events))
    many_result = compute_context_switches(_make_session(many_events))
    assert many_result["switch_rate_per_minute"] > few_result["switch_rate_per_minute"]
