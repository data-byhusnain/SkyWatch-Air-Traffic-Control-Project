// ============================================================
// src/services/socketService.js -- Socket.IO Client Singleton
// ============================================================
//
// PURPOSE:
//   Creates and exports a single socket.io-client instance.
//   Every module that needs the socket imports this same instance.
//
// WHY A SINGLETON?
//   Multiple socket connections to the same server would:
//   - Waste bandwidth (duplicate data streams)
//   - Cause event handler conflicts
//   - Confuse the Flask-SocketIO backend with multiple sessions
//
// HOW IT CONNECTS:
//   useSocket.js hook imports this and attaches event listeners.
//   The hook manages the lifecycle (connect on mount, cleanup on unmount).
// ============================================================

import { io } from "socket.io-client";
import {
  BACKEND_URL,
  SOCKET_RECONNECT_ATTEMPTS,
  SOCKET_RECONNECT_DELAY,
} from "../utils/constants";

// Create the singleton socket instance.
// autoConnect: false — we connect manually in useSocket hook
// so the connection lifecycle is tied to React's component lifecycle.
const socket = io(BACKEND_URL, {
  autoConnect: false,
  reconnection: true,
  reconnectionAttempts: SOCKET_RECONNECT_ATTEMPTS,
  reconnectionDelay: SOCKET_RECONNECT_DELAY,
  transports: ["websocket", "polling"], // Prefer WebSocket, fallback to polling
});

export default socket;
