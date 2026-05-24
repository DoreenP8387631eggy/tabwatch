"""Unit tests for backend/summarizer/mood.py."""

import pytest
from backend.models.session import BrowsingSession, TabEvent
from backend.summarizer.mood import infer_mood


def _make_session(events=None) -> BrowsingSession:
    s = BrowsingSession(session_id="test")
    for url, ts in (events or []):
        s.add_event(TabEvent(url=url, title="", timestamp=ts, event_type="visit"))
    return s


def _evt(url, ts="2024-01-01T10:00:00"):
    return (url, ts)


def test_infer_mood_empty_session():
    s = _make_session()
    result = infer_mood(s)
    assert result["dominant"] == "neutral"
    assert result["breakdown"] == {}


def test_infer_mood_focused_dev():
    events = [_evt("https://github.com/user/repo")] * 5 + \
             [_evt("https://stackoverflow.com/q/123")] * 3
    s = _make_session(events)
    result = infer_mood(s)
    assert result["dominant"] == "focused"


def test_infer_mood_distracted_social():
    events = [_evt("https://twitter.com/feed")] * 6 + \
             [_evt("https://instagram.com/explore")] * 4
    s = _make_session(events)
    result = infer_mood(s)
    assert result["dominant"] in ("distracted", "relaxed")


def test_infer_mood_scores_sum_to_one():
    events = [
        _evt("https://github.com"),
        _evt("https://twitter.com"),
        _evt("https://bbc.co.uk"),
    ]
    s = _make_session(events)
    result = infer_mood(s)
    total = sum(result["scores"].values())
    assert abs(total - 1.0) < 1e-6


def test_infer_mood_breakdown_counts():
    events = [
        _evt("https://github.com"),
        _evt("https://github.com"),
        _evt("https://twitter.com"),
    ]
    s = _make_session(events)
    result = infer_mood(s)
    total_visits = sum(result["breakdown"].values())
    assert total_visits == 3


def test_infer_mood_curious_education():
    events = [_evt("https://coursera.org/learn")] * 4 + \
             [_evt("https://khanacademy.org/math")] * 4
    s = _make_session(events)
    result = infer_mood(s)
    assert result["dominant"] in ("curious", "focused")
