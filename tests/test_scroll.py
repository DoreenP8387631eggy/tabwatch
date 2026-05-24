"""Tests for the scroll depth analyser."""
import pytest
from backend.models.session import BrowsingSession, TabEvent
from backend.summarizer.scroll import compute_scroll
from datetime import datetime, timezone


def _ts(offset: int = 0) -> str:
    return datetime(2024, 6, 1, 12, 0, offset, tzinfo=timezone.utc).isoformat()


def _make_session(events=None) -> BrowsingSession:
    s = BrowsingSession(session_id="s1", started_at=_ts(0))
    for evt in (events or []):
        s.events.append(evt)
    return s


def _evt(url: str, scroll_depth=None) -> TabEvent:
    meta = {}
    if scroll_depth is not None:
        meta["scroll_depth"] = scroll_depth
    return TabEvent(url=url, title="T", timestamp=_ts(1), event_type="visit", meta=meta)


def test_compute_scroll_empty_session():
    s = _make_session()
    result = compute_scroll(s)
    assert result["total_events"] == 0
    assert result["events_with_scroll"] == 0
    assert result["average_scroll_depth"] == 0.0
    assert result["deep_reads"] == 0
    assert result["per_domain"] == {}


def test_compute_scroll_no_scroll_metadata():
    s = _make_session([
        _evt("https://example.com"),
        _evt("https://news.com"),
    ])
    result = compute_scroll(s)
    assert result["total_events"] == 2
    assert result["events_with_scroll"] == 0
    assert result["average_scroll_depth"] == 0.0


def test_compute_scroll_single_event():
    s = _make_session([_evt("https://example.com", scroll_depth=0.5)])
    result = compute_scroll(s)
    assert result["events_with_scroll"] == 1
    assert result["average_scroll_depth"] == 0.5
    assert result["max_scroll_depth"] == 0.5
    assert result["deep_reads"] == 0


def test_compute_scroll_deep_read_threshold():
    s = _make_session([
        _evt("https://blog.com", scroll_depth=0.9),
        _evt("https://blog.com", scroll_depth=0.75),
        _evt("https://blog.com", scroll_depth=0.3),
    ])
    result = compute_scroll(s)
    assert result["deep_reads"] == 2
    assert result["max_scroll_depth"] == 0.9


def test_compute_scroll_per_domain_average():
    s = _make_session([
        _evt("https://github.com/foo", scroll_depth=0.4),
        _evt("https://github.com/bar", scroll_depth=0.6),
        _evt("https://news.ycombinator.com", scroll_depth=1.0),
    ])
    result = compute_scroll(s)
    assert "github.com" in result["per_domain"]
    assert result["per_domain"]["github.com"] == pytest.approx(0.5, abs=1e-4)
    assert result["per_domain"]["news.ycombinator.com"] == pytest.approx(1.0, abs=1e-4)


def test_compute_scroll_clamps_values():
    """Values outside [0, 1] should be clamped."""
    s = _make_session([
        _evt("https://example.com", scroll_depth=1.5),
        _evt("https://example.com", scroll_depth=-0.2),
    ])
    result = compute_scroll(s)
    assert result["max_scroll_depth"] == 1.0
    assert result["average_scroll_depth"] == pytest.approx(0.5, abs=1e-4)
