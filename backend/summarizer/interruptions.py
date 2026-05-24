"""Detect and quantify browsing interruptions within a session.

An interruption is defined as a rapid context switch back to a previously
visited domain within a short window (< 2 minutes), suggesting the user
was pulled away and returned — a classic focus-break pattern.
"""

from urllib.parse import urlparse
from typing import Dict, Any, List
from backend.models.session import BrowsingSession

_INTERRUPTION_GAP_SECONDS = 120  # switches within 2 min count as interruptions
_RETURN_WINDOW_SECONDS = 300     # must return to prior domain within 5 min


def _extract_domain(url: str) -> str:
    try:
        host = urlparse(url).hostname or ""
        return host.removeprefix("www.")
    except Exception:
        return ""


def _parse_ts(ts: str) -> float:
    from datetime import datetime, timezone
    try:
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return 0.0


def compute_interruptions(session: BrowsingSession) -> Dict[str, Any]:
    """Analyse session events and return interruption metrics."""
    events = session.events
    if len(events) < 3:
        return {
            "interruption_count": 0,
            "interrupted_domains": [],
            "interruption_rate_per_hour": 0.0,
            "most_interrupted_domain": None,
        }

    interruption_count = 0
    domain_hits: Dict[str, int] = {}
    interrupted: List[str] = []

    for i in range(1, len(events) - 1):
        prev = events[i - 1]
        curr = events[i]
        nxt = events[i + 1]

        t_prev = _parse_ts(prev.timestamp)
        t_curr = _parse_ts(curr.timestamp)
        t_nxt = _parse_ts(nxt.timestamp)

        d_prev = _extract_domain(prev.url)
        d_curr = _extract_domain(curr.url)
        d_nxt = _extract_domain(nxt.url)

        gap_in = t_curr - t_prev
        gap_out = t_nxt - t_curr

        # Interruption: quick diversion then quick return to original domain
        if (
            d_curr != d_prev
            and d_nxt == d_prev
            and gap_in < _INTERRUPTION_GAP_SECONDS
            and gap_out < _RETURN_WINDOW_SECONDS
        ):
            interruption_count += 1
            domain_hits[d_prev] = domain_hits.get(d_prev, 0) + 1
            if d_prev not in interrupted:
                interrupted.append(d_prev)

    # Rate per hour
    t_start = _parse_ts(events[0].timestamp)
    t_end = _parse_ts(events[-1].timestamp)
    duration_hours = (t_end - t_start) / 3600.0 if t_end > t_start else 0.0
    rate = round(interruption_count / duration_hours, 2) if duration_hours > 0 else 0.0

    most_interrupted = max(domain_hits, key=lambda d: domain_hits[d]) if domain_hits else None

    return {
        "interruption_count": interruption_count,
        "interrupted_domains": interrupted,
        "interruption_rate_per_hour": rate,
        "most_interrupted_domain": most_interrupted,
    }
