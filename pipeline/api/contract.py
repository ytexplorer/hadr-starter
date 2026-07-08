"""Vercel Python serverless entrypoint: two-phase USGS+GDACS fetch -> contract v2 JSON.

This is the only network-touching code. All decisions live in the pure core (pipeline.build);
this file fetches (phase-1 USGS windows + GDACS list, phase-2 bounded GDACS detail),
serializes, and degrades each network edge independently — a failed detail GET only nulls
that event's `affected`, it never crashes the build.
"""

import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from typing import Any

import httpx

from pipeline.build import FeedFetch, build_contract

USGS_URLS = {
    "all_day": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson",
    "significant_week": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.geojson",
}
GDACS_LIST_URL = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/EVENTS4APP"
GDACS_DETAIL_URL = "https://www.gdacs.org/gdacsapi/api/events/geteventdata"
DETAIL_ALERT_LEVELS = frozenset({"orange", "red"})
TIMEOUT = 10.0


def _fetch_usgs(client: httpx.Client, window: str, now: datetime) -> FeedFetch:
    try:
        resp = client.get(USGS_URLS[window], timeout=TIMEOUT)
        resp.raise_for_status()
        return FeedFetch(
            source="usgs", window=window, status="ok",
            fetched_at=now, payload=resp.json(), error=None,
        )
    except Exception as exc:  # noqa: BLE001 — any fetch/parse failure degrades this window only
        return FeedFetch(
            source="usgs", window=window, status="error",
            fetched_at=now, payload=None, error=str(exc),
        )


def _fetch_gdacs_list(client: httpx.Client, now: datetime) -> FeedFetch:
    try:
        resp = client.get(GDACS_LIST_URL, timeout=TIMEOUT)
        resp.raise_for_status()
        return FeedFetch(
            source="gdacs", window="events4app", status="ok",
            fetched_at=now, payload=resp.json(), error=None,
        )
    except Exception as exc:  # noqa: BLE001 — a down GDACS list degrades only its own feed row
        return FeedFetch(
            source="gdacs", window="events4app", status="error",
            fetched_at=now, payload=None, error=str(exc),
        )


def _detail_targets(list_payload: dict[str, Any] | None) -> list[tuple[str, str]]:
    """(eventtype, eventid) for Orange/Red events — the only ones that can clear `major` (§7.5)."""
    if not list_payload:
        return []
    targets: list[tuple[str, str]] = []
    for feature in list_payload.get("features", []):
        props = feature.get("properties", {})
        if str(props.get("alertlevel", "")).lower() not in DETAIL_ALERT_LEVELS:
            continue
        eventtype = props.get("eventtype")
        eventid = props.get("eventid")
        if eventtype and eventid is not None:
            targets.append((str(eventtype), str(eventid)))
    return targets


def _fetch_detail_map(client: httpx.Client, targets: list[tuple[str, str]]) -> dict[str, Any]:
    """Bounded phase-2 GETs. A failed detail is omitted -> that event's affected stays null."""
    detail_map: dict[str, Any] = {}
    for eventtype, eventid in targets:
        try:
            resp = client.get(
                GDACS_DETAIL_URL,
                params={"eventtype": eventtype, "eventid": eventid},
                timeout=TIMEOUT,
            )
            resp.raise_for_status()
            detail_map[eventid] = resp.json()
        except Exception:  # noqa: BLE001 — degrade this event only; never crash the build
            continue
    return detail_map


def build_response(client: httpx.Client, now: datetime) -> dict[str, Any]:
    fetches = [_fetch_usgs(client, w, now) for w in ("all_day", "significant_week")]
    gdacs_list = _fetch_gdacs_list(client, now)
    fetches.append(gdacs_list)
    detail_map = _fetch_detail_map(client, _detail_targets(gdacs_list.payload))
    return build_contract(fetches, detail_map, now)


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
