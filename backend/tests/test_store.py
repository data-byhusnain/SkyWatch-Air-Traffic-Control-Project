import unittest
from app.models.aircraft import Aircraft, CollisionAlert
from app.store.state import AircraftStore

class TestAircraftStore(unittest.TestCase):
    def setUp(self):
        self.store = AircraftStore()
        # Reset the singleton before each test
        self.store._aircraft.clear()
        self.store._alerts.clear()

    def test_update_aircraft(self):
        ac = Aircraft(icao24="1", callsign="A", latitude=30.0, longitude=70.0)
        self.store.update_aircraft([ac])
        
        all_ac = self.store.get_all_aircraft()
        self.assertEqual(len(all_ac), 1)
        self.assertEqual(all_ac[0].icao24, "1")

    def test_overwrite_existing(self):
        ac1 = Aircraft(icao24="1", callsign="A", latitude=30.0, longitude=70.0, velocity=100)
        self.store.update_aircraft([ac1])
        
        # New update with same icao24 should overwrite
        ac2 = Aircraft(icao24="1", callsign="A", latitude=31.0, longitude=71.0, velocity=200)
        self.store.update_aircraft([ac2])
        
        all_ac = self.store.get_all_aircraft()
        self.assertEqual(len(all_ac), 1)
        self.assertEqual(all_ac[0].velocity, 200)
        self.assertEqual(all_ac[0].latitude, 31.0)

    def test_remove_stale_aircraft(self):
        import time
        ac = Aircraft(icao24="1", callsign="A", latitude=30.0, longitude=70.0)
        self.store.update_aircraft([ac])
        
        # Should not be removed if max_age_seconds is large
        self.store.remove_stale_aircraft(max_age_seconds=60)
        self.assertEqual(len(self.store.get_all_aircraft()), 1)
        
        # Simulate wait and remove with tiny max_age_seconds
        time.sleep(0.1)
        self.store.remove_stale_aircraft(max_age_seconds=0.05)
        self.assertEqual(len(self.store.get_all_aircraft()), 0)

    def test_update_alerts(self):
        alert1 = CollisionAlert(aircraft_1="1", aircraft_2="2", distance_km=4.0, level="RED")
        self.store.update_alerts([alert1])
        
        alerts = self.store.get_alerts()
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].level, "RED")

if __name__ == '__main__':
    unittest.main()
