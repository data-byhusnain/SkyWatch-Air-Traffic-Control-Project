import React from 'react';
import './Footer.css';

export default function Footer({ setActiveView }) {
  const handleNav = (e, view) => {
    e.preventDefault();
    if (setActiveView) {
      setActiveView(view);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  return (
    <footer className="professional-footer">
      <div className="footer-container">
        
        {/* Column 1: Brand & Description */}
        <div className="footer-col brand-col">
          <div className="footer-brand">
            <div className="brand-icon-small">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2L2 22l10-5 10 5L12 2z" />
              </svg>
            </div>
            <span>SkyWatch</span>
          </div>
          <p className="footer-desc">
            Advanced real-time airspace monitoring system powered by ADS-B telemetry data. 
            Providing commercial-grade radar visualization, conflict prediction, and global traffic analytics.
          </p>
        </div>

        {/* Column 2: Quick Links */}
        <div className="footer-col">
          <h3 className="footer-heading">Product Features</h3>
          <ul className="footer-links">
            <li><a href="#radar" onClick={(e) => handleNav(e, 'radar')}>Live Radar Map</a></li>
            <li><a href="#analytics" onClick={(e) => handleNav(e, 'analytics')}>Global Analytics</a></li>
            <li><a href="#alerts" onClick={(e) => handleNav(e, 'radar')}>Threat Prediction</a></li>
            <li><a href="#tracking" onClick={(e) => handleNav(e, 'radar')}>Flight Tracking</a></li>
          </ul>
        </div>

        {/* Column 3: Resources */}
        <div className="footer-col">
          <h3 className="footer-heading">Resources</h3>
          <ul className="footer-links">
            <li><a href="https://opensky-network.org" target="_blank" rel="noreferrer">OpenSky Network API</a></li>
            <li><a href="https://github.com/data-byhusnain/SkyWatch-Air-Traffic-Control-Project" target="_blank" rel="noreferrer">GitHub Repository</a></li>
          </ul>
        </div>

        {/* Column 4: Status */}
        <div className="footer-col">
          <h3 className="footer-heading">System Status</h3>
          <ul className="footer-status-list">
            <li>
              <span className="status-dot green"></span>
              Main Telemetry Server: <strong>Online</strong>
            </li>
            <li>
              <span className="status-dot green"></span>
              Prediction Engine: <strong>Active</strong>
            </li>
            <li>
              <span className="status-dot yellow"></span>
              ADS-B Coverage: <strong>Optimal</strong>
            </li>
          </ul>
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="footer-bottom">
        <div className="footer-bottom-container">
          <span className="copyright">&copy; {new Date().getFullYear()} SkyWatch ATC. All rights reserved.</span>
          <div className="footer-legal">
            <a href="#privacy">Privacy Policy</a>
            <a href="#terms">Terms of Service</a>
            <a href="#cookies">Cookie Settings</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
