"""Same-feed union-by-id + deterministic cross-feed dedup (ADR 0005 layer-1).

`union_by_id` collapses same-feed overlap (e.g. the USGS `all_day` vs
`significant_week` windows) keyed on `(feed, source_id)`, keeping the record with
the greatest `updated`. `same_event` / `cross_feed_clusters` implement the
deterministic three-tier cross-feed merge — matching GLIDE, shared external ids,
or an EQ-only geographic+temporal coincidence. Semantic embedding dedup
(layer-2) is deferred.
"""

from collections.abc import Iterable

from pipeline.geo import great_circle_km
from pipeline.models import NormalizedEvent

MAX_MERGE_KM = 100.0
MERGE_TIME_WINDOW_MIN = 60.0


def union_by_id(events: Iterable[NormalizedEvent]) -> list[NormalizedEvent]:
    best: dict[tuple[str, str], NormalizedEvent] = {}
    for e in events:
        key = (e.feed, e.source_id)
        current = best.get(key)
        if current is None or e.updated > current.updated:
            best[key] = e
    return list(best.values())


def _norm_glide(glide: str | None) -> str:
    return glide.strip().upper() if glide else ""


def same_event(a: NormalizedEvent, b: NormalizedEvent) -> bool:
    # Tier 1 — matching GLIDE codes on the same hazard.
    ga, gb = _norm_glide(a.glide), _norm_glide(b.glide)
    if ga and gb and ga == gb and a.hazard == b.hazard:
        return True
    # Tier 2 — a shared external source id.
    if a.external_ids & b.external_ids:
        return True
    # Tier 3 — EQ-only geographic + temporal coincidence.
    if a.hazard == "EQ" and b.hazard == "EQ":
        distance = great_circle_km(a.lat, a.lon, b.lat, b.lon)
        minutes = abs((a.time - b.time).total_seconds()) / 60.0
        if distance <= MAX_MERGE_KM and minutes <= MERGE_TIME_WINDOW_MIN:
            return True
    return False


def cross_feed_clusters(events: list[NormalizedEvent]) -> list[list[NormalizedEvent]]:
    n = len(events)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[max(ri, rj)] = min(ri, rj)

    for i in range(n):
        for j in range(i + 1, n):
            if same_event(events[i], events[j]):
                union(i, j)

    clusters: dict[int, list[NormalizedEvent]] = {}
    for i in range(n):
        clusters.setdefault(find(i), []).append(events[i])
    return list(clusters.values())
