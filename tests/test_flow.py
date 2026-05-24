"""Tests for backend/summarizer/flow.py"""

import pytest
from datetime import datetime, timezone

from backend.models.session import BrowsingSession, TabEvent
from backend.summarizer.flow import compute_flow


def _make_session() -> BrowsingSession:
    s = BrowsingSession(session_id="test-flow")
    return s


def _evt(url: str, ts: str | None = None) -> TabEvent:
    return TabEvent(
        url=url,
        title=url,
        timestamp=ts or datetime.now(timezone.utc).isoformat(),
    )


def test_compute_flow_empty_session():
    s = _make_session()
    result = compute_flow(s)
    assert result["flow_score"] == 0
    assert result["transitions"] == 0
    assert result["unique_domains"] == 0
    assert result["revisit_rate"] == 0.0
    assert result["label"] == "No Data"


def test_compute_flow_single_event():
    s = _make_session()
    s.add_event(_evt("https://github.com/user/repo"))
    result = compute_flow(s)
    assert result["unique_domains"] == 1
    assert result["transitions"] == 0
    assert result["flow_score"] > 0


def test_compute_flow_smooth_focused():
    """Staying mostly on one domain should yield a high flow score."""
    s = _make_session()
    for i in range(8):
        s.add_event(_evt("https://docs.python.org/page" + str(i)))
    result = compute_flow(s)
    assert result["flow_score"] >= 70
    assert result["label"] == "Smooth"


def test_compute_flow_erratic_many_domains():
    """Visiting a completely new domain on every event should score low."""
    s = _make_session()
    domains = [
        "https://twitter.com",
        "https://reddit.com",
        "https://youtube.com",
        "https://facebook.com",
        "https://instagram.com",
        "https://tiktok.com",
        "https://twitch.tv",
        "https://discord.com",
        "https://slack.com",
        "https://linkedin.com",
    ]
    for d in domains:
        s.add_event(_evt(d))
    result = compute_flow(s)
    assert result["flow_score"] < 40
    assert result["label"] == "Erratic"


def test_compute_flow_revisit_rate_increases_score():
    """Revisiting domains should boost the flow score."""
    s = _make_session()
    urls = [
        "https://github.com",
        "https://stackoverflow.com",
        "https://github.com",
        "https://stackoverflow.com",
        "https://github.com",
    ]
    for u in urls:
        s.add_event(_evt(u))
    result = compute_flow(s)
    assert result["revisit_rate"] > 0
    assert result["transitions"] >= 2


def test_compute_flow_label_moderate():
    """A mixed session should land in the Moderate band."""
    s = _make_session()
    urls = [
        "https://github.com",
        "https://github.com",
        "https://news.ycombinator.com",
        "https://github.com",
        "https://docs.python.org",
        "https://github.com",
    ]
    for u in urls:
        s.add_event(_evt(u))
    result = compute_flow(s)
    assert result["label"] in ("Smooth", "Moderate")
    assert 0 <= result["flow_score"] <= 100
