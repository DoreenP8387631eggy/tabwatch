"""API endpoints for per-category time breakdown."""

from flask import Blueprint, jsonify, current_app

from backend.summarizer.categories import compute_category_time, top_categories


def _store():
    return current_app.config["SESSION_STORE"]


def init_categories(app):
    bp = Blueprint("categories", __name__)

    @bp.route("/sessions/<session_id>/categories", methods=["GET"])
    def get_categories(session_id):
        """Return time-spent (seconds) per category for a session."""
        session = _store().load(session_id)
        if session is None:
            return jsonify({"error": "session not found"}), 404

        breakdown = compute_category_time(session)
        total = sum(breakdown.values())
        return jsonify({
            "session_id": session_id,
            "categories": breakdown,
            "total_seconds": round(total, 2),
        })

    @bp.route("/sessions/<session_id>/categories/top", methods=["GET"])
    def get_top_categories(session_id):
        """Return top categories ranked by time spent."""
        session = _store().load(session_id)
        if session is None:
            return jsonify({"error": "session not found"}), 404

        ranked = top_categories(session)
        return jsonify({
            "session_id": session_id,
            "top_categories": ranked,
        })

    app.register_blueprint(bp)
