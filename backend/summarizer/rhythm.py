"""Browsing rhythm analysis: detects regularity and pacing of tab activity."""

from typing import Dict, Any, List
from datetime import datetime
from backend.models.session import BrowsingSession


def _parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def _inter_event_gaps(events: list) -> List[float]:
    """Return list of seconds between consecutive events."""
    if len(events) < 2:
        return []
    gaps = []
    for i in range(1, len(events)):
        t1 = _parse_ts(events[i - 1]["timestamp"])
        t2 = _parse_ts(events[i]["timestamp"])
        diff = (t2 - t1).total_seconds()
        if diff >= 0:
            gaps.append(diff)
    return gaps


def compute_rhythm(session: BrowsingSession) -> Dict[str, Any]:
    """Analyse the pacing rhythm of a browsing session.

    Returns:
        avg_gap_seconds   – mean time between tab events
        median_gap_seconds
        burst_count       – number of bursts (gap < 5 s)
        idle_count        – number of idle pauses (gap > 120 s)
        rhythm_label      – 'frantic' | 'steady' | 'relaxed' | 'idle'
        event_count
    """
    events = [e.to_dict() if hasattr(e, "to_dict") else e for e in session.events]
    if not events:
        return {
            "avg_gap_seconds": 0,
            "median_gap_seconds": 0,
            "burst_count": 0,
            "idle_count": 0,
            "rhythm_label": "idle",
            "event_count": 0,
        }

    gaps = _inter_event_gaps(events)
    event_count = len(events)

    if not gaps:
        return {
            "avg_gap_seconds": 0,
            "median_gap_seconds": 0,
            "burst_count": 0,
            "idle_count": 0,
            "rhythm_label": "idle",
            "event_count": event_count,
        }

    avg_gap = sum(gaps) / len(gaps)
    sorted_gaps = sorted(gaps)
    mid = len(sorted_gaps) // 2
    median_gap = (
        sorted_gaps[mid]
        if len(sorted_gaps) % 2
        else (sorted_gaps[mid - 1] + sorted_gaps[mid]) / 2
    )
    burst_count = sum(1 for g in gaps if g < 5)
    idle_count = sum(1 for g in gaps if g > 120)

    if avg_gap < 10:
        label = "frantic"
    elif avg_gap < 45:
        label = "steady"
    elif avg_gap < 120:
        label = "relaxed"
    else:
        label = "idle"

    return {
        "avg_gap_seconds": round(avg_gap, 2),
        "median_gap_seconds": round(median_gap, 2),
        "burst_count": burst_count,
        "idle_count": idle_count,
        "rhythm_label": label,
        "event_count": event_count,
    }
