"""Persistent storage for session notes using JSON files."""

import json
from pathlib import Path
from typing import Optional


class NotesStore:
    def __init__(self, data_dir: str = "data"):
        self._path = Path(data_dir) / "notes.json"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.write_text(json.dumps([]))

    def _load_all(self) -> list[dict]:
        try:
            return json.loads(self._path.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_all(self, notes: list[dict]) -> None:
        self._path.write_text(json.dumps(notes, indent=2))

    def add(self, note: dict) -> dict:
        notes = self._load_all()
        notes.append(note)
        self._save_all(notes)
        return note

    def get_for_session(self, session_id: str) -> list[dict]:
        return [n for n in self._load_all() if n.get("session_id") == session_id]

    def get_all(self) -> list[dict]:
        return self._load_all()

    def delete_for_session(self, session_id: str) -> int:
        notes = self._load_all()
        remaining = [n for n in notes if n.get("session_id") != session_id]
        removed = len(notes) - len(remaining)
        self._save_all(remaining)
        return removed
