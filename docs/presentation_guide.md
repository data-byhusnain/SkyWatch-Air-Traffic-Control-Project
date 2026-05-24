# ATC System - Presentation & Demo Guide

This document outlines the ideal setup and script for demonstrating the project during a final presentation or viva.

## 1. Screenshot Preparation

To capture the best screenshots for your project report or slides:

**Setup:**
- Start the backend in Demo Mode (`ATC_DEMO_MODE=true python run.py`) to ensure reliable data.
- Open the frontend in Chrome/Edge at `http://localhost:5173`.
- **Zoom Level:** Set browser zoom to 90% or 100% to ensure the Sidebar and Canvas fit comfortably.
- **Window Size:** Maximize the window.

- Wait until at least one RED alert banner/popup appears.
- Click on an aircraft to demonstrate the "Target Lock" trajectory and the side details card.
- Open the "ANALYTICS" modal and take a screenshot showcasing the system statistics.
- Highlight the `AircraftList` sidebar showing the full data table.

## 2. Live Demo Script (5 Minutes)

**Step 1: Introduction (1 min)**
- Start backend normally (no demo mode). Start frontend.
- "Welcome to the ATC Monitoring System. On the left is our real-world interactive map powered by OpenStreetMap, showing live flights over the region. On the right, our live telemetry feed."
- "The backend is currently polling the public OpenSky Network API to retrieve live flight data."

**Step 2: Realtime Movement & Target Lock (1 min)**
- Hover over an aircraft, then click it.
- "Because APIs have rate limits (15 seconds), we built an internal physics engine. It takes the velocity and heading of each plane and extrapolates its position. If you click a plane, you'll see a 'Target Lock' HUD appear with a 3-minute predicted trajectory calculated by our engine."

**Step 3: Collision Detection (1.5 min)**
- "Behind the scenes, a background thread runs an `O(n^2)` algorithm every 1 second, computing the exact geographic distance between all aircraft pairs using the Haversine formula."
- Wait for a RED or YELLOW alert (or use Demo Mode if live data is too sparse).
- "Notice the floating popup directly over the map and the connecting solid line between the planes. The system instantly detects they are under 5 kilometers apart and flags them as a priority."

**Step 4: Architecture Conclusion & Analytics (1.5 min)**
- Open the Analytics Modal from the top bar.
- "All of this data is synchronized via a thread-safe singleton store and pushed to the React frontend via WebSockets."
- "The system is built for resilience. If the OpenSky API fails, our physics engine takes full control and the system gracefully degrades into simulation mode."

## 3. Failure Recovery Guide

During a live demo, things can go wrong. Here is how to recover smoothly without breaking the presentation:

**Problem:** OpenSky API fails or is rate-limited (No planes appear).
**Recovery:** Stop the backend (`Ctrl+C`). Restart it in Demo Mode:
`$env:ATC_DEMO_MODE="true"; python run.py`. Explain that you are using a prerecorded offline snapshot.

**Problem:** WebSocket disconnects / Frontend freezes.
**Recovery:** Check the backend console. If Flask is running, simply refresh the browser tab. The frontend will instantly reconnect and request a full state snapshot.

**Problem:** Backend crashes completely.
**Recovery:** `Ctrl+C` to kill the process. Relaunch `python run.py`. The simulation engine will rebuild its state immediately upon startup. Refresh the frontend.
