# System Architecture

The ATC Monitoring System uses a decoupled, thread-safe architecture designed for high performance, realtime visualization, and guaranteed stability.

## 1. System Overview
The system is divided into two primary tiers:
- **Backend (Flask + Python):** Responsible for data ingestion, physics simulation, collision detection, and realtime broadcasting.
- **Frontend (React + Leaflet):** Responsible for high-performance interactive geographic visualization and HUD (Heads Up Display) components.

## 2. Backend Threading Model
The backend runs four distinct concurrent processes, synchronized via a single Thread-Safe Store (`AircraftStore`).

1. **Flask/SocketIO Main Thread:** Handles incoming HTTP REST requests and manages WebSocket connections.
2. **OpenSky Poller Thread (External IO):** Wakes up every 15 seconds to fetch live JSON from the OpenSky Network REST API. Parses the data and updates the Store.
3. **Simulation Engine Thread (Physics):** Wakes up every 1.0 second. Reads all aircraft from the store, applies heading and velocity math to move them forward in time, and writes new positions back to the store. This prevents "jumping" between API polls.
4. **Broadcaster Engine Thread (Orchestrator):** Wakes up every 1.0 second. Reads the final position state from the store, runs the collision detection algorithm, writes alerts to the store, and broadcasts the final payload to all WebSocket clients.

### The Thread-Safe Store (`AircraftStore`)
Because four threads are reading and writing simultaneously, Python's GIL is insufficient to prevent race conditions. The `AircraftStore` uses `threading.Lock` internally. Any thread interacting with the store acquires the lock, ensuring isolated atomic reads/writes.

## 3. Collision Detection Math
The collision detector evaluates every unique pair of aircraft using an `O(n^2)` algorithm. 

To determine distance accurately across the curvature of the Earth, we implement the **Haversine Formula**:
- $a = \sin^2(\Delta \text{lat}/2) + \cos(\text{lat}_1) \cdot \cos(\text{lat}_2) \cdot \sin^2(\Delta \text{lon}/2)$
- $c = 2 \cdot \text{atan2}(\sqrt{a}, \sqrt{1-a})$
- $d = R \cdot c$ (where R = 6371 km)

**Thresholds:**
- `< 5 km` = RED (Imminent Danger)
- `5 km - 10 km` = YELLOW (Warning)
- `> 10 km` = GREEN (Safe)

## 4. Frontend Rendering Pipeline (React-Leaflet)
The frontend utilizes a modern web mapping paradigm (React-Leaflet) integrated with dynamic Heads-Up Display (HUD) overlays.

1. **State Ingestion:** `useSocket.js` receives WebSocket payloads and updates the React Context (`AircraftContext`).
2. **React Boundary:** Components like `StatusBar`, `AircraftList`, and the `AnalyticsModal` re-render dynamically using the Context.
3. **Geographic Mapping (`MapDisplay`):** The system completely avoids abstract plotting by utilizing OpenStreetMap tiles. Aircraft are rendered as individual SVG markers that automatically rotate to match their true geographic heading.
4. **Interactive Target Lock & HUD:** Clicking an aircraft on the map engages a "Target Lock", drawing a 3-minute predictive trajectory and opening a detailed telemetry card on the side panel. Collision alerts trigger floating, localized UI popups directly over the map for immediate operator visibility.

## 5. Graceful Degradation & Demo Mode
If the OpenSky Network API goes offline, the backend degrades gracefully:
1. It ceases API polling.
2. The Simulation Engine takes complete control, extrapolating future positions indefinitely based on the last known velocity and heading.
3. If no data was loaded at startup, it injects synthetic simulated aircraft or loads a prerecorded `demo_data.json`.
4. The system **never crashes**.
