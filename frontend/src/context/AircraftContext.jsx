// ============================================================
// src/context/AircraftContext.jsx -- Global State Provider
// ============================================================
//
// PURPOSE:
//   Stores ALL realtime data received from the backend WebSocket.
//   Every component in the app reads from this context instead of
//   managing its own copy of aircraft/alert data.
//
// WHY CONTEXT (not Redux, not Zustand)?
//   - Built into React (no extra dependency)
//   - Sufficient for a single-page app with one data source
//   - Simple to understand for a semester project
//   - No boilerplate: just Provider + useContext
//
// STATE SHAPE:
//   aircraft: Aircraft[]       -- all tracked aircraft
//   alerts: CollisionAlert[]   -- active collision warnings
//   connected: boolean         -- WebSocket connection status
//   simulationRunning: boolean -- backend simulation engine status
//   dataSource: string         -- "LIVE" / "SIMULATED" / "DEMO" / "MIXED" / "NONE"
//   lastUpdate: string|null    -- ISO timestamp of last received update
//
// HOW IT CONNECTS:
//   main.jsx wraps <App /> with <AircraftProvider>
//   useSocket.js hook calls the dispatch/setter functions
//   All display components call useAircraft() to read the state
// ============================================================

import { createContext, useContext, useState, useCallback } from "react";

// Create the context object (consumed by useContext)
const AircraftContext = createContext(null);

/**
 * AircraftProvider — wraps the app and provides global state.
 *
 * Usage in main.jsx:
 *   <AircraftProvider>
 *     <App />
 *   </AircraftProvider>
 */
export function AircraftProvider({ children }) {
  // ── State ───────────────────────────────────────────────
  const [aircraft, setAircraft] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [connected, setConnected] = useState(false);
  const [simulationRunning, setSimulationRunning] = useState(false);
  const [dataSource, setDataSource] = useState("NONE");
  const [lastUpdate, setLastUpdate] = useState(null);
  const [selectedAircraftId, setSelectedAircraftId] = useState(null);

  // ── Stable Update Functions (useCallback prevents re-renders) ──
  // These are called by useSocket.js when WebSocket events arrive.

  const updateAircraft = useCallback((aircraftList) => {
    setAircraft(aircraftList);
    setLastUpdate(new Date().toISOString());
  }, []);

  const updateAlerts = useCallback((alertList) => {
    setAlerts(alertList);
  }, []);

  const updateStatus = useCallback((status) => {
    setSimulationRunning(status.running || false);
    setDataSource(status.source || "NONE");
  }, []);

  const updateConnected = useCallback((isConnected) => {
    setConnected(isConnected);
  }, []);

  // ── Context Value ─────────────────────────────────────────
  // This object is what every consumer component receives.
  const value = {
    // Data
    aircraft,
    alerts,
    connected,
    simulationRunning,
    dataSource,
    lastUpdate,
    selectedAircraftId,
    // Updaters (used by useSocket hook)
    updateAircraft,
    updateAlerts,
    updateStatus,
    updateConnected,
    setSelectedAircraftId,
  };

  return (
    <AircraftContext.Provider value={value}>
      {children}
    </AircraftContext.Provider>
  );
}

/**
 * useAircraft — convenience hook to consume the context.
 *
 * Usage in any component:
 *   const { aircraft, alerts, connected } = useAircraft();
 *
 * Throws an error if used outside <AircraftProvider>.
 */
export function useAircraft() {
  const context = useContext(AircraftContext);
  if (!context) {
    throw new Error("useAircraft must be used within <AircraftProvider>");
  }
  return context;
}
