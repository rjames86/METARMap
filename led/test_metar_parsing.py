#!/usr/bin/env python3
"""
Unit tests for metar_data.py parsing
Tests both XML and JSON API responses to ensure equivalent MetarInfo objects
"""

import unittest
from unittest.mock import patch, Mock
import datetime

# Import the actual metar_data module
from metar_data import MetarInfos

class TestMetarDataParsing(unittest.TestCase):
    """Test metar_data.py parsing with mock API responses"""
    
    def setUp(self):
        """Set up mock API response data and expected values for KSLC"""
        
        # Expected values that both APIs should produce
        self.expected_airport_code = 'KSLC'
        self.expected_flight_category = 'VFR'
        self.expected_temp_c = 30
        self.expected_dewpoint_c = 11  # Rounded from 10.6
        self.expected_wind_speed = 10
        self.expected_wind_dir = '350'
        self.expected_wind_gust_speed = 0
        self.expected_vis = 10
        self.expected_altim_hg = 30.04
        self.expected_latitude = 40.77
        self.expected_longitude = -111.97
        self.expected_obs_time = datetime.datetime(2025, 8, 25, 0, 54, 0, tzinfo=datetime.timezone.utc)
        self.expected_sky_conditions = [
            {'cover': 'FEW', 'cloudBaseFt': 8000},
            {'cover': 'SCT', 'cloudBaseFt': 14000},
            {'cover': 'BKN', 'cloudBaseFt': 25000}
        ]
        
        # Mock XML response from old API
        self.mock_xml_response = '''<?xml version="1.0" encoding="UTF-8"?>
<response>
  <data num_results="1">
    <METAR>
      <raw_text>KSLC 250054Z 35010KT 10SM FEW080 SCT140 BKN250 30/11 A3004</raw_text>
      <station_id>KSLC</station_id>
      <observation_time>2025-08-25T00:54:00Z</observation_time>
      <latitude>40.77</latitude>
      <longitude>-111.97</longitude>
      <temp_c>30.0</temp_c>
      <dewpoint_c>10.6</dewpoint_c>
      <wind_dir_degrees>350</wind_dir_degrees>
      <wind_speed_kt>10</wind_speed_kt>
      <visibility_statute_mi>10.0</visibility_statute_mi>
      <altim_in_hg>30.04</altim_in_hg>
      <flight_category>VFR</flight_category>
      <sky_condition sky_cover="FEW" cloud_base_ft_agl="8000" />
      <sky_condition sky_cover="SCT" cloud_base_ft_agl="14000" />
      <sky_condition sky_cover="BKN" cloud_base_ft_agl="25000" />
    </METAR>
  </data>
</response>'''
        
        # Mock JSON response from new API
        self.mock_json_response = [
            {
                "icaoId": "KSLC",
                "obsTime": 1756083240,  # 2025-08-25T00:54:00Z as Unix timestamp
                "temp": 30.0,
                "dewp": 10.6,
                "wdir": 350,
                "wspd": 10,
                "wgst": None,
                "visib": "10+",
                "altim": 1017.4,  # hectopascals (30.04 inHg * 33.8639)
                "wxString": None,
                "lat": 40.77,
                "lon": -111.97,
                "clouds": [
                    {"cover": "FEW", "base": 8000},
                    {"cover": "SCT", "base": 14000},
                    {"cover": "BKN", "base": 25000}
                ]
            }
        ]
    
    def test_xml_parsing(self):
        """Test that XML parsing works correctly"""
        result = MetarInfos.from_xml(self.mock_xml_response)
        
        self.assertIn('KSLC', result)
        kslc = result['KSLC']
        
        # Test all expected values
        self.assertEqual(kslc.airport_code, self.expected_airport_code)
        self.assertEqual(kslc.flightCategory, self.expected_flight_category)
        self.assertEqual(kslc.tempC, self.expected_temp_c)
        self.assertEqual(kslc.dewpointC, self.expected_dewpoint_c)
        self.assertEqual(kslc.windSpeed, self.expected_wind_speed)
        self.assertEqual(kslc.windDir, self.expected_wind_dir)
        self.assertEqual(kslc.windGustSpeed, self.expected_wind_gust_speed)
        self.assertEqual(kslc.vis, self.expected_vis)
        self.assertEqual(kslc.altimHg, self.expected_altim_hg)
        self.assertEqual(kslc.latitude, self.expected_latitude)
        self.assertEqual(kslc.longitude, self.expected_longitude)
        self.assertEqual(kslc.observation_time, self.expected_obs_time)
        
        # Test sky conditions
        self.assertEqual(len(kslc.skyConditions), len(self.expected_sky_conditions))
        for i, expected_cloud in enumerate(self.expected_sky_conditions):
            self.assertEqual(kslc.skyConditions[i]['cover'], expected_cloud['cover'])
            self.assertEqual(kslc.skyConditions[i]['cloudBaseFt'], expected_cloud['cloudBaseFt'])
    
    def test_json_parsing(self):
        """Test that JSON parsing produces same results as XML"""
        result = MetarInfos.from_json(self.mock_json_response)
        
        self.assertIn('KSLC', result)
        kslc = result['KSLC']
        
        # Test all expected values (same as XML test)
        self.assertEqual(kslc.airport_code, self.expected_airport_code)
        self.assertEqual(kslc.flightCategory, self.expected_flight_category)
        self.assertEqual(kslc.tempC, self.expected_temp_c)
        self.assertEqual(kslc.dewpointC, self.expected_dewpoint_c)
        self.assertEqual(kslc.windSpeed, self.expected_wind_speed)
        self.assertEqual(kslc.windDir, self.expected_wind_dir)
        self.assertEqual(kslc.windGustSpeed, self.expected_wind_gust_speed)
        self.assertEqual(kslc.vis, self.expected_vis)
        
        # Altimeter should be close (unit conversion)
        self.assertAlmostEqual(kslc.altimHg, self.expected_altim_hg, places=2)
        
        self.assertEqual(kslc.latitude, self.expected_latitude)
        self.assertEqual(kslc.longitude, self.expected_longitude)
        self.assertEqual(kslc.observation_time, self.expected_obs_time)
        
        # Test sky conditions
        self.assertEqual(len(kslc.skyConditions), len(self.expected_sky_conditions))
        for i, expected_cloud in enumerate(self.expected_sky_conditions):
            self.assertEqual(kslc.skyConditions[i]['cover'], expected_cloud['cover'])
            self.assertEqual(kslc.skyConditions[i]['cloudBaseFt'], expected_cloud['cloudBaseFt'])
    
    def test_flight_category_calculation(self):
        """Test flight category calculation logic"""
        # Test the _calculate_flight_category method for various scenarios
        # VFR: vis > 5, ceiling > 3000
        # MVFR: vis 3-5, ceiling 1000-3000  
        # IFR: vis 1-3, ceiling 500-1000
        # LIFR: vis < 1, ceiling < 500
        pass

if __name__ == '__main__':
    unittest.main(verbosity=2)