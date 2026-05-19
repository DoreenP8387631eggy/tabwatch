"""Unit tests for backend/summarizer/goals.py."""

import pytest
from datetime import datetime, timezone
from backend.models.session import BrowsingSession, TabEvent
from backend.summarizer.goals import evaluate_goals, DEFAULT_GOALS


def _make_session(events: list[tuple[str, int]]) -> BrowsingSession:
    """Create a closed session with (url, duration_seconds) pairs."""
    s = BrowsingSession(session_id="unit-test")
    t = 0
    for url, dur in events:
        s.add_event(TabEvent(url=url, timestamp=t, duration=dur))
        t += dur
    s.close()
    return s


def test_evaluate_goals_all_met():
    events = [
        ("https://github.com/repo", 4000),
        ("https://docs.python.org", 200),
    ]
    session = _make_session(events)
    result = evaluate_goals(session)
    assert result["all_met"] is True
    assert result["goals_met"] == result["goals_total"]


def test_evaluate_goals_social_exceeded():
    events = [("https://twitter.com/feed", 3000)]
    session = _make_session(events)
    result = evaluate_goals(session)
    social_result = next(r for r in result["results"] if r["goal"] == "max_social_minutes")
    assert social_result["met"] is False
    assert social_result["actual"] == pytest.approx(50.0, rel=1e-2)


def test_evaluate_goals_custom_target():
    events = [("https://twitter.com/feed", 3000)]
    session = _make_session(events)
    custom_goals = {**DEFAULT_GOALS, "max_social_minutes": 60}
    result = evaluate_goals(session, custom_goals)
    social_result = next(r for r in result["results"] if r["goal"] == "max_social_minutes")
    assert social_result["met"] is True


def test_evaluate_goals_empty_session():
    session = _make_session([])
    result = evaluate_goals(session)
    assert isinstance(result["results"], list)
    assert result["goals_total"] > 0
    for r in result["results"]:
        if r["goal"].startswith("max_"):
            assert r["met"] is True


def test_evaluate_goals_structure():
    session = _make_session([("https://github.com", 100)])
    result = evaluate_goals(session)
    assert "goals_met" in result
    assert "goals_total" in result
    assert "all_met" in result
    assert "results" in result
    for item in result["results"]:
        assert {"goal", "target", "actual", "met"} <= item.keys()
