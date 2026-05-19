"""Timeline builder: groups tab events into time-bucketed activity blocks."""

from datetime import datetime, timedelta
from typing import List, Dict, Any

from backend.models.session import BrowsingSession
from backend.summarizer.summarize import _extract_domain

BUCKET_MINUTES = 5


def _bucket_key(ts: float, bucket_minutes: int = BUCKET_MINUTES) -> str:
    """Round a UNIX timestamp down to the nearest bucket boundary."""
    dt = datetime.utcfromtimestamp(ts)
    total_minutes = dt.hour * 60 + dt.minute
    floored = (total_minutes // bucket_minutes) * bucket_minutes
    bucketed = dt.replace(hour=floored // 60, minute=floored % 60, second=0, microsecond=0)
    return bucketed.strftime("%H:%M")


def build_timeline(session: BrowsingSession, bucket_minutes: int = BUCKET_MINUTES) -> List[Dict[str, Any]]:
    """Return a list of time buckets with aggregated domain activity.

    Each bucket:
        {
            "time": "HH:MM",
            "domains": {"example.com": visit_count, ...},
            "event_count": int
        }
    """
    buckets: Dict[str, Dict[str, Any]] = {}

    for event in session.events:
        key = _bucket_key(event.timestamp, bucket_minutes)
        if key not in buckets:
            buckets[key] = {"time": key, "domains": {}, "event_count": 0}

        domain = _extract_domain(event.url)
        buckets[key]["domains"][domain] = buckets[key]["domains"].get(domain, 0) + 1
        buckets[key]["event_count"] += 1

    return sorted(buckets.values(), key=lambda b: b["time"])
