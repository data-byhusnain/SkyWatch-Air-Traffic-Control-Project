// ============================================================
// main.jsx -- Application Entry Point
// ============================================================
//
// This is the first file that runs. It:
//   1. Imports the global CSS design system
//   2. Wraps <App /> with <AircraftProvider> (global state)
//   3. Renders everything into the #root DOM element
//
// React.StrictMode is intentionally left OFF to prevent
// double-mounting effects which would cause duplicate socket
// connections during development.
// ============================================================

import { createRoot } from "react-dom/client";
import { AircraftProvider } from "./context/AircraftContext";
import App from "./App";
import "./index.css";

createRoot(document.getElementById("root")).render(
  <AircraftProvider>
    <App />
  </AircraftProvider>
);
