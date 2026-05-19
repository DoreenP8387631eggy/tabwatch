"""API routes for session summaries."""

from flask import Blueprint, current_app, jsonify

from backend.summarizer import summarize_session

summary_bp = Blueprint("summary", __name__)


@summary_bp.get("/sessions/<session_id>/summary")
def get_summary(session_id: str):
    """Return a productivity summary for a specific session."""
    store = current_app.config["SESSION_STORE"]
    session = store.load(session_id)
    if session is None:
        return jsonify({"error": "session not found"}), 404

    summary = summarize_session(session)
    return jsonify(summary), 200


@summary_bp.get("/sessions/summaries")
def list_summaries():
    """Return productivity summaries for all stored sessions."""
    store = current_app.config["SESSION_STORE"]
    session_ids = store.list_sessions()
    summaries = []
    for sid in session_ids:
        session = store.load(sid)
        if session is not None:
            summaries.append(summarize_session(session))

    summaries.sort(key=lambda s: s["session_id"])
    return jsonify(summaries), 200
