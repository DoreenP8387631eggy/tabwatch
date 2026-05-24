"""API endpoints for browsing pattern detection."""

from flask import Blueprint, jsonify, current_app
from backend.summarizer.patterns import detect_patterns

patterns_bp = Blueprint("patterns", __name__)


def _store():
    return current_app.config["SESSION_STORE"]


def _load_closed_sessions(store):
    """Load all sessions that have been closed (have an end_time)."""
    all_ids = store.list_sessions()
    sessions = []
    for sid in all_ids:
        session = store.load(sid)
        if session and session.end_time is not None:
            sessions.append(session)
    return sessions


@patterns_bp.route("/patterns", methods=["GET"])
def get_patterns():
    """Return recurring browsing patterns across all closed sessions."""
    store = _store()
    sessions = _load_closed_sessions(store)

    if not sessions:
        return jsonify({
            "session_count": 0,
            "patterns": {
                "recurring_domains": [],
                "peak_hours": [],
                "avg_session_duration": 0,
                "most_consistent_domain": None,
            },
        }), 200

    result = detect_patterns(sessions)
    return jsonify({"session_count": len(sessions), "patterns": result}), 200


@patterns_bp.route("/patterns/recurring-domains", methods=["GET"])
def get_recurring_domains():
    """Return only the list of recurring domains."""
    store = _store()
    sessions = _load_closed_sessions(store)
    result = detect_patterns(sessions)
    return jsonify({"recurring_domains": result["recurring_domains"]}), 200


@patterns_bp.route("/patterns/peak-hours", methods=["GET"])
def get_peak_hours():
    """Return the top peak hours of browsing activity."""
    store = _store()
    sessions = _load_closed_sessions(store)
    result = detect_patterns(sessions)
    return jsonify({"peak_hours": result["peak_hours"]}), 200
