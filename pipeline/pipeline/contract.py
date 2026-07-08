"""Map a merged event to a contract v2 event, and time formatting for the contract."""

from datetime import datetime, timezone
from typing import Any

from pipeline.affected import affected_block
from pipeline.boost import compute_boost
from pipeline.merge import MergedEvent
from pipeline.severity import base_signal, is_major, level_for

SCHEMA_VERSION = "2.0.0"


def to_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def event_from_merged(m: MergedEvent, now: datetime) -> dict[str, Any]:
    e = m.event
    inputs = {"mag": e.mag, "sig": e.sig, "alert": e.alert, "alert_score": e.alert_score}
    boost = compute_boost(e.lat, e.lon)
    # Round at emit: the contract is the shared artefact (ADR 0006) and must carry tidy 3-dp
    # scores, matching boost.applied/distance_km, not full-precision float noise.
    score = round(base_signal(e.hazard, inputs) + boost["applied"], 3)
    primary = m.sources[0]
    return {
        "id": f"{primary.feed}:{primary.id}",
        "hazard": e.hazard,
        "title": e.title,
        "place": e.place,
        "time": to_iso(e.time),
        "geometry": {"lat": e.lat, "lon": e.lon, "depth_km": e.depth_km},
        "magnitude": e.mag,
        "severity": {
            "level": level_for(e.hazard, inputs),
            "score": score,
            "inputs": inputs,
            "boost": boost,
        },
        "major": is_major(score),
        # USGS "automatic" or GDACS istemporary "true" both mean provisional (spec §7.4)
        "provisional": e.status in ("automatic", "true"),
        "sources": [{"feed": s.feed, "id": s.id, "url": s.url} for s in m.sources],
        "affected": affected_block(e.affected_population, e.affected_basis),
    }
