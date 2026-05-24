# ============================================================
# app/models/aircraft.py -- Core Data Models
# ============================================================
#
# PURPOSE:
#   Defines the shape of every data object in the system.
#   Two models live here:
#     1. Aircraft     -- represents one tracked aircraft
#     2. CollisionAlert -- represents a proximity warning between two aircraft
#
# WHY DATACLASSES (not dicts, not Pydantic, not SQLAlchemy)?
#   - Built into Python 3.7+ (no extra dependency)
#   - Auto-generates __init__, __repr__, __eq__ for free
#   - Type hints serve as self-documentation
#   - Mutable by default (we need to update positions each tick)
#   - Simpler than Pydantic for a semester project
#   - No database ORM needed -- these live in memory only
#
# HOW THESE MODELS CONNECT TO OTHER MODULES:
#
#   opensky_service.py  --> creates Aircraft objects from API response
#   simulation.py       --> mutates Aircraft.latitude/longitude/altitude each tick
#   collision.py        --> reads Aircraft pairs, creates CollisionAlert objects
#   state.py            --> stores dict[icao24, Aircraft] and list[CollisionAlert]
#   broadcaster.py      --> calls to_dict() on each object before SocketIO emit
#   routes.py           --> calls to_dict() for JSON REST responses
#
# SERIALIZATION:
#   Flask's jsonify() cannot serialize dataclass objects directly.
#   Each model has a to_dict() method that returns a plain Python dict.
#   These dicts are JSON-serializable and sent to the frontend as-is.
#
# MUTABILITY:
#   Both dataclasses are mutable (frozen=False, the default).
#   This is intentional -- the simulation engine updates aircraft
#   positions in-place every tick rather than creating new objects.
# ============================================================

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Aircraft:
    """
    Represents a single tracked aircraft in the ATC system.

    An Aircraft object is created when:
      - OpenSky API returns a new state vector (source="LIVE")
      - The simulation engine generates a synthetic aircraft (source="SIMULATED")

    The object is then:
      - Stored in state.py's AircraftStore (keyed by icao24)
      - Mutated by simulation.py each tick (lat/lon/altitude change)
      - Read by collision.py to compute pairwise distances
      - Serialized by broadcaster.py and sent to the React frontend
    """

    # ── Identity ─────────────────────────────────────────────
    # icao24: Unique 24-bit ICAO transponder address (hex string).
    #   This is the primary key for every aircraft in the system.
    #   Example: "3c6752" (a Lufthansa aircraft)
    #   OpenSky uses this as the unique identifier in their API.
    icao24: str

    # callsign: The flight number / radio callsign.
    #   Example: "DLH1234", "MAS370", "SIA21"
    #   Can be empty string if the aircraft isn't broadcasting one.
    callsign: str = ""

    # ── Position ─────────────────────────────────────────────
    # latitude: Decimal degrees, positive = North, negative = South.
    #   Range: -90.0 to +90.0
    #   Example: 3.1390 (Kuala Lumpur)
    latitude: float = 0.0

    # longitude: Decimal degrees, positive = East, negative = West.
    #   Range: -180.0 to +180.0
    #   Example: 101.6869 (Kuala Lumpur)
    longitude: float = 0.0

    # altitude: Barometric altitude in METERS above sea level.
    #   OpenSky returns this in meters. We keep it in meters internally.
    #   Frontend can convert to feet for display (1 meter = 3.281 feet).
    #   Example: 10668.0 (about 35,000 feet -- typical cruising altitude)
    altitude: float = 0.0

    # ── Movement ─────────────────────────────────────────────
    # velocity: Ground speed in METERS PER SECOND.
    #   OpenSky returns m/s. We keep it in m/s internally.
    #   Frontend can convert to knots for display (1 m/s = 1.944 knots).
    #   Example: 250.0 (about 486 knots -- typical cruising speed)
    velocity: float = 0.0

    # heading: True track angle in DEGREES clockwise from North.
    #   0 = North, 90 = East, 180 = South, 270 = West
    #   Used by simulation.py to compute direction of movement.
    #   Example: 45.0 (heading northeast)
    heading: float = 0.0

    # vertical_rate: Rate of climb or descent in METERS PER SECOND.
    #   Positive = climbing, Negative = descending, 0 = level flight.
    #   Used by simulation.py to update altitude each tick.
    #   Example: 5.0 (climbing at ~1000 feet per minute)
    vertical_rate: float = 0.0

    # ── Metadata ─────────────────────────────────────────────
    # origin_country: Country where the aircraft is registered.
    #   Comes directly from OpenSky. Not used in simulation logic,
    #   but nice to display on the frontend's aircraft list panel.
    #   Example: "Malaysia", "United States", "Germany"
    origin_country: str = ""

    # alert_level: Current collision risk assessment for this aircraft.
    #   Set by collision.py after pairwise distance checks.
    #   Values: "GREEN" (safe), "YELLOW" (warning), "RED" (danger)
    #   Frontend uses this to color the radar blip and list row.
    alert_level: str = "GREEN"

    # source: Where this aircraft's data came from.
    #   "LIVE"      = fetched from OpenSky API (real aircraft)
    #   "SIMULATED" = generated by simulation engine (synthetic)
    #   Displayed on the frontend so the user knows what's real vs fake.
    source: str = "LIVE"

    # last_updated: ISO 8601 timestamp of the last position update.
    #   Updated every time opensky_service or simulation modifies this aircraft.
    #   Used to detect stale aircraft that should be removed.
    #   Stored as string for easy JSON serialization.
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        """
        Converts this Aircraft to a plain dict for JSON serialization.

        Called by:
          - broadcaster.py before socketio.emit()
          - routes.py before jsonify()

        Returns:
            Dict with all aircraft fields, ready for JSON.
        """
        return {
            "icao24": self.icao24,
            "callsign": self.callsign,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude": self.altitude,
            "velocity": self.velocity,
            "heading": self.heading,
            "vertical_rate": self.vertical_rate,
            "origin_country": self.origin_country,
            "alert_level": self.alert_level,
            "source": self.source,
            "last_updated": self.last_updated,
        }

    def update_timestamp(self) -> None:
        """
        Refreshes last_updated to the current UTC time.
        Called after any position change (simulation tick or API update).
        """
        self.last_updated = datetime.now(timezone.utc).isoformat()


@dataclass
class CollisionAlert:
    """
    Represents a proximity warning between two aircraft.

    Created by collision.py when two aircraft are within WARNING range.
    Stored in state.py's alert list and broadcast to the frontend.

    The frontend uses this to:
      - Show alert banners (colored by level)
      - Flash the involved aircraft blips on the radar
      - List active threats in the alert panel
    """

    # aircraft_1: ICAO24 address of the first aircraft in the pair.
    #   Always the aircraft with the alphabetically lower icao24
    #   to avoid duplicate alerts (A-B and B-A are the same pair).
    aircraft_1: str

    # aircraft_2: ICAO24 address of the second aircraft in the pair.
    aircraft_2: str

    # distance_km: Current distance between the two aircraft in KILOMETERS.
    #   Computed using the Haversine formula (accounts for Earth's curvature).
    #   Rounded to 2 decimal places for display.
    #   Example: 4.73 (RED alert -- under 5 km)
    distance_km: float

    # level: Severity of this collision risk.
    #   "RED"    = distance < DANGER_DISTANCE_KM  (default 50 km)
    #   "YELLOW" = distance < WARNING_DISTANCE_KM (default 100 km)
    #   Thresholds are read from config.py.
    #   (No "GREEN" alerts are created -- GREEN means no alert needed.)
    level: str

    # timestamp: ISO 8601 time when this alert was generated.
    #   Used for ordering alerts chronologically on the frontend.
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        """
        Converts this CollisionAlert to a plain dict for JSON serialization.

        Called by:
          - broadcaster.py before socketio.emit("alert_update", ...)
          - routes.py before jsonify() for GET /api/alerts

        Returns:
            Dict with all alert fields, ready for JSON.
        """
        return {
            "aircraft_1": self.aircraft_1,
            "aircraft_2": self.aircraft_2,
            "distance_km": self.distance_km,
            "level": self.level,
            "timestamp": self.timestamp,
        }
