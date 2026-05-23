"""Tests for the streak computation module."""

import time
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import pytest

from backend.models.session import BrowsingSession, TabEvent
from backend.summarizer.streak import compute_streak, _session_date


def _make_session(days_ago: int) -> BrowsingSession:
    """Create a closed BrowsingSession whose start_time is `days_ago` days before now."""
    now = datetime.now(tz=timezone.utc)
    start = (now - timedelta(days=days_ago)).timestamp()
    s = BrowsingSession()
    s.start_time = start
    s.end_time = start + 600
    s.events = [
        TabEvent(url="https://example.com", title="Example", timestamp=start)
    ]
    return s


def test_compute_streak_empty():
    result = compute_streak([])
    assert result["current_streak"] == 0
    assert result["longest_streak"] == 0
    assert result["active_days"] == []
    assert result["total_sessions"] == 0


def test_compute_streak_single_session_today():
    s = _make_session(days_ago=0)
    result = compute_streak([s])
    assert result["current_streak"] == 1
    assert result["longest_streak"] == 1
    assert len(result["active_days"]) == 1
    assert result["total_sessions"] == 1


def test_compute_streak_consecutive_days():
    sessions = [_make_session(days_ago=i) for i in range(4)]
    result = compute_streak(sessions)
    assert result["current_streak"] == 4
    assert result["longest_streak"] == 4
    assert len(result["active_days"]) == 4


def test_compute_streak_broken_streak():
    # Days 0, 1, then a gap, then 4, 5
    sessions = [
        _make_session(days_ago=0),
        _make_session(days_ago=1),
        _make_session(days_ago=4),
        _make_session(days_ago=5),
    ]
    result = compute_streak(sessions)
    assert result["current_streak"] == 2
    assert result["longest_streak"] == 2
    assert result["total_sessions"] == 4


def test_compute_streak_longest_not_current():
    # Longest streak was 3 days ago; current streak is 1
    sessions = [
        _make_session(days_ago=0),
        _make_session(days_ago=5),
        _make_session(days_ago=6),
        _make_session(days_ago=7),
    ]
    result = compute_streak(sessions)
    assert result["current_streak"] == 1
    assert result["longest_streak"] == 3


def test_compute_streak_no_recent_activity():
    # Last session was 3 days ago — streak should be 0
    sessions = [
        _make_session(days_ago=3),
        _make_session(days_ago=4),
    ]
    result = compute_streak(sessions)
    assert result["current_streak"] == 0
    assert result["longest_streak"] == 2


def test_session_date_format():
    s = _make_session(days_ago=0)
    date_str = _session_date(s)
    # Should be a valid ISO date
    datetime.strptime(date_str, "%Y-%m-%d")


def test_duplicate_sessions_same_day_counted_once():
    # Two sessions on the same day should count as one active day
    s1 = _make_session(days_ago=0)
    s2 = _make_session(days_ago=0)
    result = compute_streak([s1, s2])
    assert len(result["active_days"]) == 1
    assert result["total_sessions"] == 2
    assert result["current_streak"] == 1
