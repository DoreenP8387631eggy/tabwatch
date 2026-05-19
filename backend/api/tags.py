"""API routes for session tag classification."""

from flask import Blueprint, jsonify, current_app
from backend.summarizer.tags import compute_tags
from backend.summarizer.summarize import _extract_domain

tags_bp = Blueprint("tags", __name__)


@tags_bp.route("/sessions/<session_id>/tags", methods=["GET"])
def get_tags(session_id: str):
    """Return computed tags for a session based on visited domains."""
    store = current_app.config["store"]
    session = store.load(session_id)
    if session is None:
        return jsonify({"error": "Session not found"}), 404

    domains = [
        _extract_domain(event.url)
        for event in session.events
        if event.url
    ]

    tags = compute_tags(domains)
    return jsonify({
        "session_id": session_id,
        "tags": tags,
        "domain_count": len(domains),
    }), 200


@tags_bp.route("/sessions/<session_id>/tags/breakdown", methods=["GET"])
def get_tags_breakdown(session_id: str):
    """Return per-domain tag breakdown for a session."""
    store = current_app.config["store"]
    session = store.load(session_id)
    if session is None:
        return jsonify({"error": "Session not found"}), 404

    from backend.summarizer.tags import classify_domain
    breakdown = {}
    for event in session.events:
        if event.url:
            domain = _extract_domain(event.url)
            tag = classify_domain(domain)
            breakdown[domain] = tag

    return jsonify({
        "session_id": session_id,
        "breakdown": breakdown,
    }), 200
