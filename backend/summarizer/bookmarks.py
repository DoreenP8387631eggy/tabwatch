"""Bookmark detection: identify frequently revisited domains within a session."""

from collections import defaultdict
from typing import Any

from backend.models.session import BrowsingSession

_REVISIT_THRESHOLD = 3  # visits to be considered a "bookmark-worthy" domain


def _extract_domain(url: str) -> str:
    try:
        from urllib.parse import urlparse
        host = urlparse(url).netloc
        return host.removeprefix("www.")
    except Exception:
        return url


def detect_bookmarks(session: BrowsingSession, threshold: int = _REVISIT_THRESHOLD) -> dict[str, Any]:
    """Return domains the user revisited heavily, suggesting bookmark-worthy sites."""
    visit_counts: dict[str, int] = defaultdict(int)
    first_seen: dict[str, float] = {}
    last_seen: dict[str, float] = {}

    for event in session.events:
        if event.event_type != "visit":
            continue
        domain = _extract_domain(event.url)
        visit_counts[domain] += 1
        ts = event.timestamp
        if domain not in first_seen:
            first_seen[domain] = ts
        last_seen[domain] = ts

    candidates = [
        {
            "domain": domain,
            "visits": count,
            "first_seen": first_seen[domain],
            "last_seen": last_seen[domain],
        }
        for domain, count in visit_counts.items()
        if count >= threshold
    ]
    candidates.sort(key=lambda x: x["visits"], reverse=True)

    return {
        "session_id": session.session_id,
        "threshold": threshold,
        "bookmark_candidates": candidates,
        "total_candidates": len(candidates),
    }
