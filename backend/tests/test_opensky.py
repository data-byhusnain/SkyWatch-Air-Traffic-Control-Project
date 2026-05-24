import unittest
from unittest.mock import patch, Mock
import requests
from app.services.opensky_service import fetch_aircraft

class TestOpenSkyService(unittest.TestCase):

    @patch('app.services.opensky_service.requests.get')
    def test_successful_fetch(self, mock_get):
        # Mock a successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "time": 1234567,
            "states": [
                ["111111", "CALL1", "Country", 123, 123, 70.0, 30.0, 10000.0, False, 250.0, 90.0, 0.0, None, 10000.0, "1234", False, 0]
            ]
        }
        mock_get.return_value = mock_response

        aircraft_list = fetch_aircraft()
        self.assertEqual(len(aircraft_list), 1)
        self.assertEqual(aircraft_list[0].icao24, "111111")
        self.assertEqual(aircraft_list[0].callsign, "CALL1")
        self.assertEqual(aircraft_list[0].latitude, 30.0)

    @patch('app.services.opensky_service.requests.get')
    def test_rate_limited(self, mock_get):
        # Mock 429 Too Many Requests
        mock_response = Mock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response

        aircraft_list = fetch_aircraft()
        self.assertEqual(len(aircraft_list), 0)

    @patch('app.services.opensky_service.requests.get')
    def test_timeout(self, mock_get):
        # Mock requests.exceptions.Timeout
        mock_get.side_effect = requests.exceptions.Timeout

        aircraft_list = fetch_aircraft()
        self.assertEqual(len(aircraft_list), 0)

    @patch('app.services.opensky_service.requests.get')
    def test_missing_lat_lon(self, mock_get):
        # Mock response where lat/lon is None
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "time": 1234567,
            "states": [
                ["111111", "CALL1", "Country", 123, 123, None, None, 10000.0, False, 250.0, 90.0, 0.0, None, 10000.0, "1234", False, 0]
            ]
        }
        mock_get.return_value = mock_response

        # Should skip aircraft with missing position data
        aircraft_list = fetch_aircraft()
        self.assertEqual(len(aircraft_list), 0)

if __name__ == '__main__':
    unittest.main()
