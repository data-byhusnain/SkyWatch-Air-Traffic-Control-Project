import { useAircraft } from "../../context/AircraftContext";
import { MS_TO_KNOTS, METERS_TO_FEET } from "../../utils/constants";
import "./SelectedAircraftCard.css";

export default function SelectedAircraftCard() {
  const { aircraft, selectedAircraftId, setSelectedAircraftId } = useAircraft();

  if (!selectedAircraftId) return null;

  const ac = aircraft.find(a => a.icao24 === selectedAircraftId);
  if (!ac) return null;

  return (
    <div className="card">
      <div className="card-header">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
        Active Selection
        <button className="sac-close-btn" onClick={() => setSelectedAircraftId(null)} aria-label="Clear selected aircraft">x</button>
      </div>
      
      <div className="data-row"><span className="data-label">Callsign</span><span className="data-value">{ac.callsign || "UNKNOWN"}</span></div>
      <div className="data-row"><span className="data-label">Type</span><span className="data-value">{ac.icao24}</span></div>
      <div className="data-row"><span className="data-label">Altitude</span><span className="data-value">{Math.round(ac.altitude * METERS_TO_FEET)} ft</span></div>
      <div className="data-row"><span className="data-label">Ground Speed</span><span className="data-value">{Math.round(ac.velocity * MS_TO_KNOTS)} kts</span></div>
      <div className="data-row"><span className="data-label">Heading</span><span className="data-value">{ac.heading ? Math.round(ac.heading) + " deg" : "N/A"}</span></div>
    </div>
  );
}
