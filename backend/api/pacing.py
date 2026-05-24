"""API routes for pacing analysis."""

from flask import Blueprint, jsonify, current_app
from backend.summarizer.pacing import compute_pacing


def init_pacing(app, store):
    bp = Blueprint("pacing", __name__)

    def _store():
        return store

    @bp.route("/sessions/<session_id>/pacing", methods=["GET"])
    def get_pacing(session_id):
        """Return full pacing analysis for a session."""
        session = _store().load(session_id)
        if session is None:
            return jsonify({"error": "Session not found"}), 404
        result = compute_pacing(session)
        return jsonify(result), 200

    @bp.route("/sessions/<session_id>/pacing/label", methods=["GET"])
    def get_pacing_label(session_id):
        """Return only the pacing label ('steady', 'bursty', or 'sparse')."""
        session = _store().load(session_id)
        if session is None:
            return jsonify({"error": "Session not found"}), 404
        result = compute_pacing(session)
        return jsonify({"label": result["label"]}), 200

    @bp.route("/sessions/<session_id>/pacing/coverage", methods=["GET"])
    def get_pacing_coverage(session_id):
        """Return the coverage ratio and active/total minutes."""
        session = _store().load(session_id)
        if session is None:
            return jsonify({"error": "Session not found"}), 404
        result = compute_pacing(session)
        return jsonify({
            "coverage_ratio": result["coverage_ratio"],
            "active_minutes": result["active_minutes"],
            "total_minutes": result["total_minutes"],
        }), 200

    app.register_blueprint(bp)
