# ============================================================
# app/sockets/__init__.py — SocketIO Event Handler Registration
# ============================================================
#
# PURPOSE:
#   Turns the sockets/ folder into a Python package.
#   Importing events.py here ensures all @socketio.on() decorators
#   are registered when the app starts, even if nothing else
#   explicitly imports events.py.
#
# HOW IT CONNECTS:
#   app/__init__.py imports this package, which triggers
#   the import of events.py, registering all socket handlers.
# ============================================================

from app.sockets import events  # noqa: F401
