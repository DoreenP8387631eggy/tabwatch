"""API endpoints for word-cloud data derived from a browsing session."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from backend.summarizer.wordcloud import build_wordcloud


def init_wordcloud(app, store):
    bp = Blueprint("wordcloud", __name__)

    def _store():
        return store

    @bp.route("/sessions/<session_id>/wordcloud", methods=["GET"])
    def get_wordcloud(session_id: str):
        """Return word frequency data for the session."""
        top_n = request.args.get("top_n", 30, type=int)
        top_n = max(1, min(top_n, 100))  # clamp between 1 and 100

        session = _store().load(session_id)
        if session is None:
            return jsonify({"error": "Session not found"}), 404

        data = build_wordcloud(session, top_n=top_n)
        return jsonify({"session_id": session_id, **data})

    @bp.route("/sessions/<session_id>/wordcloud/top", methods=["GET"])
    def get_top_word(session_id: str):
        """Return only the single most-frequent word in the session."""
        session = _store().load(session_id)
        if session is None:
            return jsonify({"error": "Session not found"}), 404

        data = build_wordcloud(session, top_n=1)
        words = data.get("words", [])
        if not words:
            return jsonify({"session_id": session_id, "top_word": None})

        return jsonify({"session_id": session_id, "top_word": words[0]})

    app.register_blueprint(bp)
