# ============================================================
# app/services/opensky_service.py -- OpenSky API Integration
# ============================================================
#
# PURPOSE:
#   Fetches live aircraft data from the OpenSky Network REST API,
#   normalizes the raw response into Aircraft dataclass objects,
#   and handles every failure scenario gracefully.
#
# OPENSKY NETWORK API OVERVIEW:
#   - Free, public REST API for live flight tracking
#   - No authentication required (anonymous access)
#   - Rate limit: 1 request per 10 seconds (anonymous)
#   - Endpoint: https://opensky-network.org/api/states/all
#   - Returns "state vectors" — arrays of flight data for each aircraft
#   - Supports geographic bounding box filtering via query parameters
#   - Documentation: https://openskynetwork.github.io/opensky-api/rest.html
#
# ARCHITECTURE BOUNDARIES:
#   This module is intentionally isolated:
#     - NO Flask imports (not a route handler)
#     - NO SocketIO imports (not a broadcaster)
#     - NO store imports (does not write to state directly)
#     - Returns a plain list[Aircraft] to the caller
#
#   Why? Because the CALLER decides what to do with the data:
#     - broadcaster.py will call fetch_aircraft() and push to the store
#     - tests can call fetch_aircraft() without running Flask
#     - demo mode can call load_demo_data() instead
#
#   This separation makes the module independently testable and
#   keeps the system modular — each layer has one job.
#
# GRACEFUL DEGRADATION STRATEGY:
#   The OpenSky API can fail in many ways:
#     1. Network timeout (your internet is down)
#     2. HTTP 429 (rate limited — too many requests)
#     3. HTTP 500/502/503 (OpenSky server issues)
#     4. Malformed JSON (partial response)
#     5. Empty state list (no aircraft in bounding box)
#     6. Aircraft with missing lat/lon (incomplete data)
#
#   This module handles ALL of these by:
#     - Catching every exception type
#     - Logging the error clearly to console
#     - Returning an empty list [] on failure (NEVER raising)
#     - Letting the caller fall back to simulation or demo data
#
#   The system NEVER crashes due to an API failure.
#
# HOW IT CONNECTS:
#   broadcaster.py (Phase 8) will call:
#     aircraft_list = fetch_aircraft(bounding_box, timeout)
#     if aircraft_list:
#         store.update_aircraft(aircraft_list)
#     else:
#         # keep existing aircraft, continue simulation
#
# ============================================================

import json
import os
from datetime import datetime, timezone
from typing import Optional

import requests

from app.models.aircraft import Aircraft


# ═══════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════

# OpenSky REST API base URL
OPENSKY_API_URL: str = "https://opensky-network.org/api/states/all"

# Default bounding box: Pakistan region
# Latitude:  23.5°N to 37.0°N (Karachi to northern areas)
# Longitude: 60.0°E to 77.5°E (Balochistan to Kashmir border)
#
# You can change this to any region. Common examples:
#   Malaysia:  lamin=1.0,  lamax=7.5,  lomin=99.5,  lomax=119.5
#   Europe:    lamin=35.0, lamax=60.0, lomin=-10.0, lomax=30.0
#   USA:       lamin=24.0, lamax=50.0, lomin=-125.0, lomax=-66.0
#   Pakistan:  lamin=23.5, lamax=37.0, lomin=60.0,  lomax=77.5
DEFAULT_BOUNDING_BOX: dict = {
    "lamin": 23.5,
    "lamax": 37.0,
    "lomin": 60.0,
    "lomax": 77.5,
}

# Default request timeout in seconds
DEFAULT_TIMEOUT: int = 10

# Path to demo data fallback file (relative to backend/ directory)
DEMO_DATA_PATH: str = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "demo_data.json"
)

# ═══════════════════════════════════════════════════════════════
# OPENSKY STATE VECTOR INDEX REFERENCE
# ═══════════════════════════════════════════════════════════════
#
# The OpenSky API returns each aircraft as a JSON array (not a dict).
# Each element is accessed by index. Here's the full mapping:
#
#   Index  Field            Type     Description
#   ─────  ─────────────    ──────   ────────────────────────────────
#   0      icao24           string   Unique ICAO 24-bit transponder address
#   1      callsign         string   Flight callsign (may be null)
#   2      origin_country   string   Country of aircraft registration
#   3      time_position    int      Unix timestamp of last position report
#   4      last_contact     int      Unix timestamp of last signal received
#   5      longitude        float    Decimal degrees (may be null)
#   6      latitude         float    Decimal degrees (may be null)
#   7      baro_altitude    float    Barometric altitude in meters (may be null)
#   8      on_ground        bool     Whether aircraft is on the ground
#   9      velocity         float    Ground speed in m/s (may be null)
#   10     true_track       float    Heading in degrees from North (may be null)
#   11     vertical_rate    float    Climb/descent in m/s (may be null)
#   12     sensors          array    IDs of receivers (not used by us)
#   13     geo_altitude     float    Geometric altitude in meters (may be null)
#   14     squawk           string   Transponder squawk code (may be null)
#   15     spi              bool     Special position indicator
#   16     position_source  int      0=ADS-B, 1=ASTERIX, 2=MLAT, 3=FLARM
#
# IMPORTANT NOTES:
#   - Many fields can be null/None (aircraft not broadcasting)
#   - We SKIP aircraft with null latitude OR longitude (can't plot them)
#   - We SKIP aircraft that are on_ground (index 8 = True)
#   - All other null fields get safe defaults (0.0, "", etc.)
#


# ═══════════════════════════════════════════════════════════════
# MAIN FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def fetch_aircraft(
    bounding_box: Optional[dict] = None,
    timeout: int = DEFAULT_TIMEOUT
) -> list[Aircraft]:
    """
    Fetches live aircraft data from the OpenSky Network API.

    Workflow:
      1. Build the request URL with bounding box parameters
      2. Send HTTP GET request with timeout
      3. Parse the JSON response
      4. Extract the 'states' array
      5. Normalize each state vector into an Aircraft object
      6. Skip any aircraft with missing position data
      7. Return the list of valid Aircraft objects

    Args:
        bounding_box: Dict with keys: lamin, lamax, lomin, lomax.
                      Defaults to Pakistan region if not provided.
        timeout: Request timeout in seconds. Default 10.

    Returns:
        List of Aircraft objects. Empty list on ANY failure.
        The caller should check: if not aircraft_list: use_fallback()

    Example successful return:
        [
            Aircraft(icao24="3c6752", callsign="DLH1234", latitude=33.69, ...),
            Aircraft(icao24="a1b2c3", callsign="PIA203",  latitude=24.86, ...),
        ]

    Example failure return:
        []  (empty list — caller falls back to simulation/demo)
    """
    if bounding_box is None:
        bounding_box = DEFAULT_BOUNDING_BOX

    # Build query parameters for the bounding box filter
    params: dict = {
        "lamin": bounding_box["lamin"],
        "lamax": bounding_box["lamax"],
        "lomin": bounding_box["lomin"],
        "lomax": bounding_box["lomax"],
    }

    try:
        print(f"[OpenSky] Fetching aircraft in region: {bounding_box}")

        # ── Send the HTTP GET request ────────────────────────
        response = requests.get(
            OPENSKY_API_URL,
            params=params,
            timeout=timeout
        )

        # ── Check for HTTP errors ────────────────────────────
        # 429 = rate limited, 500/502/503 = server error
        if response.status_code == 429:
            print("[OpenSky] Rate limited (HTTP 429). Will retry next cycle.")
            return []

        if response.status_code != 200:
            print(f"[OpenSky] HTTP error: {response.status_code}")
            return []

        # ── Parse JSON response ──────────────────────────────
        data = response.json()

        # ── Extract state vectors ────────────────────────────
        # The API returns: {"time": 1234567, "states": [[...], [...], ...]}
        # "states" can be null if no aircraft are in the bounding box
        states = data.get("states")

        if states is None or len(states) == 0:
            print("[OpenSky] No aircraft found in bounding box.")
            return []

        # ── Normalize each state vector ──────────────────────
        aircraft_list: list[Aircraft] = []
        skipped: int = 0

        for state_vector in states:
            aircraft = normalize_state(state_vector)
            if aircraft is not None:
                aircraft_list.append(aircraft)
            else:
                skipped += 1

        print(
            f"[OpenSky] Fetched {len(aircraft_list)} aircraft "
            f"(skipped {skipped} invalid/grounded)"
        )
        return aircraft_list

    # ── Error Handling (never crash) ─────────────────────────

    except requests.exceptions.Timeout:
        print(f"[OpenSky] Request timed out after {timeout}s. Skipping this cycle.")
        return []

    except requests.exceptions.ConnectionError:
        print("[OpenSky] Connection error (no internet?). Skipping this cycle.")
        return []

    except requests.exceptions.RequestException as e:
        # Catches all other requests errors (SSL, redirect, etc.)
        print(f"[OpenSky] Request failed: {e}")
        return []

    except json.JSONDecodeError:
        print("[OpenSky] Received malformed JSON. Skipping this cycle.")
        return []

    except Exception as e:
        # Ultimate safety net — log and continue
        print(f"[OpenSky] Unexpected error: {type(e).__name__}: {e}")
        return []


def normalize_state(state_vector: list) -> Optional[Aircraft]:
    """
    Converts a raw OpenSky state vector (array) into an Aircraft object.

    Handles missing/null fields safely by providing sensible defaults.
    Returns None for aircraft that should be skipped:
      - Missing latitude or longitude (can't be plotted on radar)
      - On the ground (not relevant for air traffic monitoring)
      - Malformed data (too few elements in the array)

    Args:
        state_vector: A list of 17 elements from the OpenSky API.
                      See the index reference at the top of this file.

    Returns:
        Aircraft object if valid, None if the aircraft should be skipped.

    Example input (raw OpenSky state vector):
        ["3c6752", "DLH1234 ", "Germany", 1716000000, 1716000000,
         101.69, 3.14, 10668.0, False, 250.0, 45.0, 0.0,
         None, 10700.0, "1234", False, 0]

    Example output (Aircraft object):
        Aircraft(icao24="3c6752", callsign="DLH1234", latitude=3.14,
                 longitude=101.69, altitude=10668.0, velocity=250.0,
                 heading=45.0, vertical_rate=0.0, origin_country="Germany",
                 alert_level="GREEN", source="LIVE")
    """
    try:
        # ── Safety check: ensure array has enough elements ───
        if not isinstance(state_vector, list) or len(state_vector) < 17:
            return None

        # ── Extract latitude and longitude (REQUIRED) ────────
        # Index 5 = longitude, Index 6 = latitude
        # If either is null, we cannot plot this aircraft — skip it
        longitude = state_vector[5]
        latitude = state_vector[6]

        if longitude is None or latitude is None:
            return None

        # ── Skip aircraft on the ground ──────────────────────
        # Index 8 = on_ground (boolean)
        # Grounded aircraft are not relevant for air collision detection
        on_ground = state_vector[8]
        if on_ground is True:
            return None

        # ── Extract all other fields with safe defaults ──────
        # Each field uses `or default` to handle None values
        icao24 = state_vector[0] or "unknown"
        callsign = (state_vector[1] or "").strip()  # OpenSky pads with spaces
        origin_country = state_vector[2] or ""
        altitude = state_vector[7] or 0.0        # Baro altitude in meters
        velocity = state_vector[9] or 0.0        # Ground speed in m/s
        heading = state_vector[10] or 0.0         # True track in degrees
        vertical_rate = state_vector[11] or 0.0   # Climb/descent in m/s

        # ── Create and return the Aircraft object ────────────
        return Aircraft(
            icao24=str(icao24),
            callsign=str(callsign),
            latitude=float(latitude),
            longitude=float(longitude),
            altitude=float(altitude),
            velocity=float(velocity),
            heading=float(heading),
            vertical_rate=float(vertical_rate),
            origin_country=str(origin_country),
            alert_level="GREEN",           # Default — collision.py sets this later
            source="LIVE",                 # Marks this as real API data
            # last_updated is auto-set by the dataclass default factory
        )

    except (IndexError, TypeError, ValueError) as e:
        # If any field conversion fails, skip this aircraft
        print(f"[OpenSky] Failed to normalize state vector: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
# DEMO DATA FALLBACK
# ═══════════════════════════════════════════════════════════════

def load_demo_data() -> list[Aircraft]:
    """
    Loads pre-recorded aircraft data from demo_data.json.

    This is the OFFLINE FALLBACK for when:
      - OpenSky API is unreachable (no internet)
      - You're presenting a demo and can't rely on live data
      - You're developing/testing without making real API calls
      - OpenSky rate-limits you during development

    The demo_data.json file contains a snapshot of real OpenSky data
    captured and saved to disk. The format is a JSON array of objects
    matching the Aircraft.to_dict() output format.

    Returns:
        List of Aircraft objects loaded from the file.
        Empty list if the file doesn't exist or is malformed.
    """
    try:
        if not os.path.exists(DEMO_DATA_PATH):
            print(f"[OpenSky] Demo data file not found: {DEMO_DATA_PATH}")
            print("[OpenSky] Generate it by running: python -c \"from app.services.opensky_service import save_demo_data; save_demo_data()\"")
            return []

        with open(DEMO_DATA_PATH, "r", encoding="utf-8") as f:
            raw_list = json.load(f)

        aircraft_list: list[Aircraft] = []
        now = datetime.now(timezone.utc).isoformat()

        for entry in raw_list:
            aircraft = Aircraft(
                icao24=entry.get("icao24", "unknown"),
                callsign=entry.get("callsign", ""),
                latitude=entry.get("latitude", 0.0),
                longitude=entry.get("longitude", 0.0),
                altitude=entry.get("altitude", 0.0),
                velocity=entry.get("velocity", 0.0),
                heading=entry.get("heading", 0.0),
                vertical_rate=entry.get("vertical_rate", 0.0),
                origin_country=entry.get("origin_country", ""),
                alert_level="GREEN",
                source="DEMO",
                last_updated=now,  # Refresh timestamp so they don't appear stale
            )
            aircraft_list.append(aircraft)

        print(f"[OpenSky] Loaded {len(aircraft_list)} aircraft from demo data")
        return aircraft_list

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"[OpenSky] Failed to load demo data: {e}")
        return []

    except Exception as e:
        print(f"[OpenSky] Unexpected error loading demo data: {type(e).__name__}: {e}")
        return []


def save_demo_data(bounding_box: Optional[dict] = None) -> bool:
    """
    Fetches live aircraft data and saves it to demo_data.json.

    Run this ONCE to capture a snapshot for offline use:
        cd backend
        python -c "from app.services.opensky_service import save_demo_data; save_demo_data()"

    The saved file can then be loaded by load_demo_data() anytime
    the live API is unavailable.

    Args:
        bounding_box: Geographic region to fetch. Defaults to Pakistan.

    Returns:
        True if data was saved successfully, False otherwise.
    """
    aircraft_list = fetch_aircraft(bounding_box)

    if not aircraft_list:
        print("[OpenSky] No aircraft fetched. Cannot save demo data.")
        print("[OpenSky] Make sure you have internet and the API is responding.")
        return False

    # Convert to list of dicts for JSON serialization
    data = [a.to_dict() for a in aircraft_list]

    try:
        with open(DEMO_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"[OpenSky] Saved {len(data)} aircraft to {DEMO_DATA_PATH}")
        return True

    except Exception as e:
        print(f"[OpenSky] Failed to save demo data: {e}")
        return False
