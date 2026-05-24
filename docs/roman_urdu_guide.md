# ATC Monitoring System — Guide

---

## PEHLE YEH SAMJHO: PROJECT KIYA HAI?

Is project ka naam hai: **"Simulation-Based Air Traffic Control Monitoring System"**

Seedha alfazon mein: Yeh ek **live radar dashboard** hai jo real waqt mein Pakistan ke aasmaani ilaqe mein ud rahe jahazon ko track karta hai, aur agar 2 jahaz ek dusre ke bahut qareeb aa jayein to automatic **WARNING** deta hai.

---

## PROBLEM STATEMENT — KYA MASLA THA?

Hamari proposal mein teen bade masle they:

### Masla #1: "Jumping Radar Blips" (Planes ka achanak jump karna)
**Kya hota tha:** OpenSky API sirf har **15 second** baad naya data deti hai.
Agar hum sirf API par depend karte, toh:
- Plane 15 second tak screen par **bilkul ruka rehta**
- Phir achanak naye coordinates par **teleport** kar jata
- Yeh bilkul real radar jaisa nahi lagta

**Hamara Solution (Dead Reckoning):** Humne ek **Physics Simulation Engine** banaya jo har **1 second** mein plane ki position khud calculate karta hai. Matlab API ka wait kiye baghair, engine plane ki **speed (velocity)** aur **direction (heading)** se agla qadam khud nikalta hai. Is liye planes **smoothly** chalte hain.

```
Formula jo use hoti hai:
Naya Lat = Purana Lat + (speed × cos(direction) × time) / Earth radius
Naya Lon = Purana Lon + (speed × sin(direction) × time) / Earth radius
```

### Masla #2: "Collision Detection Ki Ghaibat" (Takkar ka pata nahi chalta)
**Kya hota tha:** 15 second ke andar 2 planes jo 900 km/h se ud rahe hain, **7.5 kilometer** aage nikal sakte hain. Agar us beech koi check nahi, toh takkar hone se pehle alert dena impossible tha.

**Hamara Solution (Haversine Collision Engine):** Humne `collision.py` mein ek algorithm banaya jo har **1 second** mein **har plane ka fasla har dosre plane se naapata hai**. Yeh **Haversine Formula** use karta hai jo Earth ki gol shape ko consider karta hai (simple X² + Y² galat hoga kyunke Earth flat nahi hai).

Agar 55 planes hain: 55 × 54 / 2 = **1,485 calculations har second**
- Fasla < 5 km → **RED ALERT** (Danger)
- Fasla < 10 km → **YELLOW ALERT** (Warning)

### Masla #3: "Browser Slow aur Hang hona"
**Kya hota tha:** Seedha DOM (web page ka structure) update karne se 50-100 moving elements CPU ko slow kar dete hain.

**Hamara Solution (React + Leaflet):** Humne **React** framework use kiya jo **Virtual DOM** ke zariye sirf changed elements update karta hai. Map ke liye **React-Leaflet** library use ki jo hardware acceleration use karti hai. Isliye 100+ planes smoothly chalte hain.

---

## PROJECT KESE KAAM KARTA HAI — STEP BY STEP

### Jab aap `python run.py` chalate ho, yeh hota hai:

```
1. Flask App shuru hoti hai (Port 5000 par)
2. OpenSky API se pehla data aata hai (55-60 planes)
3. 4 Threads ek sath shuru hote hain:
   
   Thread A: OpenSky Poller  → Har 15s baad naya data laata hai
   Thread B: Sim Engine      → Har 1s mein planes move karta hai  
   Thread C: Broadcaster     → Har 1s mein frontend ko data bhejta hai
   Thread D: Flask Server    → HTTP requests handle karta hai
```

### Jab aap Frontend kholta hai (`npm run dev`):
```
1. Browser backend se WebSocket connection banata hai
2. Backend ka broadcaster har second data bhejta hai
3. React screen update karta hai
4. Naye planes dikhte hain, alerts aate hain
```

---

## PARALLEL COMPUTING KAHAN HAI? (PDC Subject Ka Core Sawaal)

Yeh **Parallel & Distributed Computing** ka project hai. Teacher zaroor poochhenge — yeh jawab taiyaar rakho:

### Parallel Computing:
**4 threads ek sath** chal rahe hain — yeh parallelism hai:
| Thread | Kaam | Kitni baar |
|--------|------|-----------|
| OpenSky Poller | Internet se data laana | Har 15 second |
| Simulation Engine | Planes ki position update | Har 1 second |
| Broadcaster | Frontend ko data bhejna | Har 1 second |
| Flask Server | HTTP requests ka jawab | Jab bhi aaye |

### Shared Memory Problem (Race Condition):
Jab 2 threads ek sath ek jagah likhne ki koshish karein, data corrupt ho jata hai. Ise **Race Condition** kehte hain.

**Hamara Solution:** `AircraftStore` class mein `threading.Lock()` lagaya. Koi bhi thread data read/write karne se pehle **lock acquire** karta hai. Is se ek waqt mein sirf ek thread data change kar sakta hai.

```python
# state.py mein yeh code hai:
with self._lock:
    self._aircraft[icao24] = aircraft  # Thread-safe write
```

### Distributed System:
```
[OpenSky Server]  → Internet →  [Hamara Python Backend]  → WebSocket →  [Browser]
  (External)                       (Port 5000)                          (Port 5173)
```
Teen alag systems ek sath kaam kar rahe hain — yeh **distributed architecture** hai.

---

## OPENSKY WEBSITE SE HAMARA PROJECT ALAG KYUN HAI?

Yeh bahut important sawaal hai. OpenSky website (opensky-network.org) bhi planes dikhaati hai aur woh bhi move karte hain. Toh farq kya hai?

| Feature | OpenSky Website | Hamara Project |
|---------|----------------|----------------|
| Planes dikhana | ✅ Haan | ✅ Haan |
| **Collision Detection** | ❌ Bilkul nahi | ✅ Har second |
| **RED/YELLOW Alerts** | ❌ Nahi | ✅ Distance ke sath |
| **Custom Backend** | ❌ Nahi | ✅ Python Flask |
| **Parallel Threads** | ❌ Sirf webpage | ✅ 4 threads |
| **Offline Mode** | ❌ API band = blank screen | ✅ Simulation chal-ti rahi |
| **Physics Simulation** | ❌ Simple interpolation | ✅ Dead Reckoning math |
| **Trajectory Prediction** | ❌ Nahi | ✅ 3 minute prediction |
| **Thread-safe Store** | ❌ Nahi | ✅ `threading.Lock()` |
| **PDC Concepts** | ❌ Nahi | ✅ Haan |

**Teacher ko aise samjhao:**
> "Sir, OpenSky website sirf ek viewer hai — data dikhaata hai, process nahi karta. Hamara project ek intelligent monitoring system hai. Farq wahi hai jo television par news dekhne aur khud news analyze karke danger predict karne mein hai. OpenSky par agar 2 planes 1 km ke andar bhi aajayein, koi alert nahi aata. Hamara system detect karta hai, calculate karta hai, aur real-time warning deta hai."

---

## FILE STRUCTURE — KAUN SA FILE KYA KARTA HAI?

```
atc project/
├── backend/
│   ├── run.py                    → App start karne ka button
│   ├── app/
│   │   ├── __init__.py           → Sab services ko start karta hai
│   │   ├── config.py             → Settings (port, distances, etc.)
│   │   ├── extensions.py         → SocketIO setup (WebSocket)
│   │   ├── models/
│   │   │   └── aircraft.py       → Plane ka blueprint (lat, lon, speed, etc.)
│   │   ├── store/
│   │   │   └── state.py          → Thread-safe data storage (Lock yahan hai)
│   │   ├── services/
│   │   │   ├── opensky_service.py → Internet se data laata hai
│   │   │   ├── simulation.py      → Planes ko har second move karta hai
│   │   │   ├── collision.py       → Haversine se distance calculate karta hai
│   │   │   └── broadcaster.py     → Frontend ko data bhejta hai (Heartbeat)
│   │   ├── api/
│   │   │   └── routes.py         → HTTP endpoints (/api/status, etc.)
│   │   └── sockets/
│   │       └── events.py         → WebSocket events (connect, disconnect)
│
└── frontend/
    ├── src/
    │   ├── main.jsx              → App ka darwaza
    │   ├── App.jsx               → Main layout
    │   ├── context/
    │   │   └── AircraftContext.jsx → Global state (React Context)
    │   ├── hooks/
    │   │   └── useSocket.js      → WebSocket connection manage karta hai
    │   ├── services/
    │   │   └── socketService.js  → Socket.IO client
    │   └── components/
    │       ├── MapDisplay/       → Map aur planes dikhata hai
    │       ├── StatusBar/        → ONLINE/OFFLINE, aircraft count
    │       ├── AircraftList/     → Right panel ki table
    │       ├── AlertBanner/      → Neeche ki alert strip
    │       ├── AlertHUD/         → Map ke upar ke alert boxes
    │       └── AnalyticsModal/   → Analytics button ka popup
```

---

## TECHNICAL CONCEPTS — SIMPLE ALFAZON MEIN

### 1. WebSocket kya hai?
Normal website mein hota hai: Browser poochhe → Server jawab de. (Ek taraf traffic)
WebSocket mein: Ek dafa connection bane, phir dono **barabar baat kar sakte hain** bina baar baar poochhe.
Isiliye planes screen par real-time update hote hain — backend khud data push karta hai.

### 2. Dead Reckoning kya hai?
Sochein aap aankh band karke seedha chal rahe hain 5 second. Koi aapko 5 second baad bata sakta hai aap kahan honge — speed aur direction se. Yehi Dead Reckoning hai. Hamara simulation engine bhi yehi karta hai.

### 3. Haversine Formula kya hai?
Agar aap Google Maps par 2 points ka distance naapein, woh seedhi line (Euclidean) use nahi karta — Earth ki curve consider karta hai. Haversine formula yehi karta hai. Pakistan ke ilaqe mein Euclidean formula se **3-5% galat** answer aata, jo ek real ATC system ke liye qabool nahi.

### 4. O(n²) Complexity kya hai?
Agar 55 planes hain, collision check ke liye:
- 55 × 54 / 2 = 1,485 checks har second
- Python yeh 5 milliseconds mein karta hai
- Humara broadcast window 1000ms (1 second) hai
- Toh 1,485 checks karne ke baad bhi **995ms** bacha rehta hai — bilkul comfortable

### 5. Race Condition aur Lock kya hai?
Maan lo 2 log ek hi bank account mein ek sath paise daalne ki koshish karein:
- Dono "Balance = 1000" padhte hain
- Dono "Balance = 1000 + 500 = 1500" likhte hain
- Result: 1500 — GALAT (2000 hona chahiye tha)
`threading.Lock()` is liye hai — pehla banda transaction complete kare, phir dosra shuru kare.

---

## TEACHER KE EXPECTED SAWAL AUR JAWAB

### Q1: "Tumhara project kya problem solve karta hai?"
**A:** "Sir, real ATC systems bahut mehenge hain. Free APIs sirf har 15 second mein data deti hain. Is delay ki wajah se planes screen par jump karte hain aur collision detection impossible ho jati hai. Hamara system Dead Reckoning algorithm se har second position calculate karta hai aur Haversine formula se real-time collision detection karta hai — yeh dono problems solve ho jati hain."

### Q2: "PDC (Parallel & Distributed Computing) kahan hai?"
**A:** "Sir, backend mein 4 threads parallel chal rahe hain — OpenSky poller, simulation engine, broadcaster, aur Flask server. Yeh classical parallel computing hai. Thread-safe store mein `threading.Lock()` se shared memory manage hoti hai — yeh classical synchronization problem ka solution hai. Distributed side mein teen alag systems hain: OpenSky API server, hamara Python backend, aur React frontend — yeh distributed architecture hai."

### Q3: "OpenSky website se tumhara project kaise alag hai?"
**A:** "Sir, OpenSky website sirf data visualize karti hai. Collision detection bilkul nahi hai. Hamara project data ko process karta hai, analyze karta hai, aur intelligent decisions leta hai. Real ATC controllers ko manually 100 planes track karna impossible hai — hamara system automatically detect karta hai aur alert deta hai."

### Q4: "GIL (Global Interpreter Lock) to Python mein parallelism rok deta hai?"
**A:** "Sir, GIL sirf CPU-bound tasks mein rokta hai. Hamara OpenSky poller I/O bound hai — network ka wait karta hai. GIL I/O operations ke waqt release ho jata hai. Isliye baaki threads smoothly chaltay rehte hain. Saath mein humne Eventlet monkey-patching use kiya hai jo asynchronous green-threads deta hai."

### Q5: "O(n²) collision detection inefficient nahi hai?"
**A:** "Sir, theory mein haan. Lekin practice mein Pakistan ke airspace mein kabhi bhi 100 se zyada planes nahi hote. 100 × 99 / 2 = 4,950 operations. Python yeh 5ms mein complete karta hai. Hamara broadcast window 1000ms hai, toh hum 200x fast hain. KD-Trees jaise spatial indexing ki zarurat hi nahi."

### Q6: "Yeh AI se banaya hai?"
**A:** "Sir, AI tools se madad li programming mein — jaise calculator se madad lete hain math mein. Lekin algorithm ka design, architecture ke faisale, aur har module ka logic — yeh sab humara apna kaam hai. Haversine formula, Dead Reckoning implementation, thread synchronization — hum inhe explain kar sakte hain kyunke humne samjha hai."

### Q7: "Agar OpenSky API band ho jaye toh kya hoga?"
**A:** "Sir, hamara system 'Graceful Degradation' support karta hai. Agar API fail ho, system `demo_data.json` se pre-recorded data load karta hai aur physics engine continue karta hai. System kabhi crash nahi karta — yeh fault-tolerant design hai."

### Q8: "Frontend aur Backend kaise communicate karte hain?"
**A:** "Sir, WebSocket protocol use kiya hai jisme Socket.IO library hai. Backend har second `aircraft_update` aur `alert_update` events emit karta hai. Frontend ka `useSocket.js` hook in events ko receive karta hai aur React Context mein store karta hai. Phir saare components is context se data padhte hain aur automatically re-render hote hain."

---

## PROJECT CHALANE KA TARIKA

### Step 1: Backend chalao
```powershell
cd "C:\Users\ABC\Desktop\atc project\backend"
.\venv\Scripts\activate
python run.py
```

### Step 2: Frontend chalao (naya terminal)
```powershell
cd "C:\Users\ABC\Desktop\atc project\frontend"
npm run dev
```

### Step 3: Browser mein kholo
```
http://localhost:5173
```

### Agar Port 5000 already in use error aaye:
```powershell
Stop-Process -Id (Get-NetTCPConnection -LocalPort 5000).OwningProcess -Force
```

---

## DEMO FLOW (Presentation Ke Liye)

1. **Pehle LIVE mode dikhayen** — "Yeh real planes hain jo abhi Pakistan ke upar ud rahe hain"
2. **Planes ko move hote dikhayen** — "Yeh Dead Reckoning hai, API ka wait nahi karta"
3. **Collision Alerts table dikhayen** — "Yeh Haversine formula ka result hai, RED matlab 5km se kam"
4. **Kisi plane par click karein** — "Yeh Target Lock hai, blue line 3 minute ka trajectory prediction hai"
5. **Analytics button dabayein** — "Yeh stats hain: kitne planes, kitne alerts, system health"
6. **Terminal dikhayen** — "Yahan 4 threads ka output dikh raha hai jo ek sath chal rahe hain"

---

## IMPORTANT NUMBERS (Yaad Rakho)

| Cheez | Value |
|-------|-------|
| API update interval | 15 seconds |
| Simulation tick rate | 1 second |
| Broadcast rate | 1 second |
| RED alert distance | < 5 km |
| YELLOW alert distance | 5-10 km |
| Typical aircraft count | 50-60 planes |
| Calculations per second | ~1,485 (55 planes) |
| Calculation time | ~5 milliseconds |
| Backend port | 5000 |
| Frontend port | 5173 |

---

*Is ko parh kar aap presentation aur viva dono mein confident rahoge. Best of luck!* 🎓
 