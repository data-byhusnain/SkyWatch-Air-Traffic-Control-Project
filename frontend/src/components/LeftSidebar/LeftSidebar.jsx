import React from "react";
import "./LeftSidebar.css";
import { useAircraft } from "../../context/AircraftContext";

export default function LeftSidebar({ activeView, setActiveView }) {
  const { aircraft } = useAircraft();
  const aircraftCount = aircraft ? aircraft.length : 0;

  return (
    <div className="sidebar-left">
      <div className="logo-area">
        <div className="logo-title">
          <span className="brand-mark">SW</span>
          SKYWATCH ATC
        </div>
      </div>
      
      <div className="nav-menu">
        <div 
          className={`nav-item ${activeView === 'radar' ? 'active' : ''}`}
          onClick={() => setActiveView('radar')}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/><line x1="12" y1="2" x2="12" y2="22"/><line x1="2" y1="12" x2="22" y2="12"/></svg>
          Radar Ops
        </div>
        <div className="nav-item">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
          Live Traffic ({aircraftCount})
        </div>
        <div 
          className={`nav-item ${activeView === 'analytics' ? 'active' : ''}`}
          onClick={() => setActiveView('analytics')}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/><line x1="15" y1="15" x2="15" y2="21"/><line x1="15" y1="15" x2="21" y2="15"/></svg>
          Analytics
        </div>
      </div>
      
      <div className="sidebar-bottom">
        <div className="system-status-container">
          <div className="status-dot"></div>
          System Online
        </div>
      </div>
    </div>
  );
}
