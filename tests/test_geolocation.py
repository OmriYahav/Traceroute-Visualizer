import sys
import types
import unittest
from unittest.mock import patch, MagicMock

# Stub modules that are not installed in the testing environment
# requests
if 'requests' not in sys.modules:
    requests_stub = types.ModuleType('requests')
    requests_stub.get = MagicMock()
    exc = types.SimpleNamespace(HTTPError=Exception, RequestException=Exception)
    requests_stub.exceptions = exc
    sys.modules['requests'] = requests_stub

# scapy.layers.inet
if 'scapy' not in sys.modules:
    scapy = types.ModuleType('scapy')
    layers = types.ModuleType('scapy.layers')
    inet = types.ModuleType('scapy.layers.inet')
    inet.IP = object
    inet.ICMP = object
    def traceroute(*args, **kwargs):
        return [], []
    inet.traceroute = traceroute
    sys.modules['scapy'] = scapy
    sys.modules['scapy.layers'] = layers
    sys.modules['scapy.layers.inet'] = inet

# geopy.geocoders.Nominatim
if 'geopy' not in sys.modules:
    geopy = types.ModuleType('geopy')
    geocoders = types.ModuleType('geopy.geocoders')
    class DummyNominatim:
        def __init__(self, *args, **kwargs):
            pass
        def reverse(self, *args, **kwargs):
            return MagicMock(address='dummy')
    geocoders.Nominatim = DummyNominatim
    sys.modules['geopy'] = geopy
    sys.modules['geopy.geocoders'] = geocoders

# folium
if 'folium' not in sys.modules:
    folium = types.ModuleType('folium')
    folium.Map = MagicMock
    folium.Marker = MagicMock
    folium.PolyLine = MagicMock
    sys.modules['folium'] = folium

# flask
if 'flask' not in sys.modules:
    flask = types.ModuleType('flask')
    class DummyFlask:
        def __init__(self, *args, **kwargs):
            pass
        def route(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
        def run(self, *args, **kwargs):
            pass
    flask.Flask = DummyFlask
    flask.render_template = MagicMock(return_value="")
    flask.request = MagicMock()
    sys.modules['flask'] = flask

from traceRouteV2 import get_location_data
import requests


class TestGetLocationData(unittest.TestCase):
    @patch('traceRouteV2.Nominatim')
    @patch('traceRouteV2.requests.get')
    def test_get_location_data_success(self, mock_get, mock_nominatim):
        mock_response = MagicMock()
        mock_response.json.return_value = {'lat': 1.23, 'lon': 4.56}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        mock_geo = MagicMock()
        mock_geo.reverse.return_value = MagicMock(address='Mock Address')
        mock_nominatim.return_value = mock_geo

        result = get_location_data('8.8.8.8')
        self.assertEqual(result, ('Mock Address', 1.23, 4.56))

    @patch('traceRouteV2.Nominatim')
    @patch('traceRouteV2.requests.get')
    def test_get_location_data_http_error(self, mock_get, mock_nominatim):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError('boom')
        mock_get.return_value = mock_response
        result = get_location_data('8.8.8.8')
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
