import { useAircraft } from "../../context/AircraftContext";
import { MS_TO_KNOTS, METERS_TO_FEET } from "../../utils/constants";
import "./AnalyticsModal.css";

export default function AnalyticsModal({ onClose }) {
  const { aircraft, alerts } = useAircraft();

  // Compute Statistics
  const totalAircraft = aircraft.length;
  
  let avgSpeed = 0;
  let avgAlt = 0;
  
  const sources = { LIVE: 0, SIMULATED: 0, DEMO: 0 };
  
  if (totalAircraft > 0) {
    avgSpeed = aircraft.reduce((sum, ac) => sum + ac.velocity, 0) / totalAircraft;
    avgAlt = aircraft.reduce((sum, ac) => sum + ac.altitude, 0) / totalAircraft;
    
    aircraft.forEach(ac => {
      if (sources[ac.source] !== undefined) {
        sources[ac.source]++;
      }
    });
  }

  const redAlerts = alerts.filter(a => a.level === "RED").length;
  const yellowAlerts = alerts.filter(a => a.level === "YELLOW").length;

  return (
    <div className="analytics-overlay" onClick={onClose}>
      <div className="analytics-modal" onClick={(e) => e.stopPropagation()}>
        <div className="analytics-header">
          <h2>SYSTEM ANALYTICS</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        
        <div className="analytics-body">
          <div className="stat-card">
            <span className="stat-label">TOTAL AIRCRAFT</span>
            <span className="stat-value text-safe">{totalAircraft}</span>
          </div>
          
          <div className="stat-card">
            <span className="stat-label">AVG SPEED</span>
            <span className="stat-value">{Math.round(avgSpeed * MS_TO_KNOTS)} KTS</span>
          </div>

          <div className="stat-card">
            <span className="stat-label">AVG ALTITUDE</span>
            <span className="stat-value">{Math.round(avgAlt * METERS_TO_FEET)} FT</span>
          </div>

          <div className="stat-card">
            <span className="stat-label">ALERTS (RED/YLW)</span>
            <span className="stat-value">
              <span className="text-danger">{redAlerts}</span> / <span className="text-warn">{yellowAlerts}</span>
            </span>
          </div>
        </div>

        <div className="analytics-sources">
          <h3>DATA SOURCES</h3>
          <div className="source-bar-container">
            <div className="source-bar live" style={{ width: `${totalAircraft ? (sources.LIVE / totalAircraft) * 100 : 0}%` }}>
              {sources.LIVE > 0 && `LIVE (${sources.LIVE})`}
            </div>
            <div className="source-bar sim" style={{ width: `${totalAircraft ? (sources.SIMULATED / totalAircraft) * 100 : 0}%` }}>
              {sources.SIMULATED > 0 && `SIM (${sources.SIMULATED})`}
            </div>
            <div className="source-bar demo" style={{ width: `${totalAircraft ? (sources.DEMO / totalAircraft) * 100 : 0}%` }}>
              {sources.DEMO > 0 && `DEMO (${sources.DEMO})`}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
