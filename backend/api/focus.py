"""API routes for focus analysis."""

from flask import Blueprint, jsonify

from backend.storage.session_store import SessionStore
from backend.summarizer.focus import compute_focus

focus_bp = Blueprint("focus", __name__)
_store: SessionStore | None = None


def init_focus(store: SessionStore) -> None:
    global _store
    _store = store


@focus_bp.route("/sessions/<session_id>/focus", methods=["GET"])
def get_focus(session_id: str):
    """Return focus metrics for the given session."""
    session = _store.load(session_id)
    if session is None:
        return jsonify({"error": "session not found"}), 404

    data = compute_focus(session)
    data["session_id"] = session_id
    return jsonify(data), 200


@focus_bp.route("/sessions/<session_id>/focus/score", methods=["GET"])
def get_focus_score(session_id: str):
    """Return a single 0–100 focus score derived from the focus ratio."""
    session = _store.load(session_id)
    if session is None:
        return jsonify({"error": "session not found"}), 404

    data = compute_focus(session)
    # Scale ratio to 0-100 and blend with deep-focus bonus
    total_visits = data["focused_visits"] + data["shallow_visits"]
    deep_bonus = 0
    if total_visits > 0:
        deep_bonus = round((data["deep_focus_visits"] / total_visits) * 20)

    score = min(100, round(data["focus_ratio"] * 80) + deep_bonus)
    return jsonify({"session_id": session_id, "focus_score": score}), 200
