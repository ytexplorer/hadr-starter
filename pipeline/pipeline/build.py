"""The pure pipeline core: already-fetched feed windows + GDACS detail -> contract v2. No network."""

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any

from pipeline.affected import extract_exposure
from pipeline.contract import SCHEMA_VERSION, event_from_merged, to_iso
from pipeline.dedup import cross_feed_clusters, union_by_id
from pipeline.feeds import PARSERS
from pipeline.merge import merge_cluster
from pipeline.models import NormalizedEvent


@dataclass(frozen=True)
class FeedFetch:
    """The result of fetching one feed window — success carries raw payload, failure an error."""

    source: str
    window: str
    status: str
    fetched_at: datetime
    payload: dict[str, Any] | None
    error: str | None


def _with_exposure(
    e: NormalizedEvent, detail_map: dict[str, dict[str, Any]]
) -> NormalizedEvent:
    """Carry GDACS's verbatim exposure onto the GDACS member from its detail payload."""
    if e.feed != "gdacs" or e.source_id not in detail_map:
        return e
    population, basis = extract_exposure(e.hazard, detail_map[e.source_id])
    return replace(e, affected_population=population, affected_basis=basis)


def build_contract(
    fetches: list[FeedFetch],
    detail_map: dict[str, dict[str, Any]],
    now: datetime,
) -> dict[str, Any]:
    feeds_meta: list[dict[str, Any]] = []
    events_in: list[NormalizedEvent] = []
    for f in fetches:
        if f.status == "ok" and f.payload is not None:
            parsed = PARSERS[f.source](f.payload)
            events_in.extend(parsed)
            feeds_meta.append({
                "source": f.source, "window": f.window, "status": "ok",
                "fetched_at": to_iso(f.fetched_at), "event_count": len(parsed),
                "error": None,
            })
        else:
            feeds_meta.append({
                "source": f.source, "window": f.window, "status": "error",
                "fetched_at": to_iso(f.fetched_at), "event_count": 0,
                "error": f.error or "fetch failed",
            })

    enriched = [_with_exposure(e, detail_map) for e in events_in]
    clusters = cross_feed_clusters(union_by_id(enriched))
    events = [event_from_merged(merge_cluster(c), now) for c in clusters]
    # Ordering lives here (score desc, time desc, id asc) via stable successive sorts.
    events.sort(key=lambda e: e["id"])
    events.sort(key=lambda e: e["time"], reverse=True)
    events.sort(key=lambda e: e["severity"]["score"], reverse=True)

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": to_iso(now),
        "meta": {"feeds": feeds_meta},
        "events": events,
    }
