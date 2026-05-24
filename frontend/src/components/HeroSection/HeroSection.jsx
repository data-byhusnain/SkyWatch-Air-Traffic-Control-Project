import React from "react";
import "./HeroSection.css";

export default function HeroSection({ onLaunchRadar }) {
  return (
    <section className="hero-container">
      <div className="hero-content">
        <h1 className="hero-title">
          Real-time <span className="highlight">Airspace</span> Monitoring
        </h1>
        <p className="hero-subtitle">
          Advanced predictive collision detection and radar visualization for modern air traffic control. Keep the skies safe with precision tracking and instant alerts.
        </p>
        
        <div className="hero-stats">
          <div className="stat-item">
            <span className="stat-value">Real-time</span>
            <span className="stat-label">ADS-B Tracking</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">Sub-second</span>
            <span className="stat-label">Conflict Detection</span>
          </div>
        </div>

        <button className="launch-radar-btn" onClick={onLaunchRadar}>
          Launch Radar
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="5" y1="12" x2="19" y2="12"></line>
            <polyline points="12 5 19 12 12 19"></polyline>
          </svg>
        </button>
      </div>

      <div className="hero-overlay"></div>
    </section>
  );
}
