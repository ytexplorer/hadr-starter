"""Same-source union-by-id — the degenerate case of dedup for a single feed across windows.

This is NOT cross-feed dedup (out of scope for Slice 1); it only collapses the overlap
between the USGS `all_day` and `significant_week` windows, which report the same quake.
"""

from collections.abc import Iterable

from pipeline.models import NormalizedQuake


def union_by_id(quakes: Iterable[NormalizedQuake]) -> list[NormalizedQuake]:
    best: dict[str, NormalizedQuake] = {}
    for q in quakes:
        current = best.get(q.source_id)
        if current is None or q.updated > current.updated:
            best[q.source_id] = q
    return list(best.values())
