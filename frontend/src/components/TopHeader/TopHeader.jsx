import React from 'react';
import './TopHeader.css';

export default function TopHeader({ activeView, setActiveView }) {
  return (
    <header className="saas-navbar">
      <div className="nav-container">
        {/* Brand / Logo Area */}
        <div className="nav-brand">
          <div className="brand-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2L2 22l10-5 10 5L12 2z" />
            </svg>
          </div>
          <span className="brand-text">SkyWatch<span className="brand-suffix">ATC</span></span>
        </div>

        {/* Navigation Links */}
        <nav className="nav-links">
          <button 
            className={`nav-btn ${activeView === 'radar' ? 'active' : ''}`}
            onClick={() => setActiveView('radar')}
          >
            Radar
          </button>
          <button 
            className={`nav-btn ${activeView === 'analytics' ? 'active' : ''}`}
            onClick={() => setActiveView('analytics')}
          >
            Analytics
          </button>
        </nav>

        {/* Right Status Badge */}
        <div className="nav-status">
          <div className="status-badge">
            <div className="pulse-dot"></div>
            <span>System Live</span>
          </div>
        </div>
      </div>
    </header>
  );
}
