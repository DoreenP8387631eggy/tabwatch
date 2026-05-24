"""Tests for the transitions summarizer module."""

import pytest
from datetime import datetime, timezone
from backend.models.session import BrowsingSession, TabEvent
from backend.summarizer.transitions import compute_transitions, _extract_domain


def _make_session(events=None):
    s = BrowsingSession(session_id="s1")
    for e in (events or []):
        s.events.append(e)
    return s


def _evt(url: str) -> TabEvent:
    return TabEvent(
        url=url,
        title=url,
        timestamp=datetime.now(timezone.utc).isoformat(),
        event_type="visit",
    )


# --- unit tests for _extract_domain ---

def test_extract_domain_strips_www():
    assert _extract_domain("https://www.github.com/user") == "github.com"


def test_extract_domain_plain():
    assert _extract_domain("https://news.ycombinator.com") == "news.ycombinator.com"


def test_extract_domain_fallback():
    assert _extract_domain("not-a-url") == "not-a-url"


# --- compute_transitions tests ---

def test_compute_transitions_empty_session():
    s = _make_session()
    result = compute_transitions(s)
    assert result["transition_count"] == 0
    assert result["transition_map"] == {}
    assert result["top_transitions"] == []
    assert result["self_transitions"] == 0


def test_compute_transitions_single_event():
    s = _make_session([_evt("https://github.com")])
    result = compute_transitions(s)
    assert result["transition_count"] == 0
    assert result["self_transitions"] == 0


def test_compute_transitions_no_domain_switches():
    s = _make_session([
        _evt("https://github.com/a"),
        _evt("https://github.com/b"),
        _evt("https://github.com/c"),
    ])
    result = compute_transitions(s)
    assert result["transition_count"] == 0
    assert result["self_transitions"] == 2
    assert result["top_transitions"] == []


def test_compute_transitions_single_switch():
    s = _make_session([
        _evt("https://github.com"),
        _evt("https://stackoverflow.com"),
    ])
    result = compute_transitions(s)
    assert result["transition_count"] == 1
    assert result["self_transitions"] == 0
    assert len(result["top_transitions"]) == 1
    t = result["top_transitions"][0]
    assert t["from"] == "github.com"
    assert t["to"] == "stackoverflow.com"
    assert t["count"] == 1


def test_compute_transitions_multiple_switches_sorted():
    s = _make_session([
        _evt("https://github.com"),
        _evt("https://twitter.com"),
        _evt("https://github.com"),
        _evt("https://twitter.com"),
        _evt("https://github.com"),
        _evt("https://reddit.com"),
    ])
    result = compute_transitions(s)
    assert result["transition_count"] == 5
    top = result["top_transitions"]
    # Highest count first
    assert top[0]["count"] >= top[-1]["count"]
    # github->twitter should appear twice
    gh_tw = next((t for t in top if t["from"] == "github.com" and t["to"] == "twitter.com"), None)
    assert gh_tw is not None
    assert gh_tw["count"] == 2


def test_compute_transitions_map_structure():
    s = _make_session([
        _evt("https://github.com"),
        _evt("https://stackoverflow.com"),
    ])
    result = compute_transitions(s)
    assert "github.com" in result["transition_map"]
    assert result["transition_map"]["github.com"]["stackoverflow.com"] == 1
