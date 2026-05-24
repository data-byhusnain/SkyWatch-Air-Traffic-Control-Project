import unittest
from app.models.aircraft import Aircraft
from app.services.collision import (
    haversine_km,
    check_collisions,
    reset_alert_levels,
    DANGER_KM,
    WARNING_KM
)

class TestCollisionDetection(unittest.TestCase):
    
    def test_haversine_formula(self):
        # Known distance: Islamabad (33.69, 73.04) to Lahore (31.52, 74.35) is ~275 km
        dist = haversine_km(33.69, 73.04, 31.52, 74.35)
        self.assertAlmostEqual(dist, 275.0, delta=15.0)

        # Distance to itself should be 0
        dist_zero = haversine_km(30.0, 70.0, 30.0, 70.0)
        self.assertEqual(dist_zero, 0.0)

    def test_red_alert_threshold(self):
        # Distance < 5 km
        ac1 = Aircraft(icao24="1", callsign="A", latitude=30.0, longitude=70.0)
        ac2 = Aircraft(icao24="2", callsign="B", latitude=30.03, longitude=70.0) # ~3.3 km
        
        alerts = check_collisions([ac1, ac2])
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].level, "RED")
        self.assertEqual(ac1.alert_level, "RED")
        self.assertEqual(ac2.alert_level, "RED")

    def test_yellow_alert_threshold(self):
        # Distance between 5 and 10 km
        ac1 = Aircraft(icao24="1", callsign="A", latitude=30.0, longitude=70.0)
        ac2 = Aircraft(icao24="2", callsign="B", latitude=30.07, longitude=70.0) # ~7.8 km
        
        alerts = check_collisions([ac1, ac2])
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].level, "YELLOW")
        self.assertEqual(ac1.alert_level, "YELLOW")
        self.assertEqual(ac2.alert_level, "YELLOW")

    def test_green_safe_distance(self):
        # Distance > 10 km
        ac1 = Aircraft(icao24="1", callsign="A", latitude=30.0, longitude=70.0)
        ac2 = Aircraft(icao24="2", callsign="B", latitude=31.0, longitude=71.0) # ~146 km
        
        alerts = check_collisions([ac1, ac2])
        self.assertEqual(len(alerts), 0)
        self.assertEqual(ac1.alert_level, "GREEN")
        self.assertEqual(ac2.alert_level, "GREEN")

    def test_red_overrides_yellow(self):
        # ac1 is close to ac2 (RED) and far from ac3 (YELLOW)
        ac1 = Aircraft(icao24="1", callsign="A", latitude=30.0, longitude=70.0)
        ac2 = Aircraft(icao24="2", callsign="B", latitude=30.03, longitude=70.0) # RED to ac1
        ac3 = Aircraft(icao24="3", callsign="C", latitude=30.07, longitude=70.0) # YELLOW to ac1
        
        alerts = check_collisions([ac1, ac2, ac3])
        # Expected alerts: ac1-ac2 (RED), ac1-ac3 (YELLOW), ac2-ac3 (RED: ~4.4km)
        
        # ac1 should be RED because RED overrides YELLOW
        self.assertEqual(ac1.alert_level, "RED")

    def test_no_duplicate_alerts(self):
        # Ensure we only get 1 alert for a pair, not 2 (A->B and B->A)
        ac1 = Aircraft(icao24="1", callsign="A", latitude=30.0, longitude=70.0)
        ac2 = Aircraft(icao24="2", callsign="B", latitude=30.02, longitude=70.0) # ~2.2 km
        
        alerts = check_collisions([ac1, ac2])
        self.assertEqual(len(alerts), 1)

    def test_exact_boundary(self):
        # Exactly 5.0 km (or slightly below depending on float precision)
        # 0.04491 degrees lat is approx 4.9938 km
        ac1 = Aircraft(icao24="1", callsign="A", latitude=30.0, longitude=70.0)
        ac2 = Aircraft(icao24="2", callsign="B", latitude=30.04491, longitude=70.0) 
        
        dist = haversine_km(30.0, 70.0, 30.04491, 70.0)
        alerts = check_collisions([ac1, ac2])
        
        if dist < DANGER_KM:
            self.assertEqual(alerts[0].level, "RED")
        else:
            self.assertEqual(alerts[0].level, "YELLOW")

if __name__ == '__main__':
    unittest.main()
