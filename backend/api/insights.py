"""API routes for session productivity insights."""

from flask import Blueprint, jsonify, current_app

from backend.summarizer.insights import generate_insights

insights_bp = Blueprint("insights", __name__)


@insights_bp.route("/sessions/<session_id>/insights", methods=["GET"])
def get_insights(session_id: str):
    """Return productivity insights for a specific session."""
    store = current_app.config["SESSION_STORE"]
    session = store.load(session_id)

    if session is None:
        return jsonify({"error": "Session not found"}), 404

    if not session.closed_at:
        return jsonify({"error": "Session is still open; close it before requesting insights"}), 400

    result = generate_insights(session)
    return jsonify(result), 200


@insights_bp.route("/sessions/<session_id>/insights/score", methods=["GET"])
def get_score(session_id: str):
    """Return only the productivity score for a session."""
    store = current_app.config["SESSION_STORE"]
    session = store.load(session_id)

    if session is None:
        return jsonify({"error": "Session not found"}), 404

    if not session.closed_at:
        return jsonify({"error": "Session is still open"}), 400

    result = generate_insights(session)
    return jsonify(
        {
            "session_id": session_id,
            "score": result["score"],
            "duration_seconds": result["duration_seconds"],
        }
    ), 200
