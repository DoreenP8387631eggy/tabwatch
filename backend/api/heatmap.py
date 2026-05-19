"""API endpoints for browsing heatmap data."""

from flask import Blueprint, jsonify, current_app

from backend.summarizer.heatmap import build_heatmap, peak_slot

heatmap_bp = Blueprint("heatmap", __name__)


@heatmap_bp.route("/sessions/<session_id>/heatmap", methods=["GET"])
def get_heatmap(session_id: str):
    """Return the full day/hour heatmap for a session."""
    store = current_app.config["store"]
    session = store.load(session_id)
    if session is None:
        return jsonify({"error": "Session not found"}), 404

    if not session.events:
        return jsonify({
            "session_id": session_id,
            "days": [],
            "hours": [],
            "cells": [],
            "max_count": 0,
        }), 200

    data = build_heatmap(session)
    data["session_id"] = session_id
    return jsonify(data), 200


@heatmap_bp.route("/sessions/<session_id>/heatmap/peak", methods=["GET"])
def get_peak_slot(session_id: str):
    """Return the single busiest day/hour slot for a session."""
    store = current_app.config["store"]
    session = store.load(session_id)
    if session is None:
        return jsonify({"error": "Session not found"}), 404

    if not session.events:
        return jsonify({"session_id": session_id, "peak": None}), 200

    heatmap = build_heatmap(session)
    slot = peak_slot(heatmap)
    return jsonify({"session_id": session_id, "peak": slot}), 200
