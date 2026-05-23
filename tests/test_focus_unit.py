"""Unit tests for backend/summarizer/focus.py."""

from datetime import datetime, timedelta

from backend.models.session import BrowsingSession, TabEvent
from backend.summarizer.focus import (
    DEEP_FOCUS_SECONDS,
    FOCUS_THRESHOLD_SECONDS,
    compute_focus,
)


def _make_session(events: list) -> BrowsingSession:
    s = BrowsingSession(session_id="unit-focus")
    s.events = events
    return s


def _evt(url: str, offset_seconds: float) -> TabEvent:
    return TabEvent(
        url=url,
        title="",
        timestamp=datetime(2024, 1, 1, 10, 0, 0) + timedelta(seconds=offset_seconds),
    )


def test_compute_focus_empty_session():
    result = compute_focus(_make_session([]))
    assert result["focused_visits"] == 0
    assert result["focus_ratio"] == 0.0
    assert result["top_focus_domains"] == []


def test_compute_focus_all_shallow():
    events = [
        _evt("https://example.com", 0),
        _evt("https://example.com", 10),   # 10s gap — shallow
        _evt("https://other.com", 20),
    ]
    result = compute_focus(_make_session(events))
    assert result["focused_visits"] == 0
    assert result["shallow_visits"] == 3
    assert result["focus_ratio"] == 0.0


def test_compute_focus_mixed():
    events = [
        _evt("https://docs.python.org", 0),
        _evt("https://docs.python.org", FOCUS_THRESHOLD_SECONDS + 10),  # focused
        _evt("https://twitter.com", FOCUS_THRESHOLD_SECONDS + 15),      # shallow (5s)
    ]
    result = compute_focus(_make_session(events))
    assert result["focused_visits"] == 1
    assert result["shallow_visits"] == 2
    assert 0 < result["focus_ratio"] < 1


def test_compute_focus_deep_focus():
    events = [
        _evt("https://github.com", 0),
        _evt("https://github.com", DEEP_FOCUS_SECONDS + 60),  # deep focus
    ]
    result = compute_focus(_make_session(events))
    assert result["deep_focus_visits"] == 1
    assert result["focused_visits"] >= 1


def test_top_focus_domains_ordering():
    events = [
        _evt("https://github.com", 0),
        _evt("https://github.com", 200),   # 200s on github
        _evt("https://docs.python.org", 200),
        _evt("https://docs.python.org", 300),  # 100s on docs
    ]
    result = compute_focus(_make_session(events))
    domains = [d["domain"] for d in result["top_focus_domains"]]
    assert domains[0] == "github.com"
