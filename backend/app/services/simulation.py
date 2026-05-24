# ============================================================
# app/services/simulation.py -- Aircraft Movement Simulation
# ============================================================
#
# PURPOSE:
#   Smoothly moves aircraft between OpenSky API polls so the radar
#   doesn't show static dots that jump every 15 seconds.
#
#   This module also generates synthetic (fake) aircraft when the
#   OpenSky API is unavailable, so the system always has something
#   to display and the demo never shows a blank radar.
#
# WHY IS SIMULATION NEEDED?
#   The OpenSky API is polled every 15 seconds (rate limit).
#   But a real radar updates continuously. If we only displayed
#   positions at poll time, the user would see:
#
#     t=0s   Aircraft at lat=30.00  (API poll)
#     t=1s   Aircraft at lat=30.00  (no change -- looks frozen)
#     t=2s   Aircraft at lat=30.00  (still frozen)
#     ...
#     t=15s  Aircraft at lat=30.05  (API poll -- jumps suddenly)
#
#   The simulation engine fills in the gaps:
#
#     t=0s   Aircraft at lat=30.000  (API poll -- real position)
#     t=1s   Aircraft at lat=30.003  (simulated movement)
#     t=2s   Aircraft at lat=30.007  (simulated movement)
#     ...
#     t=15s  Aircraft at lat=30.050  (API poll -- corrects to real)
#
#   This creates smooth, continuous radar animation.
#
# MOVEMENT MATH EXPLAINED:
#   Each aircraft has:
#     - velocity (m/s): how fast it's moving over the ground
#     - heading (degrees): compass direction (0=N, 90=E, 180=S, 270=W)
#     - vertical_rate (m/s): climbing or descending
#
#   Every tick (1 second), we compute:
#     distance = velocity * time_delta  (meters traveled in 1 second)
#
#   Then we decompose into north/south and east/west components:
#     north_meters = distance * cos(heading)
#     east_meters  = distance * sin(heading)
#
#   Convert meters to degrees:
#     1 degree latitude  = ~111,320 meters (constant everywhere)
#     1 degree longitude = ~111,320 * cos(latitude) meters (varies by latitude)
#
#   New position:
#     latitude  += north_meters / 111320
#     longitude += east_meters  / (111320 * cos(latitude))
#     altitude  += vertical_rate * time_delta
#
# THREADING DECISION — ONE THREAD vs ONE-PER-AIRCRAFT:
#   Option A: One thread per aircraft (BAD for this project)
#     - 55 aircraft = 55 threads
#     - Thread creation/destruction overhead on every API poll
#     - Race conditions between threads accessing the same store
#     - Hard to debug, hard to stop cleanly
#     - Excessive for a semester project
#
#   Option B: One simulation thread (GOOD — our approach)
#     - Single thread loops through ALL aircraft every tick
#     - 55 aircraft * simple math = microseconds per tick
#     - Clean start/stop lifecycle
#     - One lock acquisition per tick (not per aircraft)
#     - Easy to reason about, easy to debug
#
# HOW IT CONNECTS:
#   - broadcaster.py (Phase 8) calls engine.start() on app startup
#   - broadcaster.py calls engine.stop() on app shutdown
#   - The sim thread reads/writes to store (from app.store.state)
#   - collision.py (Phase 6) reads the updated positions from store
#   - The frontend sees smooth movement via SocketIO broadcasts
#
# ARCHITECTURE BOUNDARY:
#   - NO Flask imports
#   - NO SocketIO imports
#   - Only talks to the store (app.store.state)
#   - Independently testable without running the web server
# ============================================================

import math
import random
import string
import threading
import time
from datetime import datetime, timezone

from app.models.aircraft import Aircraft
from app.store.state import store


# ═══════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════

# Earth's radius approximation for degree-to-meter conversion
# 1 degree of latitude = ~111,320 meters everywhere on Earth
METERS_PER_DEGREE_LAT: float = 111_320.0

# Simulation tick interval in seconds
# Lower = smoother movement but more CPU usage
# 1 second is a good balance for a university project
TICK_INTERVAL: float = 1.0

# Default number of synthetic aircraft to generate
DEFAULT_SYNTHETIC_COUNT: int = 12

# Default bounding box for synthetic aircraft generation (Pakistan)
SYNTHETIC_BOUNDS: dict = {
    "lat_min": 24.0,
    "lat_max": 36.0,
    "lon_min": 61.0,
    "lon_max": 76.0,
}

# Realistic ranges for synthetic aircraft properties
SYNTHETIC_ALTITUDE_MIN: float = 5000.0    # 5,000 meters (~16,400 feet)
SYNTHETIC_ALTITUDE_MAX: float = 12000.0   # 12,000 meters (~39,400 feet)
SYNTHETIC_VELOCITY_MIN: float = 150.0     # 150 m/s (~291 knots)
SYNTHETIC_VELOCITY_MAX: float = 280.0     # 280 m/s (~544 knots)


# ═══════════════════════════════════════════════════════════════
# MOVEMENT CALCULATION
# ═══════════════════════════════════════════════════════════════

def calculate_new_position(
    latitude: float,
    longitude: float,
    altitude: float,
    velocity: float,
    heading: float,
    vertical_rate: float,
    time_delta: float
) -> tuple[float, float, float]:
    """
    Calculates a new position given current position, movement vector,
    and time elapsed.

    This is the core physics of the simulation. It uses basic trigonometry
    to decompose the aircraft's velocity vector into north/south and
    east/west components, then converts meters to degrees.

    Math breakdown:
      1. heading is in degrees clockwise from North
         - cos(heading) gives the northward component
         - sin(heading) gives the eastward component

      2. distance = velocity * time_delta (meters traveled)

      3. Latitude change = northward_distance / meters_per_degree_lat
         - This is ~constant everywhere on Earth (~111,320 m/degree)

      4. Longitude change = eastward_distance / meters_per_degree_lon
         - This VARIES by latitude because meridians converge at the poles
         - meters_per_degree_lon = 111,320 * cos(latitude)
         - At the equator: 111,320 m/degree
         - At 30 deg N: ~96,400 m/degree
         - At 60 deg N: ~55,660 m/degree

      5. Altitude change = vertical_rate * time_delta

    Args:
        latitude:      Current latitude in decimal degrees
        longitude:     Current longitude in decimal degrees
        altitude:      Current altitude in meters
        velocity:      Ground speed in meters per second
        heading:        True track in degrees (0=N, 90=E, 180=S, 270=W)
        vertical_rate: Climb/descent rate in meters per second
        time_delta:    Time elapsed in seconds since last update

    Returns:
        Tuple of (new_latitude, new_longitude, new_altitude)
        with geographic clamping applied.
    """
    # Convert heading from degrees to radians for math functions
    heading_rad = math.radians(heading)

    # Total distance traveled in meters
    distance_meters = velocity * time_delta

    # Decompose into north/south and east/west components
    # cos(0°) = 1.0 → heading North moves fully in latitude
    # sin(90°) = 1.0 → heading East moves fully in longitude
    north_meters = distance_meters * math.cos(heading_rad)
    east_meters = distance_meters * math.sin(heading_rad)

    # Convert meters to degree changes
    delta_lat = north_meters / METERS_PER_DEGREE_LAT

    # Longitude degrees per meter varies by latitude
    # Avoid division by zero at the poles (cos(90°) = 0)
    cos_lat = math.cos(math.radians(latitude))
    if cos_lat < 0.0001:
        cos_lat = 0.0001  # Safety floor near poles

    meters_per_degree_lon = METERS_PER_DEGREE_LAT * cos_lat
    delta_lon = east_meters / meters_per_degree_lon

    # Apply position changes
    new_lat = latitude + delta_lat
    new_lon = longitude + delta_lon
    new_alt = altitude + (vertical_rate * time_delta)

    # ── Geographic Safety Clamping ───────────────────────────
    # Latitude: clamp to [-90, 90] (can't go past the poles)
    new_lat = max(-90.0, min(90.0, new_lat))

    # Longitude: wrap around [-180, 180] (crossing date line)
    if new_lon > 180.0:
        new_lon -= 360.0
    elif new_lon < -180.0:
        new_lon += 360.0

    # Altitude: floor at 0 (can't go underground)
    new_alt = max(0.0, new_alt)

    return new_lat, new_lon, new_alt


# ═══════════════════════════════════════════════════════════════
# SYNTHETIC AIRCRAFT GENERATION
# ═══════════════════════════════════════════════════════════════

def generate_synthetic_aircraft(
    count: int = DEFAULT_SYNTHETIC_COUNT,
    bounds: dict = None
) -> list[Aircraft]:
    """
    Creates synthetic (fake) aircraft for simulation purposes.
    """
    if bounds is None:
        bounds = SYNTHETIC_BOUNDS

    aircraft_list: list[Aircraft] = []

    for i in range(count):
        # Generate unique identifier with SIM- prefix for easy identification
        hex_suffix = ''.join(random.choices(string.hexdigits[:16], k=6))
        icao24 = f"SIM-{hex_suffix}"

        # Generate airline-style callsign: 3-letter code + 4 digits
        callsign_prefix = random.choice(["PIA", "SRN", "AXN", "BJA", "QTA"])
        callsign_number = random.randint(100, 999)
        callsign = f"{callsign_prefix}{callsign_number}"

        # Random position within the bounding box
        latitude = random.uniform(bounds["lat_min"], bounds["lat_max"])
        longitude = random.uniform(bounds["lon_min"], bounds["lon_max"])

        # Realistic flight parameters
        altitude = random.uniform(SYNTHETIC_ALTITUDE_MIN, SYNTHETIC_ALTITUDE_MAX)
        velocity = random.uniform(SYNTHETIC_VELOCITY_MIN, SYNTHETIC_VELOCITY_MAX)
        heading = random.uniform(0.0, 360.0)
        vertical_rate = random.uniform(-2.0, 2.0)  # Slight climb/descent

        aircraft = Aircraft(
            icao24=icao24,
            callsign=callsign,
            latitude=round(latitude, 4),
            longitude=round(longitude, 4),
            altitude=round(altitude, 1),
            velocity=round(velocity, 1),
            heading=round(heading, 1),
            vertical_rate=round(vertical_rate, 2),
            origin_country="Pakistan",
            alert_level="GREEN",
            source="SIMULATED",
        )
        aircraft_list.append(aircraft)

    print(f"[Simulation] Generated {count} synthetic aircraft")
    return aircraft_list


# ═══════════════════════════════════════════════════════════════
# SIMULATION ENGINE CLASS
# ═══════════════════════════════════════════════════════════════

class SimulationEngine:
    """
    Background simulation engine that continuously updates aircraft positions.

    Lifecycle:
      1. engine = SimulationEngine()   # Create (does nothing yet)
      2. engine.start()                # Spawns background thread
      3. ... system runs ...           # Thread ticks every 1 second
      4. engine.stop()                 # Signals thread to exit cleanly

    The simulation thread:
      1. Reads all aircraft from the store
      2. For each aircraft, computes new position using velocity + heading
      3. Writes updated aircraft back to the store
      4. Sleeps for TICK_INTERVAL seconds
      5. Repeats until stop() is called

    Thread safety:
      - All store reads/writes go through AircraftStore methods
        which use threading.Lock internally
      - This thread never accesses raw dicts directly
    """

    def __init__(self):
        # The background thread reference (None when not running)
        self._thread: threading.Thread = None

        # Flag to signal the thread to stop gracefully
        # threading.Event is thread-safe — can be set/checked from any thread
        self._stop_event: threading.Event = threading.Event()

        # Track the last tick time for accurate time-delta calculations
        self._last_tick: float = 0.0

        print("[Simulation] Engine initialized (idle)")

    def start(self) -> None:
        """
        Starts the background simulation thread.

        If the engine is already running, this does nothing (safe to call twice).
        The thread is marked as daemon=True, meaning it will be killed
        automatically when the main process exits — no zombie threads.
        """
        if self.is_running():
            print("[Simulation] Engine already running — ignoring start()")
            return

        # Clear the stop flag (in case we're restarting after a stop)
        self._stop_event.clear()

        # Record the starting time
        self._last_tick = time.time()

        # Create and start the background thread
        self._thread = threading.Thread(
            target=self._simulation_loop,
            name="SimulationEngine",
            daemon=True  # Dies with the main process — no cleanup needed
        )
        self._thread.start()
        print("[Simulation] Engine STARTED (ticking every {:.1f}s)".format(TICK_INTERVAL))

    def stop(self) -> None:
        """
        Signals the simulation thread to stop and waits for it to finish.

        The thread checks self._stop_event on every tick. When it sees
        the event is set, it exits the loop cleanly. We then wait up to
        3 seconds for it to finish (join).

        After stopping, you can call start() again to restart.
        """
        if not self.is_running():
            print("[Simulation] Engine not running — ignoring stop()")
            return

        print("[Simulation] Stopping engine...")
        self._stop_event.set()  # Signal the thread to exit

        # Wait for the thread to finish (max 3 seconds)
        if self._thread is not None:
            self._thread.join(timeout=3.0)
            self._thread = None

        print("[Simulation] Engine STOPPED")

    def is_running(self) -> bool:
        """
        Returns True if the simulation thread is alive and running.

        Used by:
          - routes.py for GET /api/status (simulation_running field)
          - broadcaster.py to decide whether to start the engine
        """
        return self._thread is not None and self._thread.is_alive()

    # ── Private: The Simulation Loop ─────────────────────────

    def _simulation_loop(self) -> None:
        """
        The main loop that runs in the background thread.

        On each tick:
          1. Calculate time_delta since last tick
          2. Read all aircraft from the store (thread-safe snapshot)
          3. For each aircraft, compute new position
          4. Write all updated aircraft back to the store
          5. Sleep until next tick
          6. Check if stop was requested

        The time_delta approach (instead of assuming exactly 1.0s) handles
        the case where the tick takes slightly longer due to CPU load.
        This keeps movement speed consistent regardless of system performance.
        """
        print("[Simulation] Background thread started")

        while not self._stop_event.is_set():
            try:
                # ── Calculate time since last tick ───────────
                now = time.time()
                time_delta = now - self._last_tick
                self._last_tick = now

                # Cap time_delta to prevent huge jumps if the system
                # was paused (e.g., laptop sleep, debugger breakpoint)
                if time_delta > 5.0:
                    time_delta = TICK_INTERVAL  # Treat as a normal tick

                # ── Read all aircraft from the store ─────────
                all_aircraft = store.get_all_aircraft()

                if not all_aircraft:
                    # No aircraft in the store — nothing to simulate
                    self._stop_event.wait(timeout=TICK_INTERVAL)
                    continue

                # ── Update each aircraft's position ──────────
                for aircraft in all_aircraft:
                    # Skip aircraft with zero velocity (parked/stationary)
                    if aircraft.velocity < 0.1:
                        continue

                    # Calculate new position
                    new_lat, new_lon, new_alt = calculate_new_position(
                        latitude=aircraft.latitude,
                        longitude=aircraft.longitude,
                        altitude=aircraft.altitude,
                        velocity=aircraft.velocity,
                        heading=aircraft.heading,
                        vertical_rate=aircraft.vertical_rate,
                        time_delta=time_delta,
                    )

                    # Mutate the aircraft object in place
                    aircraft.latitude = round(new_lat, 6)
                    aircraft.longitude = round(new_lon, 6)
                    aircraft.altitude = round(new_alt, 1)

                    # Update the timestamp
                    aircraft.update_timestamp()

                # ── Write updated aircraft back to the store ─
                store.update_aircraft(all_aircraft)

            except Exception as e:
                # NEVER let the simulation thread crash
                # Log the error and continue on the next tick
                print(f"[Simulation] Tick error: {type(e).__name__}: {e}")

            # ── Sleep until next tick ────────────────────────
            # Using Event.wait() instead of time.sleep() so that
            # stop() can interrupt the sleep immediately
            self._stop_event.wait(timeout=TICK_INTERVAL)

        print("[Simulation] Background thread exiting")


# ═══════════════════════════════════════════════════════════════
# MODULE-LEVEL SINGLETON
# ═══════════════════════════════════════════════════════════════
#
# Same singleton pattern as store.py.
# Every module that needs the simulation engine imports:
#     from app.services.simulation import engine
#
# There should only be ONE simulation engine in the system.
# ═══════════════════════════════════════════════════════════════

engine = SimulationEngine()
