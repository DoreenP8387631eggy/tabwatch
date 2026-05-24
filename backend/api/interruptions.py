"""Flask blueprint exposing interruption metrics for a browsing session."""

from flask import Blueprint, jsonify, current_app
from backend.summarizer.interruptions import compute_interruptions

bp = Blueprint("interruptions", __name__)


def _store():
    return current_app.config["SESSION_STORE"]


def init_interruptions(app):
    app.register_blueprint(bp, url_prefix="/sessions")


@bp.get("/<session_id>/interruptions")
def get_interruptions(session_id: str):
    """Return full interruption analysis for a session."""
    session = _store().load(session_id)
    if session is None:
        return jsonify({"error": "session not found"}), 404

    result = compute_interruptions(session)
    return jsonify({"session_id": session_id, **result})


@bp.get("/<session_id>/interruptions/count")
def get_interruption_count(session_id: str):
    """Return only the total interruption count."""
    session = _store().load(session_id)
    if session is None:
        return jsonify({"error": "session not found"}), 404

    result = compute_interruptions(session)
    return jsonify({
        "session_id": session_id,
        "interruption_count": result["interruption_count"],
    })


@bp.get("/<session_id>/interruptions/most-interrupted")
def get_most_interrupted(session_id: str):
    """Return the domain most frequently interrupted."""
    session = _store().load(session_id)
    if session is None:
        return jsonify({"error": "session not found"}), 404

    result = compute_interruptions(session)
    return jsonify({
        "session_id": session_id,
        "most_interrupted_domain": result["most_interrupted_domain"],
    })
