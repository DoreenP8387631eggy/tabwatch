from flask import Flask

from backend.api.sessions import sessions_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(sessions_bp)

    @app.route("/health")
    def health():
        return {"status": "ok"}, 200

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
