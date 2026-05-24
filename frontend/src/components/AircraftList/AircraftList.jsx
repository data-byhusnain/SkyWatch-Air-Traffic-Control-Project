// ============================================================
// AircraftList.jsx -- Live updating aircraft data table
// ============================================================
import { useAircraft } from "../../context/AircraftContext";
import { METERS_TO_FEET, MS_TO_KNOTS } from "../../utils/constants";
import { COUNTRY_CODES } from "../../utils/countryCodes";
import "./AircraftList.css";

// Helper function to map country names to 2-letter ISO codes for FlagCDN
const getCountryCode = (countryName) => {
  if (!countryName || typeof countryName !== "string") return null;
  // Clean up the string for matching
  const cleanName = countryName.trim().toLowerCase();
  return COUNTRY_CODES[cleanName] || null;
};

export default function AircraftList() {
  const { aircraft, selectedAircraftId, setSelectedAircraftId } = useAircraft();

  // Mix countries by sorting via ICAO24 string alphabetically (gives a random-like but stable mix)
  // RED/YELLOW alerts still float to the top
  const sortedAircraft = [...aircraft].sort((a, b) => {
    const priority = { RED: 0, YELLOW: 1, GREEN: 2 };
    const pA = priority[a.alert_level] ?? 2;
    const pB = priority[b.alert_level] ?? 2;
    if (pA !== pB) return pA - pB;
    return a.icao24.localeCompare(b.icao24);
  });

  return (
    <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div className="card-header">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>
        Sector Traffic
      </div>
      
      <div style={{ overflowY: 'auto', flex: 1, padding: '0' }}>
        <table className="table" style={{ margin: 0 }}>
          <thead>
            <tr>
              <th>Flight</th>
              <th>Country</th>
              <th>Alt (ft)</th>
              <th>Spd (kts)</th>
              <th>Heading</th>
            </tr>
          </thead>
          <tbody>
            {sortedAircraft.map((ac) => {
              const level = (ac.alert_level || "GREEN").toUpperCase();
              const isSelected = ac.icao24 === selectedAircraftId;
              const isRed = level === "RED";
              
              let rowStyle = {};
              if (isSelected) rowStyle = { "--row-bg": "rgba(37, 99, 235, 0.14)" };
              else if (isRed) rowStyle = { "--row-bg": "rgba(239, 68, 68, 0.1)" };

              return (
                <tr 
                  key={ac.icao24} 
                  style={{ cursor: "pointer", ...rowStyle }}
                  onClick={() => setSelectedAircraftId(ac.icao24)}
                  title={ac.origin_country || "Unknown"}
                >
                  <td className="text-highlight" style={{ color: isRed ? 'var(--color-danger)' : '' }}>
                    {ac.callsign || ac.icao24.substring(0, 6).toUpperCase()}
                  </td>
                  <td style={{ textAlign: "center", width: "40px" }}>
                    {getCountryCode(ac.origin_country) ? (
                      <img 
                        src={`https://flagcdn.com/${getCountryCode(ac.origin_country)}.svg`} 
                        alt={ac.origin_country} 
                        style={{ width: "24px", height: "18px", borderRadius: "2px", boxShadow: "0 0 2px rgba(0,0,0,0.3)", objectFit: "cover" }} 
                      />
                    ) : (
                      <span style={{ fontSize: "10px", color: "var(--text-muted)" }}>{ac.origin_country ? ac.origin_country.substring(0, 3).toUpperCase() : "UNK"}</span>
                    )}
                  </td>
                  <td>{(ac.altitude * METERS_TO_FEET).toFixed(0)}</td>
                  <td>{(ac.velocity * MS_TO_KNOTS).toFixed(0)}</td>
                  <td>{ac.heading ? Math.round(ac.heading) + " deg" : "---"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {sortedAircraft.length === 0 && (
          <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)' }}>
            No traffic in sector
          </div>
        )}
      </div>
    </div>
  );
}
