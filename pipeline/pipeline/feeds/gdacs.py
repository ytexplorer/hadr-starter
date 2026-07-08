"""GDACS EVENTS4APP GeoJSON parser. Kept separate and swappable (one module per source)."""

from datetime import datetime, timezone
from typing import Any

from pipeline.models import NormalizedEvent

# The five hazard types we model; GDACS wildfire (WF) and anything unknown are skipped.
_HAZARDS = frozenset({"EQ", "TC", "FL", "VO", "DR"})


def _parse_gdacs_dt(raw: Any) -> datetime | None:
    """Parse a naive GDACS ISO-8601 timestamp, assumed UTC. Returns None if unparseable."""
    if not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def parse_gdacs(feed_json: dict[str, Any]) -> list[NormalizedEvent]:
    """Turn a GDACS EVENTS4APP FeatureCollection into normalized events.

    Only the five modelled hazard types (EQ/TC/FL/VO/DR) are kept; wildfire (WF) and any
    unknown eventtype are skipped defensively. Features missing an eventid, coordinates, or a
    parseable origin time are skipped rather than crashing the whole parse (mirrors USGS).
    Population exposure is NOT in this list feed — it comes from the detail feed later, so
    affected_* stay None here. `istemporary` is carried on `status` for the merge step.
    """
    out: list[NormalizedEvent] = []
    for feat in feed_json.get("features", []):
        props = feat.get("properties") or {}
        hazard = props.get("eventtype")
        if hazard not in _HAZARDS:
            continue
        source_id = props.get("eventid")
        coords = (feat.get("geometry") or {}).get("coordinates") or []
        if not source_id or len(coords) < 2 or coords[0] is None or coords[1] is None:
            continue
        time = _parse_gdacs_dt(props.get("fromdate"))
        if time is None:
            continue
        updated = _parse_gdacs_dt(props.get("datemodified")) or time
        alert = props.get("alertlevel")
        alert_score = props.get("alertscore")
        glide = props.get("glide")
        out.append(
            NormalizedEvent(
                feed="gdacs",
                source_id=str(source_id),
                hazard=hazard,
                title=props.get("name") or "",
                place=props.get("country") or "",
                time=time,
                updated=updated,
                lat=float(coords[1]),
                lon=float(coords[0]),
                url=(props.get("url") or {}).get("report") or "",
                status=str(props.get("istemporary") or "").lower(),
                depth_km=None,
                mag=None,
                sig=None,
                alert=alert.lower() if isinstance(alert, str) else None,
                alert_score=float(alert_score) if alert_score is not None else None,
                glide=glide or None,
                external_ids=frozenset(),
                iso3=props.get("iso3"),
                country=props.get("country"),
                affected_population=None,
                affected_basis=None,
            )
        )
    return out
