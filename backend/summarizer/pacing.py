"""Pacing analysis: measures how evenly distributed browsing activity is across a session."""

from typing import Dict, Any, List
from collections import defaultdict
from backend.models.session import BrowsingSession


def _parse_ts(ts: str) -> float:
    """Parse ISO timestamp to Unix float."""
    from datetime import datetime, timezone
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return dt.timestamp()


def _bucket_minute(ts: str, start: float) -> int:
    """Return the minute bucket index relative to session start."""
    return int((_parse_ts(ts) - start) // 60)


def compute_pacing(session: BrowsingSession) -> Dict[str, Any]:
    """Compute pacing metrics for a browsing session.

    Returns:
        events_per_minute: average events per active minute
        active_minutes: number of minutes with at least one event
        total_minutes: total session span in minutes
        coverage_ratio: fraction of minutes that had activity
        variance: variance in per-minute event counts
        label: 'steady', 'bursty', or 'sparse'
    """
    events = session.events
    if not events:
        return {
            "events_per_minute": 0.0,
            "active_minutes": 0,
            "total_minutes": 0,
            "coverage_ratio": 0.0,
            "variance": 0.0,
            "label": "sparse",
        }

    start_ts = _parse_ts(events[0].timestamp)
    end_ts = _parse_ts(events[-1].timestamp)
    total_minutes = max(1, int((end_ts - start_ts) // 60) + 1)

    bucket_counts: Dict[int, int] = defaultdict(int)
    for evt in events:
        b = _bucket_minute(evt.timestamp, start_ts)
        bucket_counts[b] += 1

    active_minutes = len(bucket_counts)
    counts: List[int] = list(bucket_counts.values())
    avg = sum(counts) / active_minutes
    variance = sum((c - avg) ** 2 for c in counts) / active_minutes
    coverage_ratio = round(active_minutes / total_minutes, 4)

    if coverage_ratio >= 0.7 and variance <= 4.0:
        label = "steady"
    elif variance > 10.0:
        label = "bursty"
    else:
        label = "sparse"

    return {
        "events_per_minute": round(avg, 4),
        "active_minutes": active_minutes,
        "total_minutes": total_minutes,
        "coverage_ratio": coverage_ratio,
        "variance": round(variance, 4),
        "label": label,
    }
