"""Compute time-spent breakdown by category for a browsing session."""

from collections import defaultdict
from typing import Dict, List

from backend.models.session import BrowsingSession
from backend.summarizer.tags import classify_domain


def _extract_domain(url: str) -> str:
    """Return bare domain from a URL string."""
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc.lower().lstrip("www.")
    except Exception:
        return url


def compute_category_time(session: BrowsingSession) -> Dict[str, float]:
    """Return total seconds spent per category.

    Time for an event is approximated as the gap to the *next* event
    in the same session (last event gets 0 seconds).
    """
    events = session.events
    totals: Dict[str, float] = defaultdict(float)

    for i, event in enumerate(events):
        domain = _extract_domain(event.url)
        category = classify_domain(domain)
        if i + 1 < len(events):
            delta = (
                events[i + 1].timestamp - event.timestamp
            ).total_seconds()
            # Cap unreasonably long gaps at 30 minutes
            delta = max(0.0, min(delta, 1800.0))
        else:
            delta = 0.0
        totals[category] += delta

    return dict(totals)


def top_categories(session: BrowsingSession, n: int = 5) -> List[Dict]:
    """Return top-n categories sorted by time spent (descending)."""
    totals = compute_category_time(session)
    ranked = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    return [
        {"category": cat, "seconds": round(secs, 2)}
        for cat, secs in ranked[:n]
    ]
