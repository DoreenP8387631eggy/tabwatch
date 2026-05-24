"""Flask blueprint for mood inference endpoints."""

from flask import Blueprint, jsonify, current_app
from backend.summarizer.mood import infer_mood

bp = Blueprint("mood", __name__)


def _store():
    return current_app.config["SESSION_STORE"]


def init_mood(app):
    app.register_blueprint(bp, url_prefix="/sessions")


@bp.get("/<session_id>/mood")
def get_mood(session_id: str):
    """Return the inferred mood for a session."""
    session = _store().load(session_id)
    if session is None:
        return jsonify({"error": "session not found"}), 404

    result = infer_mood(session)
    return jsonify({
        "session_id": session_id,
        "dominant_mood": result["dominant"],
        "scores": result["scores"],
        "category_breakdown": result["breakdown"],
    })


@bp.get("/<session_id>/mood/dominant")
def get_dominant_mood(session_id: str):
    """Return only the dominant mood label for a session."""
    session = _store().load(session_id)
    if session is None:
        return jsonify({"error": "session not found"}), 404

    result = infer_mood(session)
    return jsonify({
        "session_id": session_id,
        "dominant_mood": result["dominant"],
    })
