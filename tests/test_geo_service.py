from traceroute_visualizer.services.geo_service import GeoService


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload


class FakeCache:
    def __init__(self):
        self.data = {}

    def get(self, namespace, key):
        return self.data.get((namespace, key))

    def set(self, namespace, key, value):
        self.data[(namespace, key)] = value


def test_geo_service_cache_hit(monkeypatch):
    cache = FakeCache()
    service = GeoService(cache=cache, timeout_seconds=1, retries=0)

    calls = {"count": 0}

    def fake_get(*args, **kwargs):
        calls["count"] += 1
        if "ip-api" in args[0]:
            return FakeResponse(
                {
                    "status": "success",
                    "city": "Paris",
                    "country": "France",
                    "lat": 48.8,
                    "lon": 2.3,
                    "isp": "ISP",
                    "as": "AS1",
                }
            )
        return FakeResponse({"address": {"city": "Paris", "country": "France"}})

    monkeypatch.setattr(service.session, "get", fake_get)

    first = service.lookup_ip("8.8.8.8")
    second = service.lookup_ip("8.8.8.8")
    assert first["city"] == "Paris"
    assert second["city"] == "Paris"
    assert calls["count"] == 2
