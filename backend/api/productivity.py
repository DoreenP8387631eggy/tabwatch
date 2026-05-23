"""API endpoints for session productivity scoring."""

from __future__ import annotations

from flask import Blueprint, jsonify

from backend.storage.session_store import SessionStore
from backend.summarizer.productivity import compute_productivity

_store: SessionStore | None = None

productivity_bp = Blueprint("productivity", __name__)


def init_productivity(store: SessionStore) -> None:
    global _store
    _store = store


@productivity_bp.get("/sessions/<session_id>/productivity")
def get_productivity(session_id: str):
    """Return the full productivity breakdown for a session."""
    session = _store.load(session_id)
    if session is None:
        return jsonify({"error": "session not found"}), 404

    result = compute_productivity(session)
    return jsonify(result), 200


@productivity_bp.get("/sessions/<session_id>/productivity/score")
def get_productivity_score(session_id: str):
    """Return only the numeric productivity score and label."""
    session = _store.load(session_id)
    if session is None:
        return jsonify({"error": "session not found"}), 404

    result = compute_productivity(session)
    return jsonify({"score": result["score"], "label": result["label"]}), 200
