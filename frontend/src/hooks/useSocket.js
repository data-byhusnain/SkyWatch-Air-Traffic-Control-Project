// ============================================================
// src/hooks/useSocket.js -- WebSocket Lifecycle Hook
// ============================================================
//
// PURPOSE:
//   Manages the entire WebSocket connection lifecycle:
//   - Connect on mount
//   - Subscribe to backend events
//   - Update global context on each event
//   - Clean up listeners on unmount
//   - Handle reconnection gracefully
//
// WHY A CUSTOM HOOK?
//   Putting socket logic inside a component would:
//   - Mix UI concerns with I/O concerns
//   - Make it hard to reuse the socket connection
//   - Cause duplicate listeners on re-renders
//
//   A custom hook encapsulates all socket logic cleanly.
//   The hook is called ONCE in App.jsx — not in every component.
//
// EVENTS LISTENED TO:
//   'connect'           -- socket connected to backend
//   'disconnect'        -- socket disconnected
//   'aircraft_update'   -- backend sends new aircraft positions
//   'alert_update'      -- backend sends new collision alerts
//   'simulation_status' -- backend sends system health info
//   'server_message'    -- backend sends text messages (debug)
//
// DUPLICATE LISTENER PREVENTION:
//   The useEffect cleanup function calls socket.off() for EVERY
//   event before the component unmounts or the effect re-runs.
//   Without this, React strict mode (or re-renders) would attach
//   duplicate listeners, causing each event to fire 2x, 3x, etc.
// ============================================================

import { useEffect } from "react";
import socket from "../services/socketService";
import { useAircraft } from "../context/AircraftContext";

/**
 * useSocket -- call this once in App.jsx to activate WebSocket.
 *
 * It connects to the Flask-SocketIO backend, subscribes to all
 * events, and pipes incoming data into AircraftContext.
 */
export default function useSocket() {
  const {
    updateAircraft,
    updateAlerts,
    updateStatus,
    updateConnected,
  } = useAircraft();

  useEffect(() => {
    // ── Connect ───────────────────────────────────────────
    console.log("[SOCKET] Connecting to backend...");
    socket.connect();

    // ── Event: Connected ──────────────────────────────────
    function onConnect() {
      console.log("[SOCKET] Connected (id:", socket.id, ")");
      updateConnected(true);
    }

    // ── Event: Disconnected ───────────────────────────────
    function onDisconnect(reason) {
      console.log("[SOCKET] Disconnected. Reason:", reason);
      updateConnected(false);
    }

    // ── Event: Aircraft Update ────────────────────────────
    // Payload: { aircraft: [{icao24, callsign, lat, lon, ...}, ...] }
    function onAircraftUpdate(data) {
      const list = data.aircraft || [];
      console.log("[SOCKET] Aircraft update received:", list.length);
      updateAircraft(list);
    }

    // ── Event: Alert Update ───────────────────────────────
    // Payload: { alerts: [{aircraft_1, aircraft_2, distance_km, level}, ...] }
    function onAlertUpdate(data) {
      const list = data.alerts || [];
      if (list.length > 0) {
        console.log("[SOCKET] Alert update received:", list.length);
      }
      updateAlerts(list);
    }

    // ── Event: Simulation Status ──────────────────────────
    // Payload: { running, source, aircraft_count, alert_count }
    function onSimulationStatus(data) {
      updateStatus(data);
    }

    // ── Event: Server Message (debug) ─────────────────────
    function onServerMessage(data) {
      console.log("[SOCKET] Server message:", data.message);
    }

    // ── Event: Reconnection ───────────────────────────────
    function onReconnectAttempt(attempt) {
      console.log("[SOCKET] Reconnect attempt:", attempt);
    }

    function onReconnect() {
      console.log("[SOCKET] Reconnected successfully");
      updateConnected(true);
    }

    // ── Attach all listeners ──────────────────────────────
    socket.on("connect", onConnect);
    socket.on("disconnect", onDisconnect);
    socket.on("aircraft_update", onAircraftUpdate);
    socket.on("alert_update", onAlertUpdate);
    socket.on("simulation_status", onSimulationStatus);
    socket.on("server_message", onServerMessage);
    socket.io.on("reconnect_attempt", onReconnectAttempt);
    socket.io.on("reconnect", onReconnect);

    // ── Cleanup on unmount ────────────────────────────────
    // CRITICAL: Remove all listeners to prevent duplicates.
    // Then disconnect the socket cleanly.
    return () => {
      console.log("[SOCKET] Cleaning up listeners...");
      socket.off("connect", onConnect);
      socket.off("disconnect", onDisconnect);
      socket.off("aircraft_update", onAircraftUpdate);
      socket.off("alert_update", onAlertUpdate);
      socket.off("simulation_status", onSimulationStatus);
      socket.off("server_message", onServerMessage);
      socket.io.off("reconnect_attempt", onReconnectAttempt);
      socket.io.off("reconnect", onReconnect);
      socket.disconnect();
    };
  }, [updateAircraft, updateAlerts, updateStatus, updateConnected]);
}
