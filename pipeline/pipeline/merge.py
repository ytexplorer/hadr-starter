"""Collapse a cross-feed cluster into one canonical MergedEvent, keeping all source links.

Runs after same-feed union and cross-feed clustering (dedup.py) and before severity/boost,
so the merged record is the sole gate driver (ADR 0005; spec §7.4). Field preference:
magnitude/geometry/time/title/place/sig from the USGS member; alert/alert_score/affected_*
from the GDACS member; status from USGS when present else the priority member. Deterministic
regardless of input order.
"""

from dataclasses import dataclass, replace

from pipeline.models import NormalizedEvent

FEED_PRIORITY: tuple[str, ...] = ("usgs", "gdacs")


@dataclass(frozen=True)
class SourceLink:
    """A single feed's provenance link for a merged event."""

    feed: str
    id: str
    url: str


@dataclass(frozen=True)
class MergedEvent:
    """A canonical reconciled event plus every source link that fed it (ordered primary-first)."""

    event: NormalizedEvent
    sources: tuple[SourceLink, ...]


def _rank(feed: str) -> int:
    return FEED_PRIORITY.index(feed) if feed in FEED_PRIORITY else len(FEED_PRIORITY)


def _order(members: list[NormalizedEvent]) -> list[NormalizedEvent]:
    # FEED_PRIORITY, then within a feed max(updated), then lexicographic source_id.
    return sorted(
        members,
        key=lambda e: (_rank(e.feed), -e.updated.timestamp(), e.source_id),
    )


def merge_cluster(members: list[NormalizedEvent]) -> MergedEvent:
    ordered = _order(members)
    primary = ordered[0]
    usgs = next((m for m in ordered if m.feed == "usgs"), None)
    gdacs = next((m for m in ordered if m.feed == "gdacs"), None)

    geo = usgs or primary
    alert = gdacs or primary
    status = usgs or primary

    canonical = replace(
        primary,
        title=geo.title,
        place=geo.place,
        time=geo.time,
        lat=geo.lat,
        lon=geo.lon,
        depth_km=geo.depth_km,
        mag=geo.mag,
        sig=geo.sig,
        alert=alert.alert,
        alert_score=alert.alert_score,
        affected_population=alert.affected_population,
        affected_basis=alert.affected_basis,
        status=status.status,
    )
    sources = tuple(SourceLink(m.feed, m.source_id, m.url) for m in ordered)
    return MergedEvent(event=canonical, sources=sources)
