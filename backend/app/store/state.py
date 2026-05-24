# ============================================================
# app/store/state.py -- Thread-Safe In-Memory State Store
# ============================================================
#
# PURPOSE:
#   This module is the SINGLE SOURCE OF TRUTH for the entire system.
#   All aircraft positions and collision alerts live here.
#   Every other module reads from or writes to this store.
#
# WHY CENTRALIZED STATE?
#   Multiple threads run concurrently in this system:
#     - OpenSky polling thread (writes new aircraft data every 15s)
#     - Simulation thread (updates positions every 1s)
#     - Collision detection (reads all aircraft, writes alerts)
#     - Broadcaster thread (reads everything, emits via SocketIO)
#     - Flask request handlers (reads for REST API responses)
#
#   If each module kept its own copy of aircraft data, they would
#   quickly go out of sync. A single store ensures consistency.
#
# WHY THREADING.LOCK?
#   Python's GIL (Global Interpreter Lock) does NOT protect against
#   all race conditions. Consider this scenario WITHOUT a lock:
#
#     Thread A (simulation):  reads aircraft dict, starts updating positions
#     Thread B (broadcaster): reads aircraft dict at the same moment
#     Thread A:               modifies an aircraft's latitude mid-read
#     Thread B:               sends half-updated data to frontend
#
#   A threading.Lock ensures that only ONE thread can read or write
#   the state at any given time. Other threads wait until the lock
#   is released. This guarantees data consistency.
#
#   We use a context manager pattern (with self._lock:) so the lock
#   is ALWAYS released, even if an exception occurs inside the block.
#
# HOW OTHER MODULES INTERACT WITH THIS STORE:
#
#   opensky_service.py  --> calls store.update_aircraft(aircraft_list)
#                           to push fresh data from the API
#
#   simulation.py       --> calls store.get_all_aircraft() to read positions,
#                           mutates them, then calls store.update_aircraft()
#                           to write back updated positions
#
#   collision.py        --> calls store.get_all_aircraft() to compute
#                           pairwise distances, then calls
#                           store.update_alerts(alert_list) to save results
#
#   broadcaster.py      --> calls store.get_all_aircraft() and
#                           store.get_alerts() to build the SocketIO payload
#
#   routes.py           --> calls store.get_all_aircraft() and
#                           store.get_alerts() for REST API responses
#
# SNAPSHOT SAFETY:
#   get_all_aircraft() returns a LIST COPY of the aircraft values.
#   get_alerts() returns a LIST COPY of the alerts.
#   This means the caller gets a frozen-in-time snapshot that won't
#   change even if another thread modifies the store immediately after.
#   Without copies, a thread could iterate over the dict while another
#   thread adds/removes entries, causing a RuntimeError.
#
# ============================================================

import threading
from datetime import datetime, timezone
from typing import Optional

from app.models.aircraft import Aircraft, CollisionAlert


class AircraftStore:
    """
    Thread-safe in-memory store for aircraft state and collision alerts.

    This is a singleton-style class -- only one instance should exist.
    It is created in this module and imported by other modules as:
        from app.store.state import store
    """

    def __init__(self):
        # ── The Lock ─────────────────────────────────────────
        # All reads and writes to _aircraft and _alerts MUST
        # acquire this lock first. No exceptions.
        self._lock: threading.Lock = threading.Lock()

        # ── Aircraft Storage ─────────────────────────────────
        # Key:   icao24 (str) -- unique aircraft identifier
        # Value: Aircraft dataclass instance
        # Why dict? O(1) lookup by icao24, O(1) insert/delete.
        self._aircraft: dict[str, Aircraft] = {}

        # ── Alert Storage ────────────────────────────────────
        # List of active CollisionAlert objects.
        # Replaced entirely on each collision detection cycle
        # (not appended to -- we always want the current state).
        self._alerts: list[CollisionAlert] = []

        print("[Store] AircraftStore initialized (empty)")

    # ═══════════════════════════════════════════════════════════
    #  AIRCRAFT METHODS
    # ═══════════════════════════════════════════════════════════

    def update_aircraft(self, aircraft_list: list[Aircraft]) -> int:
        """
        Adds or updates multiple aircraft in the store.

        For each aircraft in the list:
          - If its icao24 already exists: REPLACE the stored object
          - If its icao24 is new: ADD it to the store

        This is called by:
          - opensky_service.py after fetching fresh API data
          - simulation.py after updating positions

        Args:
            aircraft_list: List of Aircraft objects to upsert.

        Returns:
            Total number of aircraft in the store after update.
        """
        with self._lock:
            for aircraft in aircraft_list:
                self._aircraft[aircraft.icao24] = aircraft

            count = len(self._aircraft)

        print(f"[Store] Updated {len(aircraft_list)} aircraft (total: {count})")
        return count

    def get_all_aircraft(self) -> list[Aircraft]:
        """
        Returns a SNAPSHOT (copy) of all aircraft currently in the store.

        Why a copy?
          If we returned self._aircraft.values() directly, the caller
          would hold a reference to the live dict. If another thread
          modifies the dict while the caller is iterating, Python raises:
              RuntimeError: dictionary changed size during iteration

          By returning list(...), we create an independent copy that is
          safe to iterate, serialize, or hold onto indefinitely.

        Called by:
          - collision.py  (to compute distances between all pairs)
          - broadcaster.py (to build the SocketIO payload)
          - routes.py (for GET /api/aircraft)

        Returns:
            List of all Aircraft objects (snapshot, safe to iterate).
        """
        with self._lock:
            return list(self._aircraft.values())

    def get_aircraft(self, icao24: str) -> Optional[Aircraft]:
        """
        Returns a single aircraft by its ICAO24 address.

        Args:
            icao24: The unique hex identifier to look up.

        Returns:
            The Aircraft object if found, or None if not tracked.
        """
        with self._lock:
            return self._aircraft.get(icao24, None)

    def remove_aircraft(self, icao24: str) -> bool:
        """
        Removes a single aircraft from the store.

        Called when:
          - An aircraft leaves the monitored bounding box
          - An aircraft hasn't been updated for too long (stale)
          - Manual removal via API (future feature)

        Args:
            icao24: The unique hex identifier to remove.

        Returns:
            True if the aircraft was found and removed, False if not found.
        """
        with self._lock:
            if icao24 in self._aircraft:
                del self._aircraft[icao24]
                print(f"[Store] Removed aircraft {icao24}")
                return True
            return False

    def aircraft_count(self) -> int:
        """
        Returns the number of aircraft currently being tracked.

        Called by:
          - routes.py for GET /api/status (aircraft_count field)
          - StatusBar component on the frontend (via status endpoint)

        Returns:
            Integer count of tracked aircraft.
        """
        with self._lock:
            return len(self._aircraft)

    def remove_stale_aircraft(self, max_age_seconds: float = 60.0) -> int:
        """
        Removes aircraft that haven't been updated within max_age_seconds.

        This prevents "ghost" aircraft from lingering on the radar after
        they've left the airspace or the API stops reporting them.

        How it works:
          1. Gets the current UTC time
          2. For each aircraft, parses its last_updated timestamp
          3. If (now - last_updated) > max_age_seconds, removes it
          4. Returns the count of removed aircraft

        Called by:
          - broadcaster.py on each broadcast cycle (housekeeping)

        Args:
            max_age_seconds: Maximum age in seconds before removal.
                             Default 60s = aircraft must update within 1 minute.

        Returns:
            Number of stale aircraft that were removed.
        """
        now = datetime.now(timezone.utc)
        stale_icaos: list[str] = []

        with self._lock:
            for icao24, aircraft in self._aircraft.items():
                try:
                    # Parse the ISO 8601 timestamp string back to datetime
                    last_update = datetime.fromisoformat(aircraft.last_updated)
                    age_seconds = (now - last_update).total_seconds()

                    if age_seconds > max_age_seconds:
                        stale_icaos.append(icao24)
                except (ValueError, TypeError):
                    # If timestamp is malformed, consider it stale
                    stale_icaos.append(icao24)

            # Remove stale aircraft (done inside the lock to prevent races)
            for icao24 in stale_icaos:
                del self._aircraft[icao24]

        if stale_icaos:
            print(f"[Store] Removed {len(stale_icaos)} stale aircraft: {stale_icaos}")

        return len(stale_icaos)

    # ═══════════════════════════════════════════════════════════
    #  ALERT METHODS
    # ═══════════════════════════════════════════════════════════

    def update_alerts(self, alerts: list[CollisionAlert]) -> int:
        """
        REPLACES the entire alert list with a new set of alerts.

        Why replace instead of append?
          Alerts are recomputed from scratch on every collision detection
          cycle. Old alerts are no longer valid because aircraft have moved.
          We always want the alerts to reflect the CURRENT state.

        Called by:
          - collision.py after running pairwise distance checks.

        Args:
            alerts: The complete list of active CollisionAlerts.

        Returns:
            Number of active alerts.
        """
        with self._lock:
            self._alerts = list(alerts)  # Store a copy, not a reference
            count = len(self._alerts)

        if count > 0:
            red_count = sum(1 for a in alerts if a.level == "RED")
            yellow_count = sum(1 for a in alerts if a.level == "YELLOW")
            print(f"[Store] Alerts updated: {count} total ({red_count} RED, {yellow_count} YELLOW)")

        return count

    def get_alerts(self) -> list[CollisionAlert]:
        """
        Returns a SNAPSHOT (copy) of all active collision alerts.

        Why a copy? Same reason as get_all_aircraft() -- prevents
        RuntimeError if another thread replaces the list mid-iteration.

        Called by:
          - broadcaster.py (to emit alert_update events)
          - routes.py (for GET /api/alerts)

        Returns:
            List of active CollisionAlert objects (snapshot).
        """
        with self._lock:
            return list(self._alerts)

    def clear_alerts(self) -> None:
        """
        Removes all active alerts.

        Called when:
          - Simulation is stopped (no more movement = no more risks)
          - System reset

        """
        with self._lock:
            self._alerts.clear()
            print("[Store] All alerts cleared")

    # ═══════════════════════════════════════════════════════════
    #  UTILITY METHODS
    # ═══════════════════════════════════════════════════════════

    def get_summary(self) -> dict:
        """
        Returns a summary of the current store state.

        Used by GET /api/status to include live stats in the response.

        Returns:
            Dict with aircraft_count, alert_count, red_alerts, yellow_alerts.
        """
        with self._lock:
            aircraft_count = len(self._aircraft)
            alert_count = len(self._alerts)
            red_count = sum(1 for a in self._alerts if a.level == "RED")
            yellow_count = sum(1 for a in self._alerts if a.level == "YELLOW")

        return {
            "aircraft_count": aircraft_count,
            "alert_count": alert_count,
            "red_alerts": red_count,
            "yellow_alerts": yellow_count,
        }

    def clear_all(self) -> None:
        """
        Resets the entire store to empty.
        Used for testing and system reset.
        """
        with self._lock:
            self._aircraft.clear()
            self._alerts.clear()
            print("[Store] Complete store reset")


# ═══════════════════════════════════════════════════════════════
# MODULE-LEVEL SINGLETON
# ═══════════════════════════════════════════════════════════════
#
# WHY A SINGLETON?
#   Every module in the system must read/write to the SAME store.
#   If opensky_service creates its own AircraftStore and collision.py
#   creates another, they would have completely separate data.
#
#   By creating one instance here at module level, every import gets
#   the same object:
#       from app.store.state import store
#       store.update_aircraft(...)  # Same store everywhere
#
#   This is the simplest singleton pattern in Python -- just create
#   the instance in the module. No metaclass magic needed.
# ═══════════════════════════════════════════════════════════════

store = AircraftStore()
