from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import uuid


@dataclass
class TabEvent:
    url: str
    title: str
    timestamp: datetime
    event_type: str  # 'open', 'close', 'focus', 'blur'
    duration_seconds: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "title": self.title,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "duration_seconds": self.duration_seconds,
        }


@dataclass
class BrowsingSession:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    events: List[TabEvent] = field(default_factory=list)

    def add_event(self, event: TabEvent) -> None:
        self.events.append(event)

    def close(self) -> None:
        self.ended_at = datetime.utcnow()

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.ended_at:
            return (self.ended_at - self.started_at).total_seconds()
        return None

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration_seconds": self.duration_seconds,
            "events": [e.to_dict() for e in self.events],
        }
