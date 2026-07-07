"""Vercel Python serverless entrypoint: fetch USGS windows and return contract v1 JSON.

This is the only network-touching code. All logic lives in the pure core (pipeline.build);
this file just fetches and serializes.
"""

import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from typing import Any

import httpx

from pipeline.build import WindowFetch, build_contract

USGS_URLS = {
    "all_day": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson",
    "significant_week": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.geojson",
}


def fetch_window(client: httpx.Client, window: str, now: datetime) -> WindowFetch:
    try:
        resp = client.get(USGS_URLS[window], timeout=10.0)
        resp.raise_for_status()
        return WindowFetch(window=window, ok=True, payload=resp.json(), error=None, fetched_at=now)
    except Exception as exc:  # noqa: BLE001 — any fetch/parse failure degrades this window only
        return WindowFetch(window=window, ok=False, payload=None, error=str(exc), fetched_at=now)


def build_response(client: httpx.Client, now: datetime) -> dict[str, Any]:
    fetches = [fetch_window(client, w, now) for w in ("all_day", "significant_week")]
    return build_contract(fetches, now)


class handler(BaseHTTPRequestHandler):  # noqa: N801 — Vercel requires the name `handler`
    def do_GET(self) -> None:  # noqa: N802
        now = datetime.now(timezone.utc)
        try:
            with httpx.Client() as client:
                contract = build_response(client, now)
            body = json.dumps(contract).encode("utf-8")
            status = 200
        except Exception as exc:  # noqa: BLE001 — fail loud; no last-good store this slice
            body = json.dumps({"error": str(exc)}).encode("utf-8")
            status = 500
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")  # for local cross-origin e2e (Task 12)
        self.end_headers()
        self.wfile.write(body)
