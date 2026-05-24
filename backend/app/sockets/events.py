# ============================================================
# app/sockets/events.py — WebSocket Event Handlers
# ============================================================
#
# PURPOSE:
#   Defines all SocketIO event handlers (the WebSocket equivalent
#   of HTTP route handlers).
#
#   In Phase 1: only connect/disconnect events are wired up.
#   Phase 8 will add the aircraft_update and alert_update emitters.
#
# HOW SOCKETIO EVENTS WORK:
#   - @socketio.on('connect')    fires when a client opens a WS connection
#   - @socketio.on('disconnect') fires when a client closes the connection
#   - @socketio.on('my_event')   fires when client emits 'my_event'
#   - socketio.emit('event', data) pushes data to ALL connected clients
#
# HOW IT CONNECTS:
#   Imported by app/sockets/__init__.py
#   socketio instance comes from app/extensions.py (no circular import)
# ============================================================

from flask_socketio import emit
from app.extensions import socketio


from flask import request

# ── Event: Client Connected ──────────────────────────────────
@socketio.on("connect")
def handle_connect():
    print(f"[SocketIO] Client connected: {request.sid}")
    emit("server_message", {"message": "Connected to ATC backend"})


# ── Event: Client Disconnected ───────────────────────────────
@socketio.on("disconnect")
def handle_disconnect():
    print(f"[SocketIO] Client disconnected: {request.sid}")


# ── Event: Client Requests Immediate Update ──────────────────
@socketio.on("request_update")
def handle_request_update():
    """
    Client can emit 'request_update' to get an immediate state push
    without waiting for the next broadcast cycle.
    In Phase 1, we return a placeholder. Phase 8 will send real data.
    """
    print("[SocketIO] Client requested immediate update")
    emit("server_message", {"message": "Update requested — data coming in Phase 8"})
