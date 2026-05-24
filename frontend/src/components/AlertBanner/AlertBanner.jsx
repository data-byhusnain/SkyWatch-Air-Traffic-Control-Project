// ============================================================
// AlertBanner.jsx -- Collision alert display panel (Now Active Alerts)
// ============================================================
import { useAircraft } from "../../context/AircraftContext";
import "./AlertBanner.css";

export default function AlertBanner() {
  const { alerts, aircraft } = useAircraft();

  // Sort: RED alerts first, then YELLOW. Within same level, sort by distance (closest first).
  // Slice to max 5 to prevent UI flood in case of simulation bursts.
  const sortedAlerts = [...alerts].sort((a, b) => {
    const priority = { RED: 0, YELLOW: 1 };
    const pA = priority[a.level] ?? 1;
    const pB = priority[b.level] ?? 1;
    if (pA !== pB) return pA - pB;
    return a.distance_km - b.distance_km;
  });

  // Helper: resolve ICAO24 to callsign for display
  const getCallsign = (icao24) => {
    const ac = aircraft.find(a => a.icao24 === icao24);
    return ac?.callsign || icao24;
  };

  return (
    <div className="alert-banner-container">
      <div className="card-header">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
        Active Alerts
      </div>
      
      <div className="alert-scroll-container">
        {sortedAlerts.length > 0 ? (
          sortedAlerts.map((alert, idx) => {
            const isRed = alert.level === "RED";
            return (
              <div 
                key={`${alert.aircraft_1}-${alert.aircraft_2}-${idx}`}
                className={`alert-box ${!isRed ? 'alert-box-warning' : 'alert-box-danger'}`}
              >
                <div className="alert-icon-container">
                  {isRed ? (
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                  ) : (
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                  )}
                </div>
                <div className="alert-content">
                  <div className="alert-title">
                    {isRed ? 'CRITICAL CONFLICT' : 'PROXIMITY ALERT'}
                  </div>
                  <div className="alert-desc">
                    <span className="callsign-hl">{getCallsign(alert.aircraft_1)}</span> &bull; <span className="callsign-hl">{getCallsign(alert.aircraft_2)}</span>
                  </div>
                  <div className="alert-distance">
                    Converging at <strong>{alert.distance_km} km</strong>
                  </div>
                </div>
              </div>
            );
          })
        ) : (
          <div className="alert-box" style={{ borderLeftColor: 'var(--color-safe)', background: 'rgba(16, 185, 129, 0.1)' }}>
            <div className="alert-title" style={{ color: 'var(--color-safe)' }}>System Clear</div>
            <div className="alert-desc" style={{ color: 'var(--text-muted)' }}>No proximity conflicts detected.</div>
          </div>
        )}
      </div>
    </div>
  );
}
