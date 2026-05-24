import unittest
from app.models.aircraft import Aircraft
from app.services.simulation import calculate_new_position

class TestSimulationEngine(unittest.TestCase):
    def update_position(self, ac: Aircraft):
        new_lat, new_lon, new_alt = calculate_new_position(
            latitude=ac.latitude,
            longitude=ac.longitude,
            altitude=ac.altitude,
            velocity=ac.velocity,
            heading=ac.heading,
            vertical_rate=ac.vertical_rate,
            time_delta=1.0
        )
        ac.latitude = new_lat
        ac.longitude = new_lon
        ac.altitude = new_alt

    def test_update_position_north(self):
        # Heading 0 is North -> Latitude should increase
        ac = Aircraft(icao24="1", callsign="A", latitude=30.0, longitude=70.0, velocity=250.0, heading=0.0)
        self.update_position(ac)
        self.assertGreater(ac.latitude, 30.0)
        self.assertEqual(ac.longitude, 70.0)

    def test_update_position_east(self):
        # Heading 90 is East -> Longitude should increase
        ac = Aircraft(icao24="1", callsign="A", latitude=30.0, longitude=70.0, velocity=250.0, heading=90.0)
        self.update_position(ac)
        self.assertEqual(ac.latitude, 30.0)
        self.assertGreater(ac.longitude, 70.0)

    def test_update_position_south(self):
        # Heading 180 is South -> Latitude should decrease
        ac = Aircraft(icao24="1", callsign="A", latitude=30.0, longitude=70.0, velocity=250.0, heading=180.0)
        self.update_position(ac)
        self.assertLess(ac.latitude, 30.0)
        self.assertAlmostEqual(ac.longitude, 70.0, places=5)

    def test_update_position_west(self):
        # Heading 270 is West -> Longitude should decrease
        ac = Aircraft(icao24="1", callsign="A", latitude=30.0, longitude=70.0, velocity=250.0, heading=270.0)
        self.update_position(ac)
        self.assertAlmostEqual(ac.latitude, 30.0, places=5)
        self.assertLess(ac.longitude, 70.0)

    def test_zero_velocity(self):
        # Zero velocity -> position should not change
        ac = Aircraft(icao24="1", callsign="A", latitude=30.0, longitude=70.0, velocity=0.0, heading=45.0)
        self.update_position(ac)
        self.assertEqual(ac.latitude, 30.0)
        self.assertEqual(ac.longitude, 70.0)

if __name__ == '__main__':
    unittest.main()
