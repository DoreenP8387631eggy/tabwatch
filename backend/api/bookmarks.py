"""API routes for bookmark detection."""

from flask import Blueprint, jsonify, current_app

from backend.summarizer.bookmarks import detect_bookmarks

bookmarks_bp = Blueprint("bookmarks", __name__)


def _store():
    return current_app.config["SESSION_STORE"]


@bookmarks_bp.route("/sessions/<session_id>/bookmarks", methods=["GET"])
def get_bookmarks(session_id: str):
    """Return bookmark candidates for a session."""
    session = _store().load(session_id)
    if session is None:
        return jsonify({"error": "Session not found"}), 404

    result = detect_bookmarks(session)
    return jsonify(result), 200


@bookmarks_bp.route("/sessions/<session_id>/bookmarks/top", methods=["GET"])
def get_top_bookmark(session_id: str):
    """Return the single most-revisited domain in the session."""
    session = _store().load(session_id)
    if session is None:
        return jsonify({"error": "Session not found"}), 404

    result = detect_bookmarks(session)
    candidates = result["bookmark_candidates"]
    if not candidates:
        return jsonify({"top_bookmark": None, "message": "No bookmark candidates found"}), 200

    return jsonify({"top_bookmark": candidates[0]}), 200


def init_bookmarks(app):
    app.register_blueprint(bookmarks_bp)
