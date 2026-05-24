# ============================================================
# app/config.py — Configuration Classes
# ============================================================
#
# PURPOSE:
#   Centralizes all application configuration in one place.
#   Values are read from environment variables (loaded from .env).
#   Different config classes allow switching between dev/prod.
#
# ARCHITECTURE DECISION:
#   Using a class-based config (not a flat dict) means:
#   - Config is self-documenting (you see all options in one file)
#   - Easy to add ProductionConfig later without touching other files
#   - Flask's app.config.from_object() reads it cleanly
#
# HOW IT CONNECTS:
#   app/__init__.py calls: app.config.from_object(config[env])
# ============================================================

import os
from dotenv import load_dotenv

# Load .env file into os.environ before any config class reads it
load_dotenv()


class BaseConfig:
    """
    Shared settings inherited by all environments.
    All values come from environment variables with safe defaults.
    """

    # Flask core
    SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "dev-secret-fallback")

    # OpenSky API
    OPENSKY_USERNAME: str = os.getenv("OPENSKY_USERNAME", "")
    OPENSKY_PASSWORD: str = os.getenv("OPENSKY_PASSWORD", "")
    OPENSKY_TIMEOUT: int = int(os.getenv("OPENSKY_TIMEOUT", "10"))
    OPENSKY_POLL_INTERVAL: int = int(os.getenv("OPENSKY_POLL_INTERVAL", "15"))

    # Geographic bounding box for aircraft monitoring
    BOUNDING_BOX: dict = {
        "lamin": float(os.getenv("BOUNDING_LAT_MIN", "1.0")),
        "lamax": float(os.getenv("BOUNDING_LAT_MAX", "7.5")),
        "lomin": float(os.getenv("BOUNDING_LON_MIN", "99.5")),
        "lomax": float(os.getenv("BOUNDING_LON_MAX", "119.5")),
    }

    # Broadcast interval (seconds) — how often to push updates to frontend
    BROADCAST_INTERVAL: int = int(os.getenv("BROADCAST_INTERVAL", "1"))

    # Collision detection thresholds (kilometers)
    DANGER_DISTANCE_KM: float = float(os.getenv("DANGER_DISTANCE_KM", "50"))
    WARNING_DISTANCE_KM: float = float(os.getenv("WARNING_DISTANCE_KM", "100"))

    # Demo modes
    ATC_DEMO_MODE: bool = os.getenv("ATC_DEMO_MODE", "false").lower() == "true"


class DevelopmentConfig(BaseConfig):
    """
    Development environment — verbose logging, debug mode on.
    Used when FLASK_ENV=development (the default).
    """
    DEBUG: bool = True
    TESTING: bool = False


class ProductionConfig(BaseConfig):
    """
    Production environment — debug off, stricter settings.
    Not needed for university demo but good practice to define it.
    """
    DEBUG: bool = False
    TESTING: bool = False


class TestingConfig(BaseConfig):
    """
    Used by pytest — sets TESTING=True which disables error catching
    so tests see actual exceptions, not HTTP 500 responses.
    """
    DEBUG: bool = True
    TESTING: bool = True


# Registry: maps FLASK_ENV string → config class
# Used by the app factory to select the right config
config_map: dict = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
