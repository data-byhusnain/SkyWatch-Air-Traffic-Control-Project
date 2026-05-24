# ============================================================
# app/services/broadcaster.py -- Realtime Broadcast Orchestrator
# ============================================================
#
# PURPOSE:
#   This is the HEARTBEAT of the ATC system. Every 1 second, it:
#     1. Reads all aircraft from the centralized store
#     2. Runs collision detection on them
#     3. Stores the resulting alerts
#     4. Pushes aircraft + alerts + status to ALL connected clients
#     5. Cleans up stale aircraft that haven't been updated
#
#   It does NOT:
#     - Move aircraft (that's simulation.py's job)
#     - Fetch from OpenSky (that's opensky_service.py's job)
#     - Handle HTTP requests (that's routes.py's job)
#
# WHY IS BROADCASTER SEPARATE FROM SIMULATION?
#   Simulation and broadcasting have different concerns:
#
#   Simulation (simulation.py):
#     - Moves aircraft positions using velocity + heading math
#     - Runs in its own thread at its own tick rate
#     - Has no knowledge of SocketIO or clients
#     - Pure physics — no I/O, no networking
#
#   Broadcaster (this file):
#     - Reads the current state (whatever it is)
#     - Runs collision detection
#     - Pushes data to connected WebSocket clients
#     - Handles housekeeping (stale aircraft removal)
#     - Pure orchestration — no physics, no movement math
#
#   Separating them means:
#     - Simulation can run even with zero connected clients
#     - Broadcasting can work even if simulation is paused
#     - Each module can be tested independently
#     - Changing broadcast frequency doesn't affect simulation accuracy
#
# WHY FULL SNAPSHOTS (not diffs)?
#   On every broadcast, we send the COMPLETE list of aircraft, not
#   just the ones that changed. This is simpler and more reliable:
#
#   Diff approach (rejected):
#     - Client must track state and apply patches
#     - If client misses one update, state goes permanently wrong
#     - Reconnecting clients need special "full sync" logic
#     - More code, more bugs, more complexity
#
#   Snapshot approach (chosen):
#     - Client just replaces its entire aircraft list each time
#     - Missed updates don't matter — next snapshot corrects everything
#     - Reconnecting clients immediately get full state
#     - Dead simple to implement on both sides
#
#   At ~55 aircraft, each snapshot is ~5 KB of JSON — trivial for WebSockets.
#   Diffs only make sense at 10,000+ objects, which this project never hits.
#
# WHY 1-SECOND BROADCAST INTERVAL?
#   - Fast enough to feel "real-time" on the radar display
#   - Slow enough to not overwhelm the browser with repaints
#   - Matches the simulation tick rate (1 second)
#   - Keeps network traffic low (~5 KB/sec)
#   - Standard interval for ATC-style monitoring displays
#
# HOW THE STORE ACTS AS A SYNCHRONIZATION BOUNDARY:
#   Multiple threads run concurrently:
#     Thread 1 (simulation):   writes positions to store
#     Thread 2 (OpenSky poll): writes fresh API data to store
#     Thread 3 (broadcaster):  reads from store, writes alerts
#     Thread 4 (Flask):        reads from store for REST responses
#
#   The store's threading.Lock ensures no two threads read/write
#   at the same time. The broadcaster doesn't need to coordinate
#   directly with simulation or OpenSky — it just reads whatever
#   the store currently contains. This is the "shared memory" pattern
#   from distributed systems, applied at the thread level.
#
# HOW IT CONNECTS:
#   - app/__init__.py starts the broadcaster on app creation
#   - socketio.emit() pushes data to all connected React clients
#   - Frontend useSocket hook receives these events and updates context
#   - RadarDisplay, AircraftList, AlertBanner all re-render on new data
# ============================================================

from apscheduler.schedulers.background import BackgroundScheduler

from app.extensions import socketio
from app.services.collision import check_collisions
from app.services.simulation import engine as sim_engine
from app.store.state import store


# ═══════════════════════════════════════════════════════════════
# MODULE STATE
# ═══════════════════════════════════════════════════════════════

# APScheduler instance — runs broadcast_cycle() every 1 second
_scheduler: BackgroundScheduler = None

# Flag to prevent duplicate starts
_is_running: bool = False

# Counter for periodic stats logging (every 10 cycles = every 10 seconds)
_cycle_count: int = 0
_STATS_LOG_INTERVAL: int = 10  # Log system stats every N cycles


# ═══════════════════════════════════════════════════════════════
# BROADCAST CYCLE — THE HEARTBEAT
# ═══════════════════════════════════════════════════════════════

def broadcast_cycle() -> None:
    """
    Performs one complete broadcast cycle.

    This function is called by APScheduler every 1 second.
    It is the central coordination point of the backend.

    Steps:
      1. Read all aircraft from the store (thread-safe snapshot)
      2. Run collision detection (updates alert_level on each aircraft)
      3. Store the resulting alerts in the store
      4. Write back the aircraft (with updated alert_levels)
      5. Emit aircraft data to all connected WebSocket clients
      6. Emit alert data to all connected WebSocket clients
      7. Emit system status to all connected WebSocket clients
      8. Remove stale aircraft that haven't been updated in 60 seconds
      9. Log periodic system statistics (every 10 cycles)

    Error handling:
      The entire function is wrapped in try/except. If ANY step fails,
      the error is logged and the next cycle runs normally. The broadcaster
      NEVER crashes — it's the heartbeat and must keep beating.
    """
    global _cycle_count

    try:
        # ── Step 1: Read all aircraft from the store ─────────
        all_aircraft = store.get_all_aircraft()

        # ── Step 2: Run collision detection ──────────────────
        # This mutates each aircraft's alert_level in place
        # and returns a list of CollisionAlert objects
        alerts = check_collisions(all_aircraft)

        # ── Step 3: Store the alerts ─────────────────────────
        store.update_alerts(alerts)

        # ── Step 4: Write back aircraft with updated alert levels
        # The aircraft objects were mutated by check_collisions(),
        # so writing them back ensures the store has the latest levels
        if all_aircraft:
            store.update_aircraft(all_aircraft)

        # ── Step 5: Emit aircraft to all connected clients ───
        emit_aircraft(all_aircraft)

        # ── Step 6: Emit alerts to all connected clients ─────
        emit_alerts(alerts)

        # ── Step 7: Emit system status ───────────────────────
        emit_status(all_aircraft)

        # ── Step 8: Housekeeping — remove stale aircraft ─────
        # Aircraft not updated in 60 seconds are removed.
        # This prevents "ghost" aircraft from lingering after
        # they've left the airspace.
        store.remove_stale_aircraft(max_age_seconds=60.0)

        # ── Step 9: Periodic stats logging ───────────────────
        _cycle_count += 1
        if _cycle_count % _STATS_LOG_INTERVAL == 0:
            print("[Broadcaster] Emitted websocket update")
            _log_system_stats(all_aircraft, alerts)

    except Exception as e:
        # NEVER let the broadcaster crash — log and continue
        print(f"[Broadcaster] Cycle error: {type(e).__name__}: {e}")


# ═══════════════════════════════════════════════════════════════
# EMIT FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def emit_aircraft(aircraft_list: list) -> None:
    try:
        payload = {
            "aircraft": [ac.to_dict() for ac in aircraft_list]
        }
        socketio.emit("aircraft_update", payload)
    except Exception as e:
        print(f"[Broadcaster] Failed to emit aircraft: {e}")


def emit_alerts(alerts: list) -> None:
    try:
        payload = {
            "alerts": [alert.to_dict() for alert in alerts]
        }
        socketio.emit("alert_update", payload)
    except Exception as e:
        print(f"[Broadcaster] Failed to emit alerts: {e}")


def emit_status(aircraft_list: list) -> None:
    try:
        # Determine the primary data source
        source = _determine_source(aircraft_list)

        # Get alert count from the store
        alert_summary = store.get_summary()

        payload = {
            "running": sim_engine.is_running(),
            "source": source,
            "aircraft_count": len(aircraft_list),
            "alert_count": alert_summary["alert_count"],
            "red_alerts": alert_summary["red_alerts"],
            "yellow_alerts": alert_summary["yellow_alerts"],
        }
        socketio.emit("simulation_status", payload)
    except Exception as e:
        print(f"[Broadcaster] Failed to emit status: {e}")


# ═══════════════════════════════════════════════════════════════
# LIFECYCLE MANAGEMENT
# ═══════════════════════════════════════════════════════════════

def start_broadcaster(interval_seconds: float = 1.0) -> None:
    global _scheduler, _is_running

    if _is_running:
        print("[Broadcaster] Already running -- ignoring start()")
        return

    _scheduler = BackgroundScheduler(daemon=True)

    # Register the broadcast cycle as a recurring job
    _scheduler.add_job(
        func=broadcast_cycle,
        trigger="interval",
        seconds=interval_seconds,
        id="broadcast_cycle",
        name="ATC Broadcast Cycle",
        replace_existing=True,  # Prevents duplicate job errors on restart
    )

    _scheduler.start()
    _is_running = True

    print(f"[Broadcaster] Started (interval: {interval_seconds}s)")


def stop_broadcaster() -> None:
    global _scheduler, _is_running

    if not _is_running:
        print("[Broadcaster] Not running -- ignoring stop()")
        return

    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None

    _is_running = False
    print("[Broadcaster] Stopped")


def is_broadcaster_running() -> bool:
    """Returns True if the broadcaster scheduler is active."""
    return _is_running


# ═══════════════════════════════════════════════════════════════
# PRIVATE HELPERS
# ═══════════════════════════════════════════════════════════════

def _determine_source(aircraft_list: list) -> str:
    """
    Determines the primary data source based on current aircraft.
    """
    if not aircraft_list:
        return "NONE"

    sources = set(ac.source for ac in aircraft_list)

    if len(sources) == 1:
        return sources.pop()  # All same source
    else:
        return "MIXED"


def _log_system_stats(aircraft_list: list, alerts: list) -> None:
    live_count = sum(1 for ac in aircraft_list if ac.source == "LIVE")
    sim_count = sum(1 for ac in aircraft_list if ac.source == "SIMULATED")
    demo_count = sum(1 for ac in aircraft_list if ac.source == "DEMO")
    red_count = sum(1 for a in alerts if a.level == "RED")
    yellow_count = sum(1 for a in alerts if a.level == "YELLOW")

    print(
        f"[Broadcaster] System Summary | Aircraft: {len(aircraft_list)} "
        f"(LIVE={live_count} SIM={sim_count} DEMO={demo_count}) | "
        f"Alerts: {len(alerts)} (RED={red_count} YELLOW={yellow_count}) | "
        f"Simulation: {'ON' if sim_engine.is_running() else 'OFF'}"
    )
