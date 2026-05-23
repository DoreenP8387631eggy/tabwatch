"""API endpoints for goal evaluation."""

from flask import Blueprint, jsonify, request, current_app
from backend.summarizer.goals import evaluate_goals, DEFAULT_GOALS

goals_bp = Blueprint("goals", __name__)


def _load_open_session(session_id: str):
    """Load a session and return (session, error_response) tuple.

    Returns (session, None) on success, or (None, error_response) if the
    session is missing or still open.
    """
    store = current_app.config["store"]
    session = store.load(session_id)
    if session is None:
        return None, (jsonify({"error": "Session not found"}), 404)
    if session.end_time is None:
        return None, (jsonify({"error": "Session is still open"}), 400)
    return session, None


@goals_bp.route("/sessions/<session_id>/goals", methods=["GET"])
def get_goals(session_id: str):
    """Evaluate the session against default or query-param-overridden goals."""
    session, err = _load_open_session(session_id)
    if err:
        return err

    goals = dict(DEFAULT_GOALS)
    for key in DEFAULT_GOALS:
        raw = request.args.get(key)
        if raw is not None:
            try:
                goals[key] = float(raw)
            except ValueError:
                return jsonify({"error": f"Invalid value for {key}"}), 400

    result = evaluate_goals(session, goals)
    return jsonify(result), 200


@goals_bp.route("/sessions/<session_id>/goals/summary", methods=["GET"])
def get_goals_summary(session_id: str):
    """Return a brief pass/fail summary for the session goals."""
    session, err = _load_open_session(session_id)
    if err:
        return err

    result = evaluate_goals(session)
    passed = result["goals_met"]
    total = result["goals_total"]
    label = "excellent" if result["all_met"] else ("partial" if passed > 0 else "poor")
    return jsonify({
        "session_id": session_id,
        "passed": passed,
        "total": total,
        "rating": label,
    }), 200
