"""Tests for browsing velocity computation."""

from datetime import datetime, timedelta

from backend.models.session import BrowsingSession, TabEvent
from backend.summarizer.velocity import compute_velocity


def _make_session(closed: bool = True) -> BrowsingSession:
    s = BrowsingSession(session_id="test-vel")
    return s


def _evt(session: BrowsingSession, url: str, offset_seconds: int) -> None:
    base = datetime(2024, 6, 1, 9, 0, 0)
    ts = (base + timedelta(seconds=offset_seconds)).isoformat()
    session.events.append(TabEvent(url=url, title=url, timestamp=ts))


def test_compute_velocity_empty_session():
    s = _make_session()
    result = compute_velocity(s)
    assert result["event_count"] == 0
    assert result["duration_minutes"] == 0.0
    assert result["events_per_minute"] == 0.0
    assert result["domain_switches"] == 0
    assert result["domain_switches_per_minute"] == 0.0
    assert result["peak_burst"] == 0


def test_compute_velocity_single_event():
    s = _make_session()
    _evt(s, "https://github.com", 0)
    result = compute_velocity(s)
    assert result["event_count"] == 1
    assert result["domain_switches"] == 0
    assert result["peak_burst"] == 1


def test_compute_velocity_no_domain_switches():
    s = _make_session()
    for i in range(5):
        _evt(s, "https://github.com/page" + str(i), i * 30)
    result = compute_velocity(s)
    assert result["event_count"] == 5
    assert result["domain_switches"] == 0


def test_compute_velocity_all_different_domains():
    s = _make_session()
    urls = [
        "https://github.com",
        "https://stackoverflow.com",
        "https://reddit.com",
        "https://news.ycombinator.com",
    ]
    for i, url in enumerate(urls):
        _evt(s, url, i * 60)
    result = compute_velocity(s)
    assert result["domain_switches"] == 3
    assert result["event_count"] == 4


def test_compute_velocity_peak_burst():
    """5 events within 60 s should yield peak_burst=5."""
    s = _make_session()
    for i in range(5):
        _evt(s, "https://github.com", i * 10)   # 0,10,20,30,40 s
    _evt(s, "https://github.com", 300)            # far away
    result = compute_velocity(s)
    assert result["peak_burst"] == 5


def test_compute_velocity_rates_are_positive():
    s = _make_session()
    _evt(s, "https://github.com", 0)
    _evt(s, "https://reddit.com", 60)
    _evt(s, "https://github.com", 120)
    result = compute_velocity(s)
    assert result["events_per_minute"] > 0
    assert result["domain_switches_per_minute"] > 0
    assert result["duration_minutes"] > 0
