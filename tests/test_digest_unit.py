"""Unit tests for backend/summarizer/digest.py."""

from datetime import datetime, timedelta
from unittest.mock import patch

from backend.models.session import BrowsingSession, TabEvent
from backend.summarizer.digest import build_daily_digest, _session_date


TODAY = "2024-06-15"


def _make_session(start_offset_h: int = 0, duration_h: int = 1, closed: bool = True) -> BrowsingSession:
    start = datetime(2024, 6, 15, 9 + start_offset_h, 0, 0)
    s = BrowsingSession(session_id="s1", start_time=start.isoformat())
    s.add_event(TabEvent(url="https://github.com/user/repo", title="GitHub", timestamp=start.isoformat()))
    s.add_event(TabEvent(url="https://news.ycombinator.com", title="HN", timestamp=(start + timedelta(minutes=20)).isoformat()))
    if closed:
        end = start + timedelta(hours=duration_h)
        s.close(end.isoformat())
    return s


def test_session_date():
    s = _make_session()
    assert _session_date(s) == TODAY


def test_digest_empty_sessions():
    result = build_daily_digest([], target_date=TODAY)
    assert result["session_count"] == 0
    assert result["total_duration_seconds"] == 0
    assert result["top_domains"] == []
    assert result["tag_totals"] == {}
    assert len(result["highlights"]) >= 1


def test_digest_open_session_excluded():
    open_s = _make_session(closed=False)
    result = build_daily_digest([open_s], target_date=TODAY)
    assert result["session_count"] == 0


def test_digest_single_session():
    s = _make_session(duration_h=2)
    result = build_daily_digest([s], target_date=TODAY)
    assert result["session_count"] == 1
    assert result["total_duration_seconds"] == 7200
    assert isinstance(result["top_domains"], list)
    assert len(result["top_domains"]) > 0


def test_digest_multiple_sessions_aggregate():
    s1 = _make_session(start_offset_h=0, duration_h=1)
    s2 = _make_session(start_offset_h=2, duration_h=1)
    result = build_daily_digest([s1, s2], target_date=TODAY)
    assert result["session_count"] == 2
    assert result["total_duration_seconds"] == 7200


def test_digest_wrong_date_excluded():
    s = _make_session()
    result = build_daily_digest([s], target_date="2024-01-01")
    assert result["session_count"] == 0


def test_digest_tag_totals_present():
    s = _make_session(duration_h=1)
    result = build_daily_digest([s], target_date=TODAY)
    assert isinstance(result["tag_totals"], dict)


def test_digest_highlights_list():
    s = _make_session(duration_h=1)
    result = build_daily_digest([s], target_date=TODAY)
    assert isinstance(result["highlights"], list)
    assert len(result["highlights"]) >= 1
