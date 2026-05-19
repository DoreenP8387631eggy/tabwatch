import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from backend.models.session import BrowsingSession, TabEvent

DATA_DIR = Path(os.getenv("TABWATCH_DATA_DIR", "data/sessions"))


class SessionStore:
    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _session_path(self, session_id: str) -> Path:
        return self.data_dir / f"{session_id}.json"

    def save(self, session: BrowsingSession) -> None:
        path = self._session_path(session.session_id)
        with open(path, "w") as f:
            json.dump(session.to_dict(), f, indent=2)

    def load(self, session_id: str) -> Optional[BrowsingSession]:
        path = self._session_path(session_id)
        if not path.exists():
            return None
        with open(path) as f:
            data = json.load(f)
        return self._deserialize(data)

    def list_sessions(self) -> List[str]:
        return [p.stem for p in sorted(self.data_dir.glob("*.json"))]

    def _deserialize(self, data: dict) -> BrowsingSession:
        session = BrowsingSession(
            session_id=data["session_id"],
            started_at=datetime.fromisoformat(data["started_at"]),
            ended_at=datetime.fromisoformat(data["ended_at"]) if data["ended_at"] else None,
        )
        for e in data.get("events", []):
            session.events.append(
                TabEvent(
                    url=e["url"],
                    title=e["title"],
                    timestamp=datetime.fromisoformat(e["timestamp"]),
                    event_type=e["event_type"],
                    duration_seconds=e.get("duration_seconds"),
                )
            )
        return session
