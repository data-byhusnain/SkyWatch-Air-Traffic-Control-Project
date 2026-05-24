import { useEffect, useRef, useState } from "react";
import { MapContainer, TileLayer, Marker, Polyline, Tooltip, CircleMarker } from "react-leaflet";
import "leaflet/dist/leaflet.css"; // Moved here to ensure Vite bundles it
import { useAircraft } from "../../context/AircraftContext";
import { createAirplaneIcon } from "./AirplaneIcon";
import "./MapDisplay.css";

export default function MapDisplay() {
  const { aircraft, alerts, selectedAircraftId, setSelectedAircraftId } = useAircraft();
  const mapRef = useRef(null);
  
  const [hoveredAircraftId, setHoveredAircraftId] = useState(null);
  const hoverTimeoutRef = useRef(null);

  // Default center (Pakistan region)
  const defaultCenter = [30.0, 70.0];
  const defaultZoom = 5;

  const handleMouseOver = (icao24) => {
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
    }
    setHoveredAircraftId(icao24);
  };

  const handleMouseOut = () => {
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
    }
    hoverTimeoutRef.current = setTimeout(() => {
      setHoveredAircraftId(null);
    }, 5000);
  };

  useEffect(() => {
    return () => {
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current);
      }
    };
  }, []);

  return (
    <div className="map-container-wrapper" style={{ flex: 1, position: 'relative', height: '100%' }}>
      <MapContainer
        center={defaultCenter}
        zoom={defaultZoom}
        className="map-root"
        ref={mapRef}
      >
        {/* CartoDB Dark Matter for dark theme */}
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://carto.com/">CartoDB</a>'
        />

        {/* Draw Collision Alert Lines */}
        {alerts.map((alert, idx) => {
          const ac1 = aircraft.find(a => a.icao24 === alert.aircraft_1);
          const ac2 = aircraft.find(a => a.icao24 === alert.aircraft_2);
          if (!ac1 || !ac2) return null;

          const color = alert.level === "RED" ? "var(--color-danger)" : "var(--color-warn)";
          const weight = alert.level === "RED" ? 3 : 2;
          const dashArray = alert.level === "RED" ? "5, 5" : null;

          return (
            <Polyline
              key={`alert-${idx}`}
              positions={[
                [ac1.latitude, ac1.longitude],
                [ac2.latitude, ac2.longitude],
              ]}
              color={color}
              weight={weight}
              dashArray={dashArray}
              opacity={0.8}
            />
          );
        })}

        {/* Draw Aircraft Markers */}
        {aircraft.map((ac) => {
          const isSelected = ac.icao24 === selectedAircraftId;
          const icon = createAirplaneIcon(ac.heading, ac.alert_level);
          const isHovered = ac.icao24 === hoveredAircraftId;

          return (
            <Marker
              key={ac.icao24}
              position={[ac.latitude, ac.longitude]}
              icon={icon}
              eventHandlers={{
                click: () => setSelectedAircraftId(ac.icao24),
                mouseover: () => handleMouseOver(ac.icao24),
                mouseout: () => handleMouseOut()
              }}
            >
              {(isHovered || isSelected) && (
                <Tooltip permanent direction="top" offset={[0, -10]} className="aircraft-tooltip">
                  <div style={{ textAlign: 'center', fontFamily: 'var(--font-mono)', fontWeight: 'bold', color: 'var(--color-dark)' }}>
                    <div>{ac.callsign || ac.icao24}</div>
                    <div style={{ fontSize: '0.9em', color: 'var(--text-muted)' }}>
                      {Math.round(ac.altitude * 3.28084)} FT | {Math.round(ac.velocity * 1.94384)} KTS
                    </div>
                  </div>
                </Tooltip>
              )}
            </Marker>
          );
        })}

        {/* Draw Trajectory Line & Waypoints for Selected Aircraft */}
        {selectedAircraftId && aircraft.find(a => a.icao24 === selectedAircraftId) && (
          (() => {
            const ac = aircraft.find(a => a.icao24 === selectedAircraftId);
            if (!ac.heading || !ac.velocity) return null;

            const waypoints = [];
            const METERS_PER_DEGREE_LAT = 111320.0;
            const headingRad = ac.heading * (Math.PI / 180);

            // 5-minute trajectory with 1-minute interval waypoints
            for (let min = 1; min <= 5; min++) {
              const distanceMeters = ac.velocity * (min * 60);
              const deltaLat = (distanceMeters * Math.cos(headingRad)) / METERS_PER_DEGREE_LAT;
              const deltaLon = (distanceMeters * Math.sin(headingRad)) / (METERS_PER_DEGREE_LAT * Math.cos(ac.latitude * (Math.PI / 180)));
              waypoints.push([ac.latitude + deltaLat, ac.longitude + deltaLon]);
            }

            return (
              <>
                <Polyline
                  positions={[[ac.latitude, ac.longitude], ...waypoints]}
                  color="var(--color-primary)"
                  weight={2}
                  opacity={0.8}
                />
              </>
            );
          })()
        )}
      </MapContainer>
    </div>
  );
}
