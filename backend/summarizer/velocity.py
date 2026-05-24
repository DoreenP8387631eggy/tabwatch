"""Compute browsing velocity metrics for a session.

Velocity measures how rapidly a user switches between tabs/domains
over time, expressed as events-per-minute and domain-switches-per-minute.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.models.session import BrowsingSession


def _parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def compute_velocity(session: BrowsingSession) -> dict[str, Any]:
    """Return velocity metrics for a closed or open session."""
    events = session.events
    if not events:
        return {
            "event_count": 0,
            "duration_minutes": 0.0,
            "events_per_minute": 0.0,
            "domain_switches": 0,
            "domain_switches_per_minute": 0.0,
            "peak_burst": 0,
        }

    start = _parse_ts(events[0].timestamp)
    end_ts = session.closed_at or events[-1].timestamp
    end = _parse_ts(end_ts)

    duration_seconds = max((end - start).total_seconds(), 1)
    duration_minutes = duration_seconds / 60.0

    # Count domain switches (consecutive domain changes)
    def _domain(url: str) -> str:
        try:
            from urllib.parse import urlparse
            host = urlparse(url).hostname or url
            return host.removeprefix("www.")
        except Exception:
            return url

    domains = [_domain(e.url) for e in events]
    switches = sum(1 for i in range(1, len(domains)) if domains[i] != domains[i - 1])

    events_per_minute = len(events) / duration_minutes
    switches_per_minute = switches / duration_minutes

    # Peak burst: max events in any 60-second sliding window
    timestamps = [_parse_ts(e.timestamp) for e in events]
    peak_burst = 0
    for i, t in enumerate(timestamps):
        burst = sum(1 for t2 in timestamps[i:] if (t2 - t).total_seconds() <= 60)
        if burst > peak_burst:
            peak_burst = burst

    return {
        "event_count": len(events),
        "duration_minutes": round(duration_minutes, 2),
        "events_per_minute": round(events_per_minute, 2),
        "domain_switches": switches,
        "domain_switches_per_minute": round(switches_per_minute, 2),
        "peak_burst": peak_burst,
    }
