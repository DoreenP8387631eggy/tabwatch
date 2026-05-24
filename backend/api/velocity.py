from flask import Blueprint, jsonify
from backend.storage.session_store import SessionStore
from backend.summarizer.velocity import compute_velocity

_store: SessionStore | None = None


def init_velocity(store: SessionStore) -> Blueprint:
    global _store
    _store = store
    return _bp


_bp = Blueprint("velocity", __name__)


@_bp.get("/sessions/<session_id>/velocity")
def get_velocity(session_id: str):
    """Return full velocity metrics for the given session."""
    session = _store.load(session_id)
    if session is None:
        return jsonify({"error": "session not found"}), 404
    return jsonify(compute_velocity(session))


@_bp.get("/sessions/<session_id>/velocity/score")
def get_velocity_score(session_id: str):
    """Return a 0-100 velocity score derived from switches-per-minute.

    Scoring:
        0-1  spm  -> 100  (very focused)
        1-5  spm  ->  75
        5-10 spm  ->  50
        >10  spm  ->  25  (highly scattered)
    """
    session = _store.load(session_id)
    if session is None:
        return jsonify({"error": "session not found"}), 404

    metrics = compute_velocity(session)
    spm = metrics["switches_per_minute"]

    if spm <= 1:
        score = 100
    elif spm <= 5:
        score = 75
    elif spm <= 10:
        score = 50
    else:
        score = 25

    return jsonify({
        "session_id": session_id,
        "switches_per_minute": spm,
        "velocity_score": score,
    })
