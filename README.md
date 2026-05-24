# ✦ SkyWatch ATC - Live Radar & Air Traffic Control System

![SkyWatch ATC Dashboard](https://img.shields.io/badge/Status-Active-brightgreen)
![React](https://img.shields.io/badge/React-18-blue?logo=react)
![Flask](https://img.shields.io/badge/Flask-Backend-black?logo=flask)
![WebSocket](https://img.shields.io/badge/Socket.io-Realtime-orange)

SkyWatch ATC is a premium, real-time Air Traffic Control (ATC) monitoring dashboard. It integrates live flight telemetry from the OpenSky Network with a custom-built collision detection engine, presenting data through a sleek, "Mossy Hollow" themed React interface.

## 🌟 Key Features

- **📡 Live Global Telemetry:** Fetches and visualizes real-world aircraft data (Latitude, Longitude, Altitude, Velocity, Heading) in real-time.
- **🚨 Advanced Collision Engine:** Mathematical background engine that predicts potential airspace conflicts, categorizing them into `YELLOW` (Warning) and `RED` (Critical) alerts.
- **🗺️ Interactive Radar Map:** Smooth, simulated trajectory lines with real-time positional updates using Leaflet.js.
- **📊 Detailed Analytics Dashboard:** Fullscreen analytics offering deep insights into active traffic, fleet operators, regional distribution, and flight phases (climbing/cruising/descending).
- **🎨 Premium UI/UX:** Built with a custom "Mossy Hollow" aesthetic—featuring glassmorphism, glowing micro-animations, and dynamic data tables.

## 🛠️ Technology Stack

**Frontend:**
- React.js + Vite
- Context API (State Management)
- Socket.io-client (Real-time data streaming)
- Leaflet & React-Leaflet (Mapping)
- Pure CSS (No UI libraries, completely custom design system)

**Backend:**
- Python 3
- Flask & Flask-SocketIO
- APScheduler (Background orchestration)
- Math-based predictive collision detection algorithms

## 🚀 Getting Started

### Prerequisites
- Node.js (v18+)
- Python (3.9+)

### 1. Start the Backend
Navigate to the `backend` directory, install dependencies, and start the server:
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # On Windows
pip install -r requirements.txt
python run.py
```

### 2. Start the Frontend
In a new terminal, navigate to the `frontend` directory:
```bash
cd frontend
npm install
npm run dev
```

Open your browser to `http://localhost:5173` to view the radar.

## 📂 Project Structure
- `/backend`: Python Flask server, WebSocket broadcaster, and collision detection engine.
- `/frontend`: React application, UI components, and Map integrations.

## 🌍 Data Source
Live flight data is provided courtesy of the [OpenSky Network](https://opensky-network.org/).

## 📄 License
This project is for educational and portfolio purposes.
