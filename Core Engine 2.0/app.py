#!/usr/bin/env python3
"""
Viser AI — Splash / Landing page (optional).
Run standalone:  python app.py  → http://localhost:8080
The /main route embeds the main dashboard (web_ui_v2.py on port 5000).

To run the full stack use:  python launch.py
"""

from flask import Flask, render_template
from flask_socketio import SocketIO


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder="templates_splash",
        static_folder="static",
    )
    app.config["SECRET_KEY"] = "spec2-splash-secret"
    return app


app = create_app()
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading",
    ping_timeout=60,
    ping_interval=25,
)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/main")
def main():
    return render_template("main.html")


@socketio.on("connect")
def on_connect():
    app.logger.info("Client connected to splash app")
    socketio.emit("log", {"level": "info", "message": "Connected"})


@socketio.on("disconnect")
def on_disconnect():
    app.logger.info("Client disconnected from splash app")


if __name__ == "__main__":
    print("\n🚀 Splash UI server starting…")
    print("   → http://localhost:8080\n")
    socketio.run(app, host="0.0.0.0", port=8080, debug=False, allow_unsafe_werkzeug=True)






