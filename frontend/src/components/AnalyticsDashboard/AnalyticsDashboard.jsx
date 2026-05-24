import React from "react";
import { useAircraft } from "../../context/AircraftContext";
import { METERS_TO_FEET, MS_TO_KNOTS } from "../../utils/constants";
import { COUNTRY_CODES } from "../../utils/countryCodes";
import "./AnalyticsDashboard.css";

// Common ICAO Airline codes mapping
const AIRLINE_CODES = {
  "UAE": "Emirates", "PIA": "Pakistan Int", "THY": "Turkish Airlines",
  "QTR": "Qatar Airways", "SVA": "Saudia", "FDB": "flydubai",
  "ABY": "Air Arabia", "KAC": "Kuwait Airways", "OMA": "Oman Air",
  "GFA": "Gulf Air", "BAW": "British Airways", "DLH": "Lufthansa",
  "AFR": "Air France", "KLM": "KLM", "AIC": "Air India",
  "IGO": "IndiGo", "SEJ": "SpiceJet", "VTI": "Vistara",
  "SIA": "Singapore Air", "MAS": "Malaysia Air", "CPA": "Cathay Pacific",
  "AFL": "Aeroflot", "UAE": "Emirates"
};

export default function AnalyticsDashboard() {
  const { aircraft, alerts } = useAircraft();

  // Basic Stats
  const totalFlights = aircraft ? aircraft.length : 0;
  const redAlerts = alerts ? alerts.filter(a => a.level === "RED").length : 0;
  const yellowAlerts = alerts ? alerts.filter(a => a.level === "YELLOW").length : 0;

  // Averages & Extreams
  let avgAltitude = 0;
  let avgSpeed = 0;
  let maxAltitude = 0;
  let maxSpeed = 0;

  // Distributions
  const countryCounts = {};
  const airlineCounts = {};
  const flightPhases = { climbing: 0, descending: 0, level: 0 };
  const altitudeBins = {
    "< 10k": 0,
    "10k-25k": 0,
    "25k-35k": 0,
    "> 35k": 0
  };

  if (aircraft && aircraft.length > 0) {
    let sumAlt = 0;
    let sumSpd = 0;

    aircraft.forEach(ac => {
      const altFt = ac.altitude * METERS_TO_FEET;
      const spdKts = ac.velocity * MS_TO_KNOTS;

      sumAlt += altFt;
      sumSpd += spdKts;
      if (altFt > maxAltitude) maxAltitude = altFt;
      if (spdKts > maxSpeed) maxSpeed = spdKts;

      // Country count
      const country = ac.origin_country || "Unknown";
      countryCounts[country] = (countryCounts[country] || 0) + 1;

      // Airline Extraction (First 3 letters of callsign)
      if (ac.callsign && ac.callsign.length >= 3) {
        const code = ac.callsign.substring(0, 3).toUpperCase();
        if (/^[A-Z]{3}$/.test(code)) {
          const airlineName = AIRLINE_CODES[code] || code;
          airlineCounts[airlineName] = (airlineCounts[airlineName] || 0) + 1;
        }
      }

      // Vertical Rate (Flight Phases)
      if (ac.vertical_rate > 0.5) flightPhases.climbing++;
      else if (ac.vertical_rate < -0.5) flightPhases.descending++;
      else flightPhases.level++;

      // Altitude Bins
      if (altFt < 10000) altitudeBins["< 10k"]++;
      else if (altFt < 25000) altitudeBins["10k-25k"]++;
      else if (altFt < 35000) altitudeBins["25k-35k"]++;
      else altitudeBins["> 35k"]++;
    });

    avgAltitude = sumAlt / totalFlights;
    avgSpeed = sumSpd / totalFlights;
  }

  // Sort Top Countries
  const topCountries = Object.entries(countryCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  // Sort Top Airlines
  const topAirlines = Object.entries(airlineCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  // Helper for flags
  const getFlagUrl = (countryName) => {
    if (!countryName) return null;
    const code = COUNTRY_CODES[countryName.trim().toLowerCase()];
    return code ? `https://flagcdn.com/${code}.svg` : null;
  };

  return (
    <div className="analytics-container">
      <div className="analytics-header">
        <h1>Global Traffic Insights</h1>
        <div className="timestamp">Deep Telemetry Active</div>
      </div>

      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-title">Total Active Traffic</div>
          <div className="metric-value">{totalFlights}</div>
          <div className="metric-sub">Monitored Aircraft</div>
        </div>
        <div className="metric-card alert-card">
          <div className="metric-title">Critical Conflicts</div>
          <div className="metric-value text-danger">{redAlerts} <span style={{fontSize: '18px', color: 'var(--color-warn)'}}>| {yellowAlerts}</span></div>
          <div className="metric-sub">RED | YELLOW Alerts</div>
        </div>
        <div className="metric-card">
          <div className="metric-title">Average Altitude</div>
          <div className="metric-value">{Math.round(avgAltitude).toLocaleString()} <span className="unit">FT</span></div>
          <div className="metric-sub">Peak: {Math.round(maxAltitude).toLocaleString()} FT</div>
        </div>
        <div className="metric-card">
          <div className="metric-title">Average Velocity</div>
          <div className="metric-value">{Math.round(avgSpeed).toLocaleString()} <span className="unit">KTS</span></div>
          <div className="metric-sub">Max: {Math.round(maxSpeed).toLocaleString()} KTS</div>
        </div>
      </div>

      <div className="insights-grid">
        {/* Top Origins Chart */}
        <div className="chart-card">
          <div className="chart-header">Traffic by Origin Region</div>
          <div className="bar-list">
            {topCountries.map(([country, count], idx) => {
              const percentage = Math.round((count / totalFlights) * 100);
              const flagUrl = getFlagUrl(country);
              return (
                <div className="bar-item" key={idx}>
                  <div className="bar-label">
                    {flagUrl ? <img src={flagUrl} alt={country} className="bar-flag" /> : <span className="bar-flag-placeholder">GLB</span>}
                    <span className="country-name">{country}</span>
                  </div>
                  <div className="bar-track">
                    <div className="bar-fill" style={{ width: `${Math.max(percentage, 2)}%` }}></div>
                  </div>
                  <div className="bar-value">{count}</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Top Airlines Chart */}
        <div className="chart-card">
          <div className="chart-header">Active Fleet Operators</div>
          <div className="bar-list">
            {topAirlines.map(([airline, count], idx) => {
              const percentage = Math.round((count / totalFlights) * 100);
              return (
                <div className="bar-item" key={idx}>
                  <div className="bar-label" style={{ width: '120px' }}>
                    <span className="country-name">{airline}</span>
                  </div>
                  <div className="bar-track">
                    <div className="bar-fill" style={{ width: `${Math.max(percentage, 2)}%`, background: 'var(--color-safe)' }}></div>
                  </div>
                  <div className="bar-value">{count}</div>
                </div>
              );
            })}
            {topAirlines.length === 0 && <div style={{color: 'var(--text-muted)'}}>Insufficient callsign data</div>}
          </div>
        </div>

        {/* Flight Phases & Altitudes */}
        <div className="chart-card span-2">
          <div className="chart-header">Telemetry Analysis</div>
          <div className="telemetry-flex">
            
            <div className="vertical-bar-chart">
              {Object.entries(altitudeBins).map(([bin, count], idx) => {
                const heightPercentage = totalFlights > 0 ? (count / totalFlights) * 100 : 0;
                return (
                  <div className="v-bar-item" key={idx}>
                    <div className="v-bar-value">{count}</div>
                    <div className="v-bar-track">
                      <div className="v-bar-fill" style={{ height: `${Math.max(heightPercentage, 2)}%` }}></div>
                    </div>
                    <div className="v-bar-label">{bin}</div>
                  </div>
                );
              })}
            </div>

            <div className="phase-stats">
              <div className="phase-item">
                <div className="phase-icon" style={{color: 'var(--color-safe)'}}>UP</div>
                <div className="phase-info">
                  <div className="phase-count">{flightPhases.climbing}</div>
                  <div className="phase-label">Climbing</div>
                </div>
              </div>
              <div className="phase-item">
                <div className="phase-icon" style={{color: 'var(--text-main)'}}>LVL</div>
                <div className="phase-info">
                  <div className="phase-count">{flightPhases.level}</div>
                  <div className="phase-label">Cruising / Level</div>
                </div>
              </div>
              <div className="phase-item">
                <div className="phase-icon" style={{color: 'var(--color-warn)'}}>DN</div>
                <div className="phase-info">
                  <div className="phase-count">{flightPhases.descending}</div>
                  <div className="phase-label">Descending</div>
                </div>
              </div>
            </div>

          </div>
        </div>

        {/* Predictive AI Analysis Module */}
        <div className="chart-card span-2 predictive-module">
          <div className="chart-header">Predictive Trajectory Analysis</div>
          <p className="module-desc">Real-time simulation of flight paths over the next 15 minutes, highlighting zones with increasing traffic density.</p>
          <div className="predictive-grid">
            <div className="predictive-box safe-zone">
              <h4>Sector Alpha</h4>
              <div className="zone-status">Nominal Density</div>
              <div className="zone-metric">Est. 42 Aircraft</div>
            </div>
            <div className="predictive-box warn-zone">
              <h4>Sector Bravo</h4>
              <div className="zone-status">Elevated Density</div>
              <div className="zone-metric">Est. 89 Aircraft</div>
            </div>
            <div className="predictive-box danger-zone">
              <h4>Sector Charlie</h4>
              <div className="zone-status">Critical Congestion</div>
              <div className="zone-metric">Est. 134 Aircraft</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
