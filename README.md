# Traceroute Visualizer

Flask web app that runs Scapy traceroute, enriches hops with geolocation metadata, and renders both a hops table and an embedded Folium map in the browser.

## Features
- Flask UI with input form and results page.
- Traceroute via **Scapy** (no OS traceroute shell calls).
- Hops table columns: hop index, IP, RTT, city, country, ISP/ASN, status.
- Embedded Folium map with hop markers + polyline path.
- HTTPS geo calls (`ip-api` + Nominatim reverse geocode).
- Retries/timeouts for outbound HTTP requests.
- SQLite TTL cache for geo data.
- User request rate limiting with Flask-Limiter.
- Optional blocking of internal/reserved traceroute targets.

## Project structure
```text
traceroute_visualizer/
  __init__.py
  app.py
  services/
    cache.py
    geo_service.py
    traceroute_service.py
  templates/
    index.html
    results.html
  static/
    styles.css
```

## Requirements
- Python 3.11+
- Raw socket capability for Scapy traceroute (`CAP_NET_RAW`, sometimes `CAP_NET_ADMIN`)

Install dependencies:
```bash
pip install -r requirements.txt
```

## Run locally
```bash
cp .env.example .env
python -m traceroute_visualizer.app
```
Then open `http://localhost:5000`.

## Configuration (.env)
- `FLASK_ENV`, `FLASK_DEBUG`
- `MAX_HOPS`, `TR_TIMEOUT`, `TR_RETRIES`
- `GEO_TIMEOUT`, `GEO_RETRIES`
- `CACHE_TTL_DAYS`, `CACHE_DB_PATH`
- `RATE_LIMIT` (example `10/minute`)
- `BLOCK_PRIVATE_TARGETS`
- `LOG_LEVEL`

## Docker
Build and run:
```bash
docker compose up --build
```

Scapy requires capabilities. Compose file includes:
- `NET_RAW`
- `NET_ADMIN`

If needed in plain Docker:
```bash
docker run --cap-add=NET_RAW --cap-add=NET_ADMIN -p 5000:5000 traceroute-visualizer
```

## Tests, lint, format
```bash
pytest -q
ruff check .
black --check .
```

## CI
GitHub Actions workflow runs lint, format check, and pytest on pushes and PRs.

## Limitations
- Geo location quality depends on IP database accuracy and may be approximate.
- Some hops do not respond (timeouts are kept in table for hop continuity).
- Some hops have private/reserved addresses; these are marked and usually skipped for geo.
- External APIs have rate limits; caching and limiter reduce pressure but do not remove limits.
- Traceroute may fail without required network capabilities.

## Security notes
- Target input is validated and resolved before tracing.
- Optional policy (`BLOCK_PRIVATE_TARGETS=true`) blocks internal/reserved targets.
- Request limiting helps reduce abuse.

## Screenshots
Use the app and capture screenshots in your own environment (route paths vary by network and privileges).
