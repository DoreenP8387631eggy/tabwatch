"""Application factory for tabwatch backend."""

from flask import Flask, jsonify

from backend.storage.session_store import SessionStore


def create_app(store: SessionStore | None = None) -> Flask:
    app = Flask(__name__)

    if store is None:
        store = SessionStore()
    app.config["SESSION_STORE"] = store

    from backend.api.sessions import sessions_bp
    from backend.api.summary import summary_bp

    app.register_blueprint(sessions_bp)
    app.register_blueprint(summary_bp)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    return app
