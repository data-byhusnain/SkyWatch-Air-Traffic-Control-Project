# How to Run the ATC Monitoring System

This guide provides step-by-step instructions on how to run both the Backend and Frontend of the ATC Monitoring System using Visual Studio Code (VS Code).

## Prerequisites
- **Python 3.10+** installed on your system.
- **Node.js (v18+)** installed on your system.
- **VS Code** installed.

---

## Step 1: Open the Project in VS Code
1. Open Visual Studio Code.
2. Go to `File > Open Folder` and select the root directory of the project (e.g., `atc project`).

---

## Step 2: Start the Backend Server
The backend handles physics simulation, collision detection, and WebSocket broadcasting.

1. Open a new terminal in VS Code (`Terminal > New Terminal`).
2. Navigate to the backend directory:
   ```bash
   cd backend
   ```
3. Activate the Python virtual environment:
   - **For Windows:**
     ```bash
     .\venv\Scripts\activate
     ```
   - **For Mac/Linux:**
     ```bash
     source venv/bin/activate
     ```
   *(You should see `(venv)` appear at the start of your terminal line, confirming the environment is active).*
4. Run the Python server:
   ```bash
   python run.py
   ```
5. You should see logs indicating that the `[App]`, `[Simulation]`, and `[Broadcaster]` have started successfully. Keep this terminal running.

---

## Step 3: Start the Frontend Application
The frontend is the React + HTML5 Canvas radar visualization.

1. Open a **second terminal** in VS Code (click the `+` icon in the terminal panel to open a split or new terminal).
2. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
3. Run the Vite development server:
   ```bash
   npm run dev
   ```
4. The terminal will output a local URL, typically: `http://localhost:5173/`
5. **Ctrl + Click** (or Cmd + Click on Mac) the URL to open it in your web browser. 
6. The ATC Radar System is now live!

---

## Running in Demo Mode (Highly Recommended for Presentations)

Public APIs like OpenSky Network have strict rate limits. If you request data too frequently, or if your internet connection is unstable, the live data feed may fail.

To guarantee a smooth, flawless experience during a presentation or viva, you should run the backend in **Demo Mode**. This mode bypasses the live API and loads a prerecorded flight dataset (`demo_data.json`), while still utilizing the live physics simulation engine for movement.

**To start Demo Mode, replace Step 2, Point 4 with the following command:**

### Windows (PowerShell):
```powershell
$env:ATC_DEMO_MODE="true"; python run.py
```

### Mac/Linux (Bash):
```bash
ATC_DEMO_MODE=true python run.py
```

You will see a large banner in the terminal reading `[ATC DEMO MODE ENABLED]`, confirming you are safely running offline.
