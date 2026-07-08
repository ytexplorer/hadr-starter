"""Map a normalized quake to a contract event, and time formatting for the contract."""

from datetime import datetime, timezone
from typing import Any

from pipeline.models import NormalizedQuake
from pipeline.severity import is_major, severity_level

SCHEMA_VERSION = "2.0.0"


def to_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def event_from_quake(q: NormalizedQuake) -> dict[str, Any]:
    return {
        "id": f"usgs:{q.source_id}",
        "hazard": "EQ",
        "title": q.title,
        "place": q.place,
        "time": to_iso(q.time),
        "geometry": {"lat": q.lat, "lon": q.lon, "depth_km": q.depth_km},
        "magnitude": q.mag,
        "severity": {
            "level": severity_level(q.mag, q.sig, q.alert),
            "inputs": {"mag": q.mag, "sig": q.sig, "alert": q.alert},
        },
        "major": is_major(q.mag, q.sig, q.alert),
        "provisional": q.status == "automatic",
        "sources": [{"feed": "usgs", "id": q.source_id, "url": q.url}],
    }
