"""API routes for session comparison."""

from flask import Blueprint, jsonify, current_app
from backend.summarizer.comparison import compare_sessions

bp = Blueprint("comparison", __name__)


def _store():
    return current_app.config["SESSION_STORE"]


@bp.route("/sessions/<session_a_id>/compare/<session_b_id>", methods=["GET"])
def compare(session_a_id: str, session_b_id: str):
    """Compare two sessions by their IDs."""
    store = _store()
    session_a = store.load(session_a_id)
    if session_a is None:
        return jsonify({"error": f"Session {session_a_id} not found"}), 404

    session_b = store.load(session_b_id)
    if session_b is None:
        return jsonify({"error": f"Session {session_b_id} not found"}), 404

    if not session_a.end_time:
        return jsonify({"error": f"Session {session_a_id} is still open"}), 400

    if not session_b.end_time:
        return jsonify({"error": f"Session {session_b_id} is still open"}), 400

    result = compare_sessions(session_a, session_b)
    return jsonify(result), 200


@bp.route("/sessions/<session_a_id>/compare/<session_b_id>/delta", methods=["GET"])
def compare_delta(session_a_id: str, session_b_id: str):
    """Return only the delta fields between two sessions."""
    store = _store()
    session_a = store.load(session_a_id)
    if session_a is None:
        return jsonify({"error": f"Session {session_a_id} not found"}), 404

    session_b = store.load(session_b_id)
    if session_b is None:
        return jsonify({"error": f"Session {session_b_id} not found"}), 404

    if not session_a.end_time or not session_b.end_time:
        return jsonify({"error": "Both sessions must be closed"}), 400

    result = compare_sessions(session_a, session_b)
    delta = {
        "session_a_id": result["session_a_id"],
        "session_b_id": result["session_b_id"],
        "duration_diff_seconds": result["duration_diff_seconds"],
        "visits_diff": result["visits_diff"],
        "unique_domains_diff": result["unique_domains_diff"],
        "category_percentage_delta": result["category_percentage_delta"],
        "new_top_domains": result["new_top_domains"],
        "dropped_top_domains": result["dropped_top_domains"],
    }
    return jsonify(delta), 200
