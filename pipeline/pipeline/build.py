"""The pure pipeline core: already-fetched USGS windows -> contract v1 dict. No network."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from pipeline.contract import SCHEMA_VERSION, event_from_quake, to_iso
from pipeline.dedup import union_by_id
from pipeline.feeds.usgs import parse_usgs
from pipeline.models import NormalizedQuake


@dataclass(frozen=True)
class WindowFetch:
    """The result of fetching one USGS window — success carries raw GeoJSON, failure an error."""

    window: str
    ok: bool
    payload: dict[str, Any] | None
    error: str | None
    fetched_at: datetime


def build_contract(fetches: list[WindowFetch], now: datetime) -> dict[str, Any]:
    feeds_meta: list[dict[str, Any]] = []
    all_quakes: list[NormalizedQuake] = []
    for f in fetches:
        if f.ok and f.payload is not None:
            quakes = parse_usgs(f.payload)
            all_quakes.extend(quakes)
            feeds_meta.append({
                "source": "usgs", "window": f.window, "status": "ok",
                "fetched_at": to_iso(f.fetched_at), "event_count": len(quakes),
            })
        else:
            feeds_meta.append({
                "source": "usgs", "window": f.window, "status": "error",
                "fetched_at": to_iso(f.fetched_at), "event_count": 0,
                "error": f.error or "fetch failed",
            })
    events = [event_from_quake(q) for q in union_by_id(all_quakes)]
    events.sort(key=lambda e: e["time"], reverse=True)
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": to_iso(now),
        "meta": {"feeds": feeds_meta},
        "events": events,
    }
