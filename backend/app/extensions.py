# ============================================================
# app/extensions.py — Shared Extension Instances
# ============================================================
#
# PURPOSE:
#   Creates SocketIO (and any future extensions) as module-level
#   singletons BEFORE the Flask app exists.
#
# WHY THIS PATTERN EXISTS (important for understanding):
#   Flask extensions like SocketIO need to be initialized with
#   the app object. But if you create SocketIO inside __init__.py,
#   and then another file imports from __init__.py, you get a
#   circular import error like:
#       ImportError: cannot import name 'socketio' from partially
#       initialized module 'app'
#
#   The fix: create the extension here (no app needed yet),
#   then call socketio.init_app(app) inside create_app().
#   Any other file that needs socketio just does:
#       from app.extensions import socketio
#   ...without touching app/__init__.py at all.
#
# HOW IT CONNECTS:
#   - app/__init__.py  → calls socketio.init_app(app)
#   - app/sockets/events.py → uses @socketio.on(...)
#   - app/services/broadcaster.py → calls socketio.emit(...)
# ============================================================

from flask_socketio import SocketIO

# Create the SocketIO instance.
# async_mode='eventlet' tells it to use eventlet for concurrency,
# which is required for background threads to work correctly with Flask.
# cors_allowed_origins='*' allows the React dev server (port 5173) to connect.
socketio = SocketIO(
    async_mode="eventlet",
    cors_allowed_origins="*",
    logger=False,          # Set True to see raw SocketIO protocol logs
    engineio_logger=False  # Set True to see raw Engine.IO transport logs
)
