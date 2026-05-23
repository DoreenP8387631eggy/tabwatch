"""API endpoints for session replay."""

from flask import Blueprint, jsonify, current_app

from backend.summarizer.replay import build_replay

replay_bp = Blueprint("replay", __name__)


def _store():
    return current_app.config["SESSION_STORE"]


@replay_bp.route("/sessions/<session_id>/replay", methods=["GET"])
def get_replay(session_id: str):
    """Return all replay frames for the session in chronological order."""
    session = _store().load(session_id)
    if session is None:
        return jsonify({"error": "session not found"}), 404

    frames = build_replay(session)
    return jsonify({
        "session_id": session_id,
        "total_frames": len(frames),
        "frames": [f.to_dict() for f in frames],
    })


@replay_bp.route("/sessions/<session_id>/replay/<int:index>", methods=["GET"])
def get_frame(session_id: str, index: int):
    """Return a single replay frame by its index."""
    session = _store().load(session_id)
    if session is None:
        return jsonify({"error": "session not found"}), 404

    frames = build_replay(session)
    if index < 0 or index >= len(frames):
        return jsonify({"error": "frame index out of range"}), 404

    return jsonify(frames[index].to_dict())


def init_replay(app):
    app.register_blueprint(replay_bp)
