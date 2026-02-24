from __future__ import annotations

import ipaddress
import logging
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from traceroute_visualizer.services.cache import SQLiteTTLCache, SimpleRateLimiter

logger = logging.getLogger(__name__)


class GeoService:
    def __init__(
        self,
        cache: SQLiteTTLCache,
        timeout_seconds: float,
        retries: int,
        rate_limit_seconds: float = 0.2,
    ) -> None:
        self.cache = cache
        self.timeout_seconds = timeout_seconds
        self.rate_limiter = SimpleRateLimiter(rate_limit_seconds)
        retry = Retry(
            total=retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            raise_on_status=False,
        )
        self.session = requests.Session()
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def lookup_ip(self, ip: str) -> dict[str, Any]:
        ip_obj = ipaddress.ip_address(ip)
        if (
            ip_obj.is_private
            or ip_obj.is_loopback
            or ip_obj.is_reserved
            or ip_obj.is_multicast
        ):
            return {
                "ip": ip,
                "city": "Private",
                "country": "N/A",
                "isp": "N/A",
                "asn": "N/A",
                "lat": None,
                "lon": None,
                "status": "private",
            }

        cached = self.cache.get("ip_api", ip)
        if cached:
            return cached

        self.rate_limiter.wait()
        response = self.session.get(
            f"https://ip-api.com/json/{ip}",
            params={
                "fields": "status,message,country,city,lat,lon,isp,as,asname,query"
            },
            timeout=self.timeout_seconds,
        )
        data = response.json()
        if data.get("status") != "success":
            logger.warning("ip-api lookup failed", extra={"ip": ip, "response": data})
            result = {
                "ip": ip,
                "city": "Unknown",
                "country": "Unknown",
                "isp": "Unknown",
                "asn": "Unknown",
                "lat": None,
                "lon": None,
                "status": "unknown",
            }
            self.cache.set("ip_api", ip, result)
            return result

        lat = data.get("lat")
        lon = data.get("lon")
        location = (
            self.reverse_geocode(lat, lon)
            if lat is not None and lon is not None
            else {}
        )
        result = {
            "ip": ip,
            "city": location.get("city") or data.get("city") or "Unknown",
            "country": location.get("country") or data.get("country") or "Unknown",
            "isp": data.get("isp") or "Unknown",
            "asn": data.get("as") or data.get("asname") or "Unknown",
            "lat": lat,
            "lon": lon,
            "status": "ok",
        }
        self.cache.set("ip_api", ip, result)
        return result

    def reverse_geocode(self, lat: float, lon: float) -> dict[str, str]:
        key = f"{lat:.4f},{lon:.4f}"
        cached = self.cache.get("reverse_geo", key)
        if cached:
            return cached

        self.rate_limiter.wait()
        response = self.session.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"format": "jsonv2", "lat": lat, "lon": lon, "zoom": 5},
            headers={"User-Agent": "traceroute-visualizer/1.0"},
            timeout=self.timeout_seconds,
        )
        payload = response.json()
        address = payload.get("address", {})
        result = {
            "city": address.get("city")
            or address.get("state")
            or address.get("county")
            or "Unknown",
            "country": address.get("country") or "Unknown",
        }
        self.cache.set("reverse_geo", key, result)
        return result
