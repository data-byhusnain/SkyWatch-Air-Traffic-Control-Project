// ============================================================
// src/utils/constants.js -- Frontend Constants
// ============================================================
// All magic numbers and config values in one place.
// Change these to adjust frontend behavior without editing components.
// ============================================================

// Backend URL for socket.io-client connection.
// In development, Vite proxy handles routing, so we use relative path.
// In production, set this to the actual Flask server URL.
export const BACKEND_URL = "https://husnainriax-skywatch-backend.hf.space";

// Socket.io reconnection settings
export const SOCKET_RECONNECT_ATTEMPTS = 20;
export const SOCKET_RECONNECT_DELAY = 2000; // ms between reconnect attempts

// Alert level thresholds (must match backend collision.py)
export const DANGER_DIST_KM = 5;
export const WARNING_DIST_KM = 10;

// Alert level colors (CSS variable references for consistency)
export const ALERT_COLORS = {
  GREEN: "#00ff88",
  YELLOW: "#ffcc00",
  RED: "#ff4444",
};

// Altitude conversion factor
export const METERS_TO_FEET = 3.281;

// Speed conversion factor
export const MS_TO_KNOTS = 1.944;
