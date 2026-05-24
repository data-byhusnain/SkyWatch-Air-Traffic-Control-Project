// ============================================================
// App.jsx -- Main Application Shell (Scrolling Website UI)
// ============================================================

import { useState, useRef } from "react";
import useSocket from "./hooks/useSocket";
import TopHeader from "./components/TopHeader/TopHeader";
import Footer from "./components/Footer/Footer";
import MapDisplay from "./components/MapDisplay/MapDisplay";
import AircraftList from "./components/AircraftList/AircraftList";
import SelectedAircraftCard from "./components/SelectedAircraftCard/SelectedAircraftCard";
import AlertBanner from "./components/AlertBanner/AlertBanner";
import AnalyticsDashboard from "./components/AnalyticsDashboard/AnalyticsDashboard";
import HeroSection from "./components/HeroSection/HeroSection";
import "./App.css";

export default function App() {
  // Activate WebSocket connection and event subscriptions.
  useSocket();
  const [activeView, setActiveView] = useState("radar");
  const radarRef = useRef(null);

  const scrollToRadar = () => {
    if (radarRef.current) {
      radarRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <>
      <TopHeader activeView={activeView} setActiveView={setActiveView} />
      
      {activeView === "radar" && (
        <HeroSection onLaunchRadar={scrollToRadar} />
      )}
      <main className="main-content">
        {activeView === "radar" ? (
            <>
              <div className="radar-layout" ref={radarRef} style={{ scrollMarginTop: '80px', marginTop: '60px' }}>
                <div className="map-section">
                  <MapDisplay />
                </div>
                <div className="data-section">
                  <SelectedAircraftCard />
                  <AircraftList />
                </div>
              </div>
              
              <div className="alerts-section" style={{ marginTop: '24px' }}>
                <AlertBanner />
              </div>
            </>
        ) : (
          <div className="analytics-section">
            <AnalyticsDashboard />
          </div>
        )}
      </main>

      <Footer setActiveView={setActiveView} />
    </>
  );
}
