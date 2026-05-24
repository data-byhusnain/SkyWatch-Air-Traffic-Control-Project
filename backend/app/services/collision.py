# ============================================================
# app/services/collision.py -- Collision Detection Module
# ============================================================
#
# PURPOSE:
#   Computes pairwise geographic distances between ALL tracked aircraft
#   and assigns collision risk levels:
#     GREEN  = Safe       (distance >= 10 km)
#     YELLOW = Warning    (distance >= 5 km and < 10 km)
#     RED    = Danger     (distance < 5 km)
#
#   Generates CollisionAlert objects for every YELLOW and RED pair.
#   Updates each Aircraft's alert_level to reflect its worst-case risk.
#
# WHY HAVERSINE, NOT EUCLIDEAN?
#   Latitude and longitude are NOT a flat grid. They are angles on a
#   sphere. Using Euclidean distance (sqrt((x2-x1)^2 + (y2-y1)^2))
#   on lat/lon gives wrong results because:
#
#     1. One degree of longitude is ~111 km at the equator but only
#        ~55 km at 60 deg latitude (meridians converge at the poles).
#
#     2. Euclidean distance treats 1 degree lat = 1 degree lon,
#        which overestimates east-west distance at high latitudes.
#
#   The Haversine formula correctly accounts for Earth's curvature
#   and gives accurate distances in kilometers anywhere on the planet.
#
#   For aircraft 50-100 km apart, the error of Euclidean would be
#   significant enough to trigger false alerts or miss real ones.
#
# WHY O(n^2) COMPLEXITY IS ACCEPTABLE:
#   Checking every pair of N aircraft requires N*(N-1)/2 comparisons.
#   For typical numbers in this project:
#
#     N=10  aircraft -> 45 comparisons        (~instant)
#     N=50  aircraft -> 1,225 comparisons     (~instant)
#     N=100 aircraft -> 4,950 comparisons     (~1 ms)
#     N=500 aircraft -> 124,750 comparisons   (~50 ms)
#
#   Since we're monitoring one region with at most ~100 aircraft,
#   and this runs once per second, O(n^2) is perfectly fine.
#   Optimizations like spatial indexing (KD-trees, grid cells) would
#   be overkill for a semester project.
#
# PURE FUNCTION DESIGN:
#   This module has NO SIDE EFFECTS beyond mutating Aircraft objects
#   that are passed in. It does NOT:
#     - Import Flask or SocketIO
#     - Access the store directly
#     - Make network calls
#     - Write to disk
#
#   This means you can test it with plain Python — no server needed:
#     aircraft = [Aircraft(...), Aircraft(...)]
#     alerts = check_collisions(aircraft)
#
# HOW IT CONNECTS:
#   broadcaster.py (Phase 8) will call this every broadcast cycle:
#     all_aircraft = store.get_all_aircraft()
#     alerts = check_collisions(all_aircraft)
#     store.update_alerts(alerts)
#     store.update_aircraft(all_aircraft)  # alert_levels updated
#
#   The frontend uses aircraft.alert_level to color radar blips:
#     GREEN  -> white/green blip (normal)
#     YELLOW -> yellow blip + flashing
#     RED    -> red blip + urgent flashing + alert banner
# ============================================================

import math
from datetime import datetime, timezone

from app.models.aircraft import Aircraft, CollisionAlert


# ═══════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════

# Collision threshold distances in kilometers
# Aircraft closer than DANGER_KM are in immediate collision risk
DANGER_KM: float = 5.0

# Aircraft between DANGER_KM and WARNING_KM need attention
WARNING_KM: float = 10.0

# Earth's mean radius in kilometers (WGS-84 approximation)
# Used in the Haversine formula to convert angular distance to km
EARTH_RADIUS_KM: float = 6371.0


# ═══════════════════════════════════════════════════════════════
# HAVERSINE DISTANCE FUNCTION
# ═══════════════════════════════════════════════════════════════

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates the great-circle distance between two points on Earth
    using the Haversine formula.

    The Haversine formula:
      a = sin^2(dlat/2) + cos(lat1) * cos(lat2) * sin^2(dlon/2)
      c = 2 * arcsin(sqrt(a))
      distance = R * c

    Where:
      dlat = lat2 - lat1 (difference in latitude, in radians)
      dlon = lon2 - lon1 (difference in longitude, in radians)
      R    = Earth's radius (6371 km)

    Why "Haversine"?
      The name comes from "half versed sine": haversin(theta) = sin^2(theta/2).
      It's numerically stable for small distances (unlike the spherical
      law of cosines which loses precision for nearby points).

    Args:
        lat1: Latitude of point 1 in decimal degrees
        lon1: Longitude of point 1 in decimal degrees
        lat2: Latitude of point 2 in decimal degrees
        lon2: Longitude of point 2 in decimal degrees

    Returns:
        Distance in kilometers (float, always >= 0).

    Examples:
        # Islamabad to Lahore (~275 km)
        haversine_km(33.69, 73.04, 31.52, 74.35) -> ~276.5

        # Two aircraft 5 km apart (at equator)
        haversine_km(0.0, 0.0, 0.0449, 0.0) -> ~5.0
    """
    # Step 1: Convert all coordinates from degrees to radians
    # math.radians() multiplies by pi/180
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat_rad = math.radians(lat2 - lat1)
    dlon_rad = math.radians(lon2 - lon1)

    # Step 2: Apply the Haversine formula
    # a = sin^2(dlat/2) + cos(lat1) * cos(lat2) * sin^2(dlon/2)
    a = (
        math.sin(dlat_rad / 2.0) ** 2
        + math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(dlon_rad / 2.0) ** 2
    )

    # Step 3: c = 2 * arcsin(sqrt(a))
    # Clamp 'a' to [0, 1] to avoid domain errors from floating-point rounding
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.asin(math.sqrt(a))

    # Step 4: distance = R * c
    distance = EARTH_RADIUS_KM * c

    return distance


# ═══════════════════════════════════════════════════════════════
# ALERT LEVEL HELPERS
# ═══════════════════════════════════════════════════════════════

def reset_alert_levels(aircraft_list: list[Aircraft]) -> None:
    """
    Resets all aircraft alert levels to GREEN before a new detection cycle.

    This is called at the START of each check_collisions() run.
    Without this reset, an aircraft that was previously RED would stay RED
    even after the threat has passed (the other aircraft moved away).

    Args:
        aircraft_list: List of Aircraft objects to reset (mutated in place).
    """
    for aircraft in aircraft_list:
        aircraft.alert_level = "GREEN"


def apply_alert_level(aircraft: Aircraft, level: str) -> None:
    """
    Applies an alert level to an aircraft, respecting priority rules.

    Priority (highest to lowest): RED > YELLOW > GREEN

    Rules:
      - If aircraft is GREEN and gets YELLOW -> becomes YELLOW
      - If aircraft is GREEN and gets RED    -> becomes RED
      - If aircraft is YELLOW and gets RED   -> becomes RED (upgrade)
      - If aircraft is RED and gets YELLOW   -> stays RED (no downgrade)

    This matters because one aircraft can be in multiple alert pairs:
      Aircraft A is 4 km from B (RED) and 8 km from C (YELLOW).
      A should show RED (the worst case), not YELLOW.

    Args:
        aircraft: The Aircraft object to update (mutated in place).
        level: The alert level to apply ("RED" or "YELLOW").
    """
    # Define priority: higher number = more severe
    priority = {"GREEN": 0, "YELLOW": 1, "RED": 2}

    current_priority = priority.get(aircraft.alert_level, 0)
    new_priority = priority.get(level, 0)

    # Only upgrade, never downgrade
    if new_priority > current_priority:
        aircraft.alert_level = level


# ═══════════════════════════════════════════════════════════════
# MAIN COLLISION DETECTION FUNCTION
# ═══════════════════════════════════════════════════════════════

def check_collisions(aircraft_list: list[Aircraft]) -> list[CollisionAlert]:
    """
    Performs pairwise collision detection on all aircraft.

    Algorithm:
      1. Reset all aircraft to GREEN
      2. For each unique pair (i, j) where j > i:
         a. Compute Haversine distance
         b. If distance < DANGER_KM:  create RED alert
         c. If distance < WARNING_KM: create YELLOW alert
         d. Update both aircraft's alert_level (respecting priority)
      3. Return list of all YELLOW and RED alerts

    Why j > i (not j != i)?
      This ensures each pair is checked EXACTLY ONCE.
      Without this, we'd get duplicate alerts:
        A-B at 4 km (RED) AND B-A at 4 km (RED) — same alert twice.
      With j > i, we only check A-B once.

    Args:
        aircraft_list: List of all Aircraft objects currently tracked.
                       These objects are MUTATED (alert_level updated).

    Returns:
        List of CollisionAlert objects for YELLOW and RED pairs only.
        GREEN pairs do not generate alerts (they are safe).

    Example:
        aircraft = [
            Aircraft(icao24="A", latitude=30.0, longitude=70.0, ...),
            Aircraft(icao24="B", latitude=30.04, longitude=70.0, ...),  # ~4.4 km from A
            Aircraft(icao24="C", latitude=31.0, longitude=71.0, ...),   # ~140 km from A
        ]
        alerts = check_collisions(aircraft)
        # alerts = [CollisionAlert("A", "B", 4.45, "RED")]
        # aircraft[0].alert_level = "RED"
        # aircraft[1].alert_level = "RED"
        # aircraft[2].alert_level = "GREEN"
    """
    alerts: list[CollisionAlert] = []

    # ── Handle edge cases ────────────────────────────────────
    # 0 aircraft: nothing to compare
    # 1 aircraft: no pairs possible
    if len(aircraft_list) < 2:
        reset_alert_levels(aircraft_list)
        return alerts

    # ── Step 1: Reset all alert levels to GREEN ──────────────
    reset_alert_levels(aircraft_list)

    # ── Step 2: Check every unique pair ──────────────────────
    n = len(aircraft_list)

    for i in range(n):
        for j in range(i + 1, n):
            a1 = aircraft_list[i]
            a2 = aircraft_list[j]

            # Skip aircraft with invalid coordinates (0,0 is null island)
            if _has_invalid_coordinates(a1) or _has_invalid_coordinates(a2):
                continue

            # Compute distance using Haversine formula
            distance = haversine_km(
                a1.latitude, a1.longitude,
                a2.latitude, a2.longitude
            )
            distance = round(distance, 2)

            # ── Classify the distance ────────────────────────
            if distance < DANGER_KM:
                # RED ALERT — immediate collision risk
                level = "RED"
                print(
                    f"[COLLISION] RED alert: {a1.callsign or a1.icao24} vs "
                    f"{a2.callsign or a2.icao24} ({distance} km)"
                )

            elif distance < WARNING_KM:
                # YELLOW ALERT — aircraft are uncomfortably close
                level = "YELLOW"
                print(
                    f"[COLLISION] YELLOW alert: {a1.callsign or a1.icao24} vs "
                    f"{a2.callsign or a2.icao24} ({distance} km)"
                )

            else:
                # GREEN — safe distance, no alert needed
                continue

            # ── Create alert object ──────────────────────────
            alert = CollisionAlert(
                aircraft_1=a1.icao24,
                aircraft_2=a2.icao24,
                distance_km=distance,
                level=level,
                # timestamp auto-set by dataclass default factory
            )
            alerts.append(alert)

            # ── Update both aircraft's alert level ───────────
            # Uses priority system: RED > YELLOW > GREEN
            apply_alert_level(a1, level)
            apply_alert_level(a2, level)

    return alerts


# ═══════════════════════════════════════════════════════════════
# PRIVATE HELPERS
# ═══════════════════════════════════════════════════════════════

def _has_invalid_coordinates(aircraft: Aircraft) -> bool:
    """
    Checks if an aircraft has invalid or placeholder coordinates.

    Coordinates of exactly (0.0, 0.0) are "Null Island" in the Gulf
    of Guinea — no real aircraft should be reported there. This usually
    means the position data is missing or corrupted.

    Args:
        aircraft: Aircraft object to validate.

    Returns:
        True if coordinates are invalid/missing, False if valid.
    """
    # Null Island check (both lat AND lon are exactly 0)
    if aircraft.latitude == 0.0 and aircraft.longitude == 0.0:
        return True

    # NaN check (can happen with corrupted float conversions)
    if math.isnan(aircraft.latitude) or math.isnan(aircraft.longitude):
        return True

    return False
