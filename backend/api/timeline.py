"""API endpoints for session timeline."""

from flask import Blueprint, jsonify, current_app

from backend.summarizer.timeline import build_timeline

timeline_bp = Blueprint("timeline", __name__)


@timeline_bp.route("/sessions/<session_id>/timeline", methods=["GET"])
def get_timeline(session_id: str):
    """Return a bucketed timeline of activity for a session."""
    store = current_app.config["SESSION_STORE"]
    session = store.load(session_id)
    if session is None:
        return jsonify({"error": "Session not found"}), 404

    timeline = build_timeline(session)
    return jsonify({
        "session_id": session_id,
        "bucket_minutes": 5,
        "timeline": timeline,
    }), 200


@timeline_bp.route("/sessions/<session_id>/timeline/peak", methods=["GET"])
def get_peak_bucket(session_id: str):
    """Return the single busiest time bucket for a session."""
    store = current_app.config["SESSION_STORE"]
    session = store.load(session_id)
    if session is None:
        return jsonify({"error": "Session not found"}), 404

    timeline = build_timeline(session)
    if not timeline:
        return jsonify({"session_id": session_id, "peak": None}), 200

    peak = max(timeline, key=lambda b: b["event_count"])
    return jsonify({"session_id": session_id, "peak": peak}), 200
