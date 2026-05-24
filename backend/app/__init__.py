# ============================================================
# app/__init__.py — Flask Application Factory
# ============================================================
#
# PURPOSE:
#   The app factory is the central wiring point of the backend.
#   It creates the Flask app, applies config, registers all
#   extensions and blueprints, and returns the ready-to-run app.
#
# WHY AN APP FACTORY?
#   Instead of `app = Flask(__name__)` at module level (which causes
#   circular imports), we wrap creation in create_app().
#   This means:
#   - Tests can call create_app('testing') for isolated test apps
#   - Extensions are initialized cleanly via init_app(app)
#   - No globals are touched at import time
#
# HOW IT CONNECTS:
#   run.py calls create_app() and passes the result to socketio.run()
#   All blueprints, extensions, and socket handlers are wired here.
#
# IMPORTANT — NAMING:
#   The Flask instance is named 'flask_app' (not 'app') inside this
#   function. This is because Python's `import app.sockets` statement
#   binds the name 'app' in the local scope (referring to this package),
#   which would shadow a local variable also named 'app'.
#   Using 'flask_app' avoids this collision entirely.
# ============================================================

import os
from flask import Flask
from flask_cors import CORS

from app.config import config_map
from app.extensions import socketio


def create_app(env: str = None) -> Flask:
    """
    Flask application factory.

    Args:
        env: Environment name — 'development', 'production', or 'testing'.
             Defaults to FLASK_ENV environment variable, or 'development'.

    Returns:
        Configured Flask application instance.
    """

    # Determine which config class to use
    if env is None:
        env = os.getenv("FLASK_ENV", "development")

    # ── Create Flask Instance ────────────────────────────────
    # Named 'flask_app' to avoid shadowing by `import app.sockets` below.
    # In Python, `import X.Y` binds the name X in the current scope.
    # Since our package is called 'app', `import app.sockets` would
    # overwrite a local variable named 'app' with the package module.
    flask_app = Flask(__name__)

    # ── Load Configuration ───────────────────────────────────
    config_class = config_map.get(env, config_map["development"])
    flask_app.config.from_object(config_class)

    print(f"[App] Starting in '{env}' mode")

    # ── Initialize Extensions ────────────────────────────────
    # CORS: allows the React dev server (localhost:5173) to make requests
    # to the Flask server (localhost:5000) without browser CORS errors.
    CORS(flask_app, resources={r"/api/*": {"origins": "*"}})

    # SocketIO: attaches the pre-created socketio instance to this app.
    # async_mode and cors settings were set in extensions.py already.
    socketio.init_app(flask_app)

    # ── Register Blueprints ──────────────────────────────────
    # Import here (not at top) to avoid circular import issues.
    from app.api import api_blueprint
    flask_app.register_blueprint(api_blueprint)

    # ── Register SocketIO Event Handlers ─────────────────────
    # Importing the sockets package triggers events.py import,
    # which registers all @socketio.on() decorators.
    # NOTE: This `import app.sockets` binds 'app' as a local variable
    # pointing to the app package — that's fine because we use 'flask_app'.
    import app.sockets  # noqa: F401

    print("[App] Blueprints and socket handlers registered")
    print(f"[App] Monitoring region: {config_class.BOUNDING_BOX}")

    # ── Start Backend Services ───────────────────────────────
    # Load initial aircraft data and start the realtime pipeline.
    # This runs ONCE on startup, not on every request.
    _initialize_backend_services(config_class)

    return flask_app


def _initialize_backend_services(config_class) -> None:
    """
    Starts the backend pipeline: load data -> simulate -> broadcast.

    Called once during app creation. Separated into its own function
    for clarity and to keep create_app() focused on Flask wiring.

    Order matters:
      1. Load aircraft into the store (so there's data to work with)
      2. Start simulation engine (so positions update smoothly)
      3. Start broadcaster (so clients receive updates)
    """
    from app.services.opensky_service import fetch_aircraft, load_demo_data
    from app.services.simulation import engine as sim_engine
    from app.services.broadcaster import start_broadcaster

    # ── Step 1: Load initial aircraft data ───────────────────
    if config_class.ATC_DEMO_MODE:
        print("\n" + "=" * 55)
        print("                 ATC DEMO MODE ENABLED")
        print("           Using prerecorded aircraft data")
        print("=" * 55 + "\n")
        aircraft = load_demo_data()
    else:
        # Try live API first, fall back to demo data
        print("[App] Loading initial aircraft data...")
        bounding_box = config_class.BOUNDING_BOX
        aircraft = fetch_aircraft(bounding_box, timeout=config_class.OPENSKY_TIMEOUT)
    
        if not aircraft:
            print("[App] Live API unavailable, loading demo data...")
            aircraft = load_demo_data()

    if aircraft is None:
        aircraft = []

    # ── INJECT SIMULATED PAKISTANI FLIGHTS ───────────────────
    from app.services.simulation import generate_synthetic_aircraft
    synthetic_pakistan = generate_synthetic_aircraft(count=20)
    aircraft.extend(synthetic_pakistan)

    if aircraft:
        from app.store.state import store
        store.update_aircraft(aircraft)
        print(f"[App] Loaded {len(aircraft)} aircraft into store (including {len(synthetic_pakistan)} simulated)")
    else:
        print("[App] No aircraft data available (store is empty)")

    # ── Step 2: Start simulation engine ──────────────────────
    sim_engine.start()

    # ── Step 3: Start broadcaster ────────────────────────────
    broadcast_interval = config_class.BROADCAST_INTERVAL
    start_broadcaster(interval_seconds=broadcast_interval)

    print("[App] Backend services started successfully")

