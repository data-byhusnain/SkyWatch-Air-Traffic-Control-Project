# API Reference

The ATC Monitoring System provides both a standard REST API for one-off data fetching and a WebSocket (SocketIO) interface for realtime, low-latency updates.

## REST API Endpoints

All endpoints are prefixed with `/api` and return `application/json`.

### `GET /api/status`
Returns the current health and metrics of the backend engine.

**Response Schema:**
```json
{
  "status": "online",
  "aircraft_count": 45,
  "alert_count": 3,
  "simulation_running": true
}
```

### `GET /api/aircraft`
Returns a snapshot of all currently tracked aircraft in the region.

**Response Schema:**
```json
{
  "count": 45,
  "aircraft": [
    {
      "icao24": "3c6752",
      "callsign": "DLH1234",
      "latitude": 33.69,
      "longitude": 73.04,
      "altitude": 10500.0,
      "velocity": 250.5,
      "heading": 45.0,
      "vertical_rate": 0.0,
      "origin_country": "Germany",
      "alert_level": "GREEN",
      "source": "LIVE",
      "last_updated": "2024-05-09T14:30:00Z"
    }
  ]
}
```

### `GET /api/alerts`
Returns all active collision alerts (YELLOW or RED). Safe aircraft pairs (GREEN) are not included.

**Response Schema:**
```json
{
  "count": 1,
  "alerts": [
    {
      "aircraft_1": "3c6752",
      "aircraft_2": "a1b2c3",
      "distance_km": 4.5,
      "level": "RED",
      "timestamp": "2024-05-09T14:30:00Z"
    }
  ]
}
```

---

## WebSocket Interface (SocketIO)

Connect via a standard SocketIO client. The backend broadcasts updates every 1 second.

### Emitted Events (Server to Client)

#### `aircraft_update`
Emitted every 1 second. Contains the full state of all aircraft.
**Payload:**
```json
{
  "aircraft": [ ... array of aircraft objects ... ]
}
```

#### `alert_update`
Emitted every 1 second. Contains the full state of active alerts.
**Payload:**
```json
{
  "alerts": [ ... array of alert objects ... ]
}
```

#### `simulation_status`
Emitted every 1 second. Contains system status metrics.
**Payload:**
```json
{
  "running": true,
  "source": "LIVE",
  "aircraft_count": 45,
  "alert_count": 1,
  "red_alerts": 1,
  "yellow_alerts": 0
}
```

### Received Events (Client to Server)

#### `request_update`
Forces the backend to instantly emit an `aircraft_update` and `alert_update` cycle, ignoring the 1-second interval. Useful for instant client sync.
