# ============================================================
# app/api/routes.py -- REST API Route Handlers
# ============================================================
#
# PURPOSE:
#   Defines all HTTP endpoints exposed by the backend.
#   These supplement the WebSocket events — useful for:
#     - Initial data fetch when the frontend first loads
#     - Health checks and monitoring
#     - Simulation control (start/stop)
#     - Debugging via browser or curl
#
# ARCHITECTURE RULE:
#   Routes must NOT contain business logic.
#   They only:
#     1. Parse/validate the request
#     2. Call a service function or read from the store
#     3. Return a JSON response
#
# HOW IT CONNECTS:
#   Imported by app/api/__init__.py
#   Registered on the Flask app via app/__init__.py
# ============================================================

from flask import jsonify
from app.api import api_blueprint
from app.store.state import store
from app.services.simulation import engine as sim_engine
from app.services.broadcaster import is_broadcaster_running


# ── GET /api/status ─────────────────────────────────────────
@api_blueprint.route("/status", methods=["GET"])
def get_status():
    """
    Returns the current system status including live statistics.
    Used by the frontend StatusBar component on initial load.
    """
    summary = store.get_summary()

    return jsonify({
        "status": "online",
        "message": "ATC Monitoring System is running",
        "version": "1.0.0",
        "simulation_running": sim_engine.is_running(),
        "broadcaster_running": is_broadcaster_running(),
        "aircraft_count": summary["aircraft_count"],
        "alert_count": summary["alert_count"],
        "red_alerts": summary["red_alerts"],
        "yellow_alerts": summary["yellow_alerts"],
    }), 200


# ── GET /api/aircraft ───────────────────────────────────────
@api_blueprint.route("/aircraft", methods=["GET"])
def get_aircraft():
    """
    Returns a snapshot of all currently tracked aircraft.
    Used for initial data load or debugging.
    """
    all_aircraft = store.get_all_aircraft()

    return jsonify({
        "count": len(all_aircraft),
        "aircraft": [ac.to_dict() for ac in all_aircraft]
    }), 200


# ── GET /api/alerts ─────────────────────────────────────────
@api_blueprint.route("/alerts", methods=["GET"])
def get_alerts():
    """
    Returns all active collision alerts.
    Used for initial data load or debugging.
    """
    alerts = store.get_alerts()

    return jsonify({
        "count": len(alerts),
        "alerts": [alert.to_dict() for alert in alerts]
    }), 200


# ── POST /api/simulation/start ──────────────────────────────
@api_blueprint.route("/simulation/start", methods=["POST"])
def start_simulation():
    """Starts the simulation engine."""
    sim_engine.start()
    return jsonify({"message": "Simulation started", "running": True}), 200


# ── POST /api/simulation/stop ───────────────────────────────
@api_blueprint.route("/simulation/stop", methods=["POST"])
def stop_simulation():
    """Stops the simulation engine."""
    sim_engine.stop()
    return jsonify({"message": "Simulation stopped", "running": False}), 200
