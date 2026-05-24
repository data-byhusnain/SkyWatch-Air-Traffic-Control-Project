// ============================================================
// StatusBar.jsx -- System status display at the top of the page
// ============================================================
import { useState } from "react";
import { useAircraft } from "../../context/AircraftContext";
import AnalyticsModal from "../AnalyticsModal/AnalyticsModal";
import "./StatusBar.css";

export default function StatusBar() {
  const {
    aircraft,
    alerts,
    connected,
    simulationRunning,
    dataSource,
    lastUpdate,
  } = useAircraft();

  const [isAnalyticsOpen, setIsAnalyticsOpen] = useState(false);

  // Count alerts by severity
  const redAlerts = alerts.filter((a) => a.level === "RED").length;
  const yellowAlerts = alerts.filter((a) => a.level === "YELLOW").length;

  // Format last update time (just the time portion)
  const formattedTime = lastUpdate
    ? new Date(lastUpdate).toLocaleTimeString()
    : "--:--:--";

  // Determine badge style based on data source
  const badgeClass = {
    LIVE: "status-bar__badge--live",
    SIMULATED: "status-bar__badge--simulated",
    DEMO: "status-bar__badge--demo",
    MIXED: "status-bar__badge--simulated",
    NONE: "status-bar__badge--offline",
  }[dataSource] || "status-bar__badge--offline";

  return (
    <>
      <header className="status-bar" id="status-bar">
        {/* Title */}
        <div className="status-bar__title">
          <span className="status-bar__title-icon">◉</span>
          ATC Monitor
        </div>

        {/* Metrics */}
        <div className="status-bar__metrics">
          {/* Connection */}
          <div className="status-bar__metric">
            <span
              className={`status-bar__dot ${
                connected ? "status-bar__dot--connected" : "status-bar__dot--disconnected"
              }`}
            />
            <span className="status-bar__value">
              {connected ? "ONLINE" : "OFFLINE"}
            </span>
          </div>

          {/* Data Source */}
          <div className="status-bar__metric">
            <span className="status-bar__label">Source</span>
            <span className={`status-bar__badge ${badgeClass}`}>
              {dataSource}
            </span>
          </div>

          {/* Aircraft Count */}
          <div className="status-bar__metric">
            <span className="status-bar__label">Aircraft</span>
            <span className="status-bar__value status-bar__value--safe">
              {aircraft.length}
            </span>
          </div>

          {/* Alerts */}
          <div className="status-bar__metric">
            <span className="status-bar__label">Alerts</span>
            {redAlerts > 0 && (
              <span className="status-bar__value status-bar__value--danger">
                {redAlerts} RED
              </span>
            )}
            {yellowAlerts > 0 && (
              <span className="status-bar__value status-bar__value--warn">
                {yellowAlerts} YLW
              </span>
            )}
            {alerts.length === 0 && (
              <span className="status-bar__value status-bar__value--safe">
                CLEAR
              </span>
            )}
          </div>

          {/* Simulation */}
          <div className="status-bar__metric">
            <span className="status-bar__label">Sim</span>
            <span className={`status-bar__value ${simulationRunning ? "status-bar__value--safe" : "status-bar__value--danger"}`}>
              {simulationRunning ? "ON" : "OFF"}
            </span>
          </div>

          {/* Last Update */}
          <div className="status-bar__metric">
            <span className="status-bar__label">Updated</span>
            <span className="status-bar__value">{formattedTime}</span>
          </div>
          
          {/* Analytics Button */}
          <button 
            className="status-bar__btn" 
            onClick={() => setIsAnalyticsOpen(true)}
            style={{ 
              marginLeft: '10px', 
              background: 'rgba(0, 255, 136, 0.1)', 
              border: '1px solid #00ff88', 
              color: '#00ff88',
              padding: '4px 10px',
              borderRadius: '4px',
              cursor: 'pointer',
              fontFamily: 'inherit',
              fontSize: '11px',
              fontWeight: 'bold'
            }}
          >
            ANALYTICS
          </button>
        </div>
      </header>

      {isAnalyticsOpen && (
        <AnalyticsModal onClose={() => setIsAnalyticsOpen(false)} />
      )}
    </>
  );
}
