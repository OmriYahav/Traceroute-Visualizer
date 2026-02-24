from __future__ import annotations

import logging
import os
from typing import Any

import folium
from flask import Flask, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from traceroute_visualizer.services.cache import SQLiteTTLCache
from traceroute_visualizer.services.geo_service import GeoService
from traceroute_visualizer.services.traceroute_service import (
    resolve_target,
    run_traceroute,
)

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


def _get_bool_env(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


def build_map(hops: list[dict[str, Any]]) -> str:
    map_obj = folium.Map(location=[20, 0], zoom_start=2)
    coords: list[tuple[float, float]] = []
    for hop in hops:
        lat = hop.get("lat")
        lon = hop.get("lon")
        if lat is None or lon is None:
            continue
        coords.append((lat, lon))
        folium.Marker(
            location=[lat, lon],
            tooltip=f"Hop {hop['hop_index']} - {hop['ip']}",
            popup=(
                f"Hop {hop['hop_index']}<br>IP: {hop['ip']}<br>"
                f"{hop['city']}, {hop['country']}<br>Status: {hop['status']}"
            ),
        ).add_to(map_obj)

    if len(coords) > 1:
        folium.PolyLine(coords, color="blue", weight=3, opacity=0.7).add_to(map_obj)

    return map_obj._repr_html_()


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=[os.getenv("RATE_LIMIT", "10/minute")],
    )

    max_hops = int(os.getenv("MAX_HOPS", "20"))
    tr_timeout = float(os.getenv("TR_TIMEOUT", "2"))
    tr_retries = int(os.getenv("TR_RETRIES", "1"))
    geo_timeout = float(os.getenv("GEO_TIMEOUT", "3"))
    geo_retries = int(os.getenv("GEO_RETRIES", "2"))
    cache_ttl_days = int(os.getenv("CACHE_TTL_DAYS", "7"))
    block_private_targets = _get_bool_env("BLOCK_PRIVATE_TARGETS", True)

    cache = SQLiteTTLCache(
        os.getenv("CACHE_DB_PATH", "instance/cache.db"),
        ttl_seconds=cache_ttl_days * 86400,
    )
    geo_service = GeoService(
        cache=cache, timeout_seconds=geo_timeout, retries=geo_retries
    )

    @app.get("/")
    def index() -> str:
        return render_template("index.html")

    @app.post("/traceroute")
    @limiter.limit(os.getenv("RATE_LIMIT", "10/minute"))
    def traceroute_route() -> str:
        target = request.form.get("destination_address", "")
        try:
            hostname, resolved_ip = resolve_target(
                target, block_private_targets=block_private_targets
            )
            hop_rows = run_traceroute(
                resolved_ip, max_hops=max_hops, timeout=tr_timeout, retries=tr_retries
            )
        except ValueError as exc:
            logger.warning(
                "validation failed", extra={"target": target, "error": str(exc)}
            )
            return render_template("index.html", error=str(exc), destination=target)
        except Exception:
            logger.exception("traceroute failed")
            return render_template(
                "index.html",
                error="Traceroute failed unexpectedly.",
                destination=target,
            )

        enriched_hops: list[dict[str, Any]] = []
        for hop in hop_rows:
            base = {
                **hop,
                "city": "Unknown",
                "country": "Unknown",
                "isp": "Unknown",
                "asn": "Unknown",
                "lat": None,
                "lon": None,
            }
            if hop["ip"] not in {"*", "Unknown"}:
                try:
                    geo = geo_service.lookup_ip(hop["ip"])
                    base.update(geo)
                    if hop["status"] != "timeout":
                        base["status"] = geo.get("status", hop["status"])
                except Exception:
                    logger.exception("geo lookup failed", extra={"ip": hop["ip"]})
            enriched_hops.append(base)

        map_html = build_map(enriched_hops)
        return render_template(
            "results.html",
            destination=hostname,
            resolved_ip=resolved_ip,
            hops=enriched_hops,
            map_html=map_html,
        )

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=_get_bool_env("FLASK_DEBUG", False),
    )
