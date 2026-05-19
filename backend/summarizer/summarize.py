"""Summarizes a browsing session into productivity insights."""

from collections import Counter, defaultdict
from datetime import timedelta
from typing import Any

from backend.models.session import BrowsingSession


PRODUCTIVE_DOMAINS = {
    "github.com", "stackoverflow.com", "docs.python.org",
    "developer.mozilla.org", "leetcode.com", "notion.so",
}

DISTRACTING_DOMAINS = {
    "twitter.com", "x.com", "reddit.com", "youtube.com",
    "facebook.com", "instagram.com", "tiktok.com",
}


def _extract_domain(url: str) -> str:
    """Naively extract domain from a URL string."""
    url = url.removeprefix("https://").removeprefix("http://")
    return url.split("/")[0].removeprefix("www.")


def summarize_session(session: BrowsingSession) -> dict[str, Any]:
    """Return a summary dict for the given browsing session."""
    if not session.events:
        return {
            "session_id": session.session_id,
            "total_events": 0,
            "unique_domains": [],
            "top_domains": [],
            "productive_time_pct": 0.0,
            "distracting_time_pct": 0.0,
            "duration_seconds": 0,
            "verdict": "no data",
        }

    domain_counts: Counter = Counter()
    category_counts: Counter = Counter()

    for event in session.events:
        domain = _extract_domain(event.url)
        domain_counts[domain] += 1
        if domain in PRODUCTIVE_DOMAINS:
            category_counts["productive"] += 1
        elif domain in DISTRACTING_DOMAINS:
            category_counts["distracting"] += 1
        else:
            category_counts["neutral"] += 1

    total = len(session.events)
    productive_pct = round(category_counts["productive"] / total * 100, 1)
    distracting_pct = round(category_counts["distracting"] / total * 100, 1)

    duration = 0
    if session.ended_at and session.started_at:
        duration = int((session.ended_at - session.started_at).total_seconds())

    if productive_pct >= 60:
        verdict = "focused"
    elif distracting_pct >= 50:
        verdict = "distracted"
    else:
        verdict = "mixed"

    return {
        "session_id": session.session_id,
        "total_events": total,
        "unique_domains": list(domain_counts.keys()),
        "top_domains": domain_counts.most_common(5),
        "productive_time_pct": productive_pct,
        "distracting_time_pct": distracting_pct,
        "duration_seconds": duration,
        "verdict": verdict,
    }
