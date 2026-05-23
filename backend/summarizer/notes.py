"""Session notes: attach and retrieve user notes for browsing sessions."""

from datetime import datetime, timezone
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_note(session_id: str, text: str, author: str = "user") -> dict:
    """Create a new note dict for a session."""
    if not text or not text.strip():
        raise ValueError("Note text must not be empty.")
    return {
        "session_id": session_id,
        "text": text.strip(),
        "author": author,
        "created_at": _now_iso(),
    }


def list_notes(notes: list[dict], session_id: Optional[str] = None) -> list[dict]:
    """Return notes, optionally filtered by session_id."""
    if session_id is None:
        return list(notes)
    return [n for n in notes if n.get("session_id") == session_id]


def summarize_notes(notes: list[dict]) -> dict:
    """Return a brief summary of the notes for a session."""
    if not notes:
        return {"count": 0, "latest": None, "snippet": None}
    sorted_notes = sorted(notes, key=lambda n: n.get("created_at", ""), reverse=True)
    latest = sorted_notes[0]
    snippet = latest["text"][:80] + ("..." if len(latest["text"]) > 80 else "")
    return {
        "count": len(notes),
        "latest": latest["created_at"],
        "snippet": snippet,
    }
