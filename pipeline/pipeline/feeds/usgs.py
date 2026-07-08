"""USGS earthquake GeoJSON parser. Kept separate and swappable (one module per source)."""

from datetime import datetime, timezone
from typing import Any

from pipeline.models import NormalizedEvent


def _from_ms(ms: int | float) -> datetime:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)


def _parse_ids(raw: str | None) -> frozenset[str]:
    """USGS `properties.ids` is a comma-delimited string with leading/trailing commas."""
    if not raw:
        return frozenset()
    return frozenset(tok for tok in raw.split(",") if tok)


def parse_usgs(feed_json: dict[str, Any]) -> list[NormalizedEvent]:
    """Turn a USGS GeoJSON FeatureCollection into normalized events (hazard="EQ").

    Features missing magnitude, coordinates, an origin time, or an id are skipped
    defensively rather than crashing the whole parse.
    """
    out: list[NormalizedEvent] = []
    for feat in feed_json.get("features", []):
        props = feat.get("properties") or {}
        coords = (feat.get("geometry") or {}).get("coordinates") or []
        source_id = feat.get("id")
        mag = props.get("mag")
        time_ms = props.get("time")
        if not source_id or mag is None or time_ms is None or len(coords) < 2:
            continue
        if coords[0] is None or coords[1] is None:
            continue
        updated_ms = props.get("updated") or time_ms
        depth = coords[2] if len(coords) > 2 and coords[2] is not None else None
        out.append(
            NormalizedEvent(
                feed="usgs",
                source_id=str(source_id),
                hazard="EQ",
                title=props.get("title") or "",
                place=props.get("place") or "",
                time=_from_ms(time_ms),
                updated=_from_ms(updated_ms),
                lat=float(coords[1]),
                lon=float(coords[0]),
                url=props.get("url") or f"https://earthquake.usgs.gov/earthquakes/eventpage/{source_id}",
                status=props.get("status") or "",
                depth_km=float(depth) if depth is not None else None,
                mag=float(mag),
                sig=props.get("sig"),
                alert=props.get("alert"),
                alert_score=None,
                glide=None,
                external_ids=_parse_ids(props.get("ids")),
                iso3=None,
                country=None,
                affected_population=None,
                affected_basis=None,
            )
        )
    return out
