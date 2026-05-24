"""API blueprint for browsing rhythm endpoints."""

from flask import Blueprint, jsonify
from backend.storage.session_store import SessionStore
from backend.summarizer.rhythm import compute_rhythm

_store: SessionStore | None = None

rhythm_bp = Blueprint("rhythm", __name__)


def init_rhythm(store: SessionStore) -> Blueprint:
    global _store
    _store = store
    return rhythm_bp


@rhythm_bp.get("/sessions/<session_id>/rhythm")
def get_rhythm(session_id: str):
    """Return full rhythm analysis for a session."""
    session = _store.load(session_id)
    if session is None:
        return jsonify({"error": "Session not found"}), 404
    return jsonify(compute_rhythm(session)), 200


@rhythm_bp.get("/sessions/<session_id>/rhythm/label")
def get_rhythm_label(session_id: str):
    """Return only the rhythm label for a session."""
    session = _store.load(session_id)
    if session is None:
        return jsonify({"error": "Session not found"}), 404
    result = compute_rhythm(session)
    return jsonify({"session_id": session_id, "rhythm_label": result["rhythm_label"]}), 200


@rhythm_bp.get("/sessions/<session_id>/rhythm/bursts")
def get_burst_count(session_id: str):
    """Return burst and idle counts for a session."""
    session = _store.load(session_id)
    if session is None:
        return jsonify({"error": "Session not found"}), 404
    result = compute_rhythm(session)
    return jsonify({
        "session_id": session_id,
        "burst_count": result["burst_count"],
        "idle_count": result["idle_count"],
    }), 200
