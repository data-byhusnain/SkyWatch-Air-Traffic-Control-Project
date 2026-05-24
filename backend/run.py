# ============================================================
# run.py — Application Entry Point
# ============================================================
#
# PURPOSE:
#   The single command to start the entire backend.
#   Calls the app factory, then starts the SocketIO/eventlet server.
#
# USAGE:
#   cd backend
#   python run.py
#
# WHY socketio.run() instead of app.run()?
#   Flask's built-in app.run() uses a basic WSGI server that does NOT
#   support WebSockets. socketio.run() replaces it with an eventlet
#   server that handles both HTTP (REST) and WebSocket connections
#   on the same port simultaneously.
#
# ARCHITECTURE NOTE:
#   This file should stay minimal — no business logic, no routes.
#   It only knows: create the app, start the server.
# ============================================================

import eventlet
eventlet.monkey_patch()

from app import create_app
from app.extensions import socketio

# Create the Flask application using the factory
app = create_app()

if __name__ == "__main__":
    import os

    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"

    print("=" * 55)
    print("  ATC Monitoring System - Backend Server")
    print("=" * 55)
    print(f"  HTTP   >> http://localhost:{port}")
    print(f"  API    >> http://localhost:{port}/api/status")
    print(f"  WS     >> ws://localhost:{port}/socket.io")
    print(f"  Debug  >> {debug}")
    print("=" * 55)

    # use_reloader=False is important when using background threads.
    # Flask's reloader spawns a second process which would start
    # duplicate threads, causing race conditions.
    socketio.run(
        app,
        host="0.0.0.0",
        port=port,
        debug=debug,
        use_reloader=False
    )
