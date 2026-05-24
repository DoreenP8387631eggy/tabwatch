"""Unit tests for backend/summarizer/attention.py."""

import pytest
from backend.models.session import BrowsingSession, TabEvent
from backend.summarizer.attention import compute_attention


def _make_session() -> BrowsingSession:
    s = BrowsingSession(session_id="s1")
    return s


def _evt(url: str, ts: str) -> TabEvent:
    return TabEvent(url=url, title=url, timestamp=ts)


def test_compute_attention_empty_session():
    s = _make_session()
    result = compute_attention(s)
    assert result["total_visits"] == 0
    assert result["attention_score"] == 0
    assert result["longest_visit"] is None


def test_compute_attention_single_event():
    s = _make_session()
    s.events = [_evt("https://github.com", "2024-01-01T10:00:00")]
    result = compute_attention(s)
    assert result["total_visits"] == 1
    # Last event has no successor → 0 s duration
    assert result["avg_visit_seconds"] == 0.0


def test_compute_attention_all_shallow():
    s = _make_session()
    s.events = [
        _evt("https://twitter.com", "2024-01-01T10:00:00"),
        _evt("https://reddit.com",  "2024-01-01T10:00:05"),
        _evt("https://news.com",    "2024-01-01T10:00:09"),
    ]
    result = compute_attention(s)
    assert result["shallow_visits"] == 2   # first two have <15 s duration
    assert result["deep_visits"] == 0
    assert result["attention_score"] < 30


def test_compute_attention_deep_visits():
    s = _make_session()
    s.events = [
        _evt("https://docs.python.org", "2024-01-01T10:00:00"),
        _evt("https://docs.python.org", "2024-01-01T10:05:00"),  # 300 s gap
        _evt("https://github.com",      "2024-01-01T10:12:00"),  # 420 s gap
        _evt("https://end.com",         "2024-01-01T10:12:10"),
    ]
    result = compute_attention(s)
    assert result["deep_visits"] == 2
    assert result["attention_score"] > 50


def test_compute_attention_longest_visit():
    s = _make_session()
    s.events = [
        _evt("https://github.com",      "2024-01-01T09:00:00"),
        _evt("https://stackoverflow.com","2024-01-01T09:00:30"),  # 30 s
        _evt("https://docs.python.org", "2024-01-01T09:10:00"),  # 570 s ← longest
        _evt("https://end.com",         "2024-01-01T09:10:05"),
    ]
    result = compute_attention(s)
    assert result["longest_visit"] is not None
    assert result["longest_visit"]["domain"] == "docs.python.org"
    assert result["longest_visit"]["seconds"] == pytest.approx(570.0)


def test_compute_attention_avg():
    s = _make_session()
    s.events = [
        _evt("https://a.com", "2024-01-01T10:00:00"),
        _evt("https://b.com", "2024-01-01T10:01:00"),  # 60 s
        _evt("https://c.com", "2024-01-01T10:02:00"),  # 60 s
        _evt("https://d.com", "2024-01-01T10:02:00"),  # 0 s (last)
    ]
    result = compute_attention(s)
    assert result["avg_visit_seconds"] == pytest.approx(40.0)  # (60+60+0)/3
