"""Tests for domain frequency analysis."""
import pytest
from datetime import datetime, timedelta

from backend.models.session import BrowsingSession, TabEvent
from backend.summarizer.domains import compute_domain_frequency, top_domains


def _make_session(events_data):
    """Helper: create a BrowsingSession with preset events."""
    session = BrowsingSession(session_id="test-session")
    base = datetime(2024, 6, 1, 9, 0, 0)
    for i, (url, title) in enumerate(events_data):
        event = TabEvent(
            url=url,
            title=title,
            timestamp=base + timedelta(minutes=i * 2),
        )
        session.events.append(event)
    return session


def test_compute_domain_frequency_empty_session():
    session = BrowsingSession(session_id="empty")
    result = compute_domain_frequency(session)
    assert result == []


def test_compute_domain_frequency_single_event():
    session = _make_session([("https://github.com/explore", "GitHub")])
    result = compute_domain_frequency(session)
    assert len(result) == 1
    assert result[0]["domain"] == "github.com"
    assert result[0]["visits"] == 1
    assert result[0]["total_seconds"] == 0.0  # last event, no successor


def test_compute_domain_frequency_multiple_domains():
    events = [
        ("https://github.com/explore", "GitHub"),
        ("https://stackoverflow.com/questions", "SO"),
        ("https://github.com/pulls", "GitHub PRs"),
        ("https://news.ycombinator.com", "HN"),
    ]
    session = _make_session(events)
    result = compute_domain_frequency(session)
    domains = [r["domain"] for r in result]
    # github.com visited twice, should be first
    assert domains[0] == "github.com"
    gh = result[0]
    assert gh["visits"] == 2


def test_compute_domain_frequency_strips_www():
    session = _make_session([
        ("https://www.google.com/search?q=python", "Google"),
        ("https://google.com/", "Google Home"),
    ])
    result = compute_domain_frequency(session)
    assert len(result) == 1
    assert result[0]["domain"] == "google.com"
    assert result[0]["visits"] == 2


def test_compute_domain_frequency_time_capped_at_300():
    """Time between events > 5 min should be capped at 300 seconds."""
    session = BrowsingSession(session_id="cap-test")
    base = datetime(2024, 6, 1, 9, 0, 0)
    session.events.append(TabEvent(url="https://example.com", title="A", timestamp=base))
    session.events.append(TabEvent(url="https://other.com", title="B", timestamp=base + timedelta(minutes=30)))
    result = compute_domain_frequency(session)
    example = next(r for r in result if r["domain"] == "example.com")
    assert example["total_seconds"] == 300.0


def test_top_domains_limits_results():
    events = [
        ("https://a.com", "A"),
        ("https://b.com", "B"),
        ("https://c.com", "C"),
        ("https://d.com", "D"),
        ("https://e.com", "E"),
        ("https://f.com", "F"),
    ]
    session = _make_session(events)
    result = top_domains(session, n=3)
    assert len(result) == 3


def test_top_domains_default_n_is_five():
    events = [(f"https://site{i}.com", f"Site {i}") for i in range(8)]
    session = _make_session(events)
    result = top_domains(session)
    assert len(result) == 5
