# Academic Viva Preparation

This guide contains common viva/defense questions regarding the system's architecture and technical decisions, paired with concise, technical answers.

## General Architecture

**Q: Why did you use Flask-SocketIO instead of plain HTTP requests or long-polling?**
**A:** Air traffic monitoring requires low-latency, bidirectional communication. Long-polling introduces too much HTTP overhead (headers, handshakes) every second. WebSockets maintain a persistent TCP connection, allowing the server to push the 5KB state snapshots every second with minimal overhead, achieving true real-time performance.

**Q: Why use a geographic mapping library (React-Leaflet) instead of an abstract plotting canvas?**
**A:** While an abstract radar canvas is performant, real-world air traffic control relies heavily on geographic context (borders, terrain, cities). React-Leaflet allows us to render exact latitude/longitude coordinates over a real map projection (Web Mercator). We applied custom CSS filters to the map tiles to maintain the dark, high-contrast HUD aesthetic required for an operational dashboard, while providing full panning and zooming capabilities.

## Concurrency and Threading

**Q: Why use Python `threading`? Doesn't the Global Interpreter Lock (GIL) prevent true parallelism?**
**A:** The GIL prevents multiple threads from executing Python bytecodes simultaneously. However, our OpenSky API thread is heavily I/O bound (waiting on network responses). The GIL is released during I/O operations, allowing the simulation and broadcasting threads to continue running seamlessly. Furthermore, we used Eventlet monkey-patching to enable asynchronous green-threads, drastically improving socket performance.

**Q: How did you prevent race conditions between the OpenSky poller, the simulation engine, and the broadcaster?**
**A:** We implemented the "Shared Memory" pattern via a centralized `AircraftStore` singleton. We wrapped the internal dictionary in a `threading.Lock`. Any thread attempting to read or write aircraft data must acquire this lock, ensuring atomic operations and preventing dirty reads. Furthermore, read operations return frozen `list()` copies (snapshots) so the caller can iterate safely.

## Mathematics and Algorithms

**Q: Why use the Haversine formula instead of Euclidean distance (`x^2 + y^2`) for collision detection?**
**A:** The Earth is a sphere, not a flat grid. Lines of longitude converge at the poles. Therefore, 1 degree of longitude at the equator is ~111km, but at 60 degrees North, it is only ~55km. Euclidean math would drastically over-calculate east-west distances at higher latitudes, resulting in false alerts or missed collisions. The Haversine formula correctly calculates the great-circle distance over the Earth's curvature.

**Q: Your collision detection is O(n^2). Isn't that inefficient?**
**A:** In algorithmic theory, yes. However, in our system, `N` (the number of aircraft in a regional bounding box) rarely exceeds 100. `100 * 99 / 2 = 4,950` operations. As demonstrated by our load tests, Python computes 4,950 Haversine distances in under 5 milliseconds. Given our 1.0 second broadcast window, `O(n^2)` is completely acceptable and avoids the unnecessary complexity of implementing spatial indexing like KD-Trees.

## Academic Positioning

This project successfully demonstrates several core computer science concepts:
1. **Parallel/Distributed Computing:** Managing multiple concurrent threads (Sim, I/O, WebSockets) with safe lock mechanisms.
2. **Realtime Systems:** Strict 1.0s deadlines for broadcast updates and 60 FPS deadlines for frontend rendering.
3. **Simulation Physics:** Velocity vector decomposition and dead-reckoning extrapolation.
4. **Networking:** Decoupling REST APIs (OpenSky) from internal WebSocket streams (SocketIO).
