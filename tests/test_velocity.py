import pytest
from datetime import datetime, timedelta
from backend.models.session import BrowsingSession, TabEvent
from backend.summarizer.velocity import compute_velocity


def _make_session(events=None):
    s = BrowsingSession(session_id="test-vel")
    if events:
        s.events = events
    return s


def _evt(url: str, offset_seconds: int) -> TabEvent:
    ts = (datetime(2024, 1, 15, 10, 0, 0) + timedelta(seconds=offset_seconds)).isoformat()
    return TabEvent(url=url, title="Title", timestamp=ts, event_type="visit")


def test_compute_velocity_empty_session():
    s = _make_session()
    result = compute_velocity(s)
    assert result["total_switches"] == 0
    assert result["switches_per_minute"] == 0.0
    assert result["unique_domains_visited"] == 0
    assert result["avg_time_per_domain_seconds"] == 0.0
    assert result["domain_switch_sequence"] == []


def test_compute_velocity_single_event():
    s = _make_session([_evt("https://github.com/repo", 0)])
    result = compute_velocity(s)
    assert result["total_switches"] == 0
    assert result["unique_domains_visited"] == 1
    assert result["domain_switch_sequence"] == ["github.com"]


def test_compute_velocity_no_domain_switches():
    events = [
        _evt("https://github.com/a", 0),
        _evt("https://github.com/b", 30),
        _evt("https://github.com/c", 60),
    ]
    s = _make_session(events)
    result = compute_velocity(s)
    assert result["total_switches"] == 0
    assert result["unique_domains_visited"] == 1
    assert result["switches_per_minute"] == 0.0


def test_compute_velocity_multiple_switches():
    events = [
        _evt("https://github.com/repo", 0),
        _evt("https://twitter.com/feed", 60),
        _evt("https://github.com/issues", 120),
        _evt("https://reddit.com/r/python", 180),
        _evt("https://github.com/pulls", 240),
    ]
    s = _make_session(events)
    result = compute_velocity(s)
    assert result["total_switches"] == 4
    assert result["unique_domains_visited"] == 3
    # 4 switches over 4 minutes = 1.0 per minute
    assert result["switches_per_minute"] == 1.0
    assert result["domain_switch_sequence"] == [
        "github.com", "twitter.com", "github.com", "reddit.com", "github.com"
    ]


def test_compute_velocity_avg_time_per_domain():
    events = [
        _evt("https://github.com/repo", 0),
        _evt("https://news.ycombinator.com", 120),  # 120s on github
        _evt("https://github.com/issues", 180),    # 60s on hn
    ]
    s = _make_session(events)
    result = compute_velocity(s)
    # github: 120s, hn: 60s => total 180s / 2 domains = 90s avg
    assert result["avg_time_per_domain_seconds"] == 90.0


def test_compute_velocity_www_stripped():
    events = [
        _evt("https://www.github.com/repo", 0),
        _evt("https://github.com/issues", 60),
    ]
    s = _make_session(events)
    result = compute_velocity(s)
    # Both resolve to github.com — no switch
    assert result["total_switches"] == 0
    assert result["unique_domains_visited"] == 1
