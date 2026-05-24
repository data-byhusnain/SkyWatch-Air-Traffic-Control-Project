import L from "leaflet";

const iconCache = {};

/**
 * Creates a custom Leaflet DivIcon for an airplane.
 * Uses inline SVG and applies rotation via CSS transform.
 * Heavily cached to prevent React-Leaflet from destroying and recreating DOM nodes every 1 second.
 */
export const createAirplaneIcon = (heading, alertLevel) => {
  const roundedHeading = Math.round((heading || 0) / 5) * 5;
  const safeAlertLevel = alertLevel || "GREEN";
  const cacheKey = `${roundedHeading}-${safeAlertLevel}`;

  if (iconCache[cacheKey]) {
    return iconCache[cacheKey];
  }

  let color = "#2563eb";
  if (safeAlertLevel === "YELLOW") {
    color = "#F59E0B";
  } else if (safeAlertLevel === "RED") {
    color = "#EF4444";
  }

  // A simple airplane SVG path
  const svg = `
    <svg width="20" height="20" viewBox="0 0 24 24" fill="${color}" xmlns="http://www.w3.org/2000/svg">
      <path d="M21,16V14L13,9V3.5C13,2.67 12.33,2 11.5,2C10.67,2 10,2.67 10,3.5V9L2,14V16L10,13.5V19L8,20.5V22L11.5,21L15,22V20.5L13,19V13.5L21,16Z" />
    </svg>
  `;

  const icon = L.divIcon({
    className: "custom-airplane-icon",
    html: `<div style="transform: rotate(${roundedHeading}deg); width: 20px; height: 20px;">${svg}</div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
    popupAnchor: [0, -10],
  });

  iconCache[cacheKey] = icon;
  return icon;
};
