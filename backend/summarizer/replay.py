"""Build a chronological replay of a browsing session for step-by-step review."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from backend.models.session import BrowsingSession


def _extract_domain(url: str) -> str:
    try:
        host = urlparse(url).hostname or url
        return host.removeprefix("www.")
    except Exception:
        return url


@dataclass
class ReplayFrame:
    index: int
    timestamp: str
    url: str
    domain: str
    title: str
    event_type: str
    duration_since_prev: Optional[float]  # seconds

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "url": self.url,
            "domain": self.domain,
            "title": self.title,
            "event_type": self.event_type,
            "duration_since_prev": self.duration_since_prev,
        }


def build_replay(session: BrowsingSession) -> List[ReplayFrame]:
    """Return ordered replay frames for every event in the session."""
    events = sorted(session.events, key=lambda e: e.timestamp)
    frames: List[ReplayFrame] = []

    for idx, evt in enumerate(events):
        if idx == 0:
            gap = None
        else:
            prev_ts = events[idx - 1].timestamp
            try:
                from datetime import datetime
                fmt = "%Y-%m-%dT%H:%M:%S"
                t1 = datetime.fromisoformat(prev_ts)
                t2 = datetime.fromisoformat(evt.timestamp)
                gap = round((t2 - t1).total_seconds(), 1)
            except Exception:
                gap = None

        frames.append(
            ReplayFrame(
                index=idx,
                timestamp=evt.timestamp,
                url=evt.url,
                domain=_extract_domain(evt.url),
                title=getattr(evt, "title", ""),
                event_type=getattr(evt, "event_type", "visit"),
                duration_since_prev=gap,
            )
        )

    return frames
