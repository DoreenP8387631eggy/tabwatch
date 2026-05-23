import pytest
from datetime import datetime, timedelta, date
from unittest.mock import MagicMock
from backend.summarizer.streak import compute_streak, _session_date
from backend.models.session import BrowsingSession, TabEvent


def _make_session(days_ago: int, closed: bool = True) -> BrowsingSession:
    start = datetime.utcnow() - timedelta(days=days_ago)
    s = BrowsingSession(session_id=f"s-{days_ago}-{closed}")
    s.start_time = start
    if closed:
        s.end_time = start + timedelta(hours=1)
    return s


def test_compute_streak_empty():
    result = compute_streak([])
    assert result["current_streak"] == 0
    assert result["longest_streak"] == 0
    assert result["streak_start"] is None
    assert result["today_covered"] is False


def test_compute_streak_single_session_today():
    sessions = [_make_session(0)]
    result = compute_streak(sessions)
    assert result["current_streak"] == 1
    assert result["longest_streak"] == 1
    assert result["today_covered"] is True
    assert result["streak_start"] == date.today().isoformat()


def test_compute_streak_consecutive_days():
    sessions = [_make_session(i) for i in range(4)]
    result = compute_streak(sessions)
    assert result["current_streak"] == 4
    assert result["longest_streak"] == 4
    assert result["today_covered"] is True


def test_compute_streak_broken_streak():
    # days 0,1 then gap, then 4,5
    sessions = [_make_session(0), _make_session(1), _make_session(4), _make_session(5)]
    result = compute_streak(sessions)
    assert result["current_streak"] == 2
    assert result["longest_streak"] == 2


def test_compute_streak_excludes_open_sessions():
    open_session = _make_session(0, closed=False)
    closed_session = _make_session(1, closed=True)
    result = compute_streak([open_session, closed_session])
    # Only the closed session counts; it was yesterday
    assert result["current_streak"] == 1
    assert result["today_covered"] is False


def test_compute_streak_longest_not_current():
    # Long streak 10-6 days ago, short streak today
    long_run = [_make_session(i) for i in range(6, 11)]
    short_run = [_make_session(0)]
    result = compute_streak(long_run + short_run)
    assert result["longest_streak"] == 5
    assert result["current_streak"] == 1


def test_session_date_extraction():
    s = _make_session(3)
    d = _session_date(s)
    assert d == (date.today() - timedelta(days=3))
