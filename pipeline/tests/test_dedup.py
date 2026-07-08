from datetime import datetime, timedelta, timezone

from pipeline.dedup import (
    MAX_MERGE_KM,
    MERGE_TIME_WINDOW_MIN,
    cross_feed_clusters,
    same_event,
    union_by_id,
)
from pipeline.models import NormalizedEvent

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


def _ev(
    *,
    feed: str = "usgs",
    source_id: str = "id",
    hazard: str = "EQ",
    time: datetime = NOW,
    updated: datetime = NOW,
    lat: float = 0.0,
    lon: float = 0.0,
    glide: str | None = None,
    external_ids: frozenset[str] = frozenset(),
    mag: float | None = 5.0,
) -> NormalizedEvent:
    return NormalizedEvent(
        feed=feed,
        source_id=source_id,
        hazard=hazard,
        title="t",
        place="p",
        time=time,
        updated=updated,
        lat=lat,
        lon=lon,
        url="http://u",
        status="reviewed",
        depth_km=None,
        mag=mag,
        sig=None,
        alert=None,
        alert_score=None,
        glide=glide,
        external_ids=external_ids,
        iso3=None,
        country=None,
        affected_population=None,
        affected_basis=None,
    )


def _shape(clusters: list[list[NormalizedEvent]]) -> set[frozenset[tuple[str, str]]]:
    return {frozenset((e.feed, e.source_id) for e in c) for c in clusters}


# --- union_by_id: re-keyed on (feed, source_id) ---

def test_union_collapses_same_feed_and_id_keeping_max_updated():
    old = _ev(feed="usgs", source_id="shared", updated=NOW, mag=5.0)
    new = _ev(feed="usgs", source_id="shared", updated=NOW + timedelta(minutes=10), mag=5.4)
    result = union_by_id([old, new])
    assert len(result) == 1
    assert result[0].mag == 5.4  # the newer record won


def test_union_newer_wins_regardless_of_order():
    old = _ev(feed="usgs", source_id="shared", updated=NOW, mag=5.0)
    new = _ev(feed="usgs", source_id="shared", updated=NOW + timedelta(minutes=10), mag=5.4)
    result = union_by_id([new, old])  # newer placed FIRST — must still win
    assert len(result) == 1
    assert result[0].mag == 5.4


def test_union_does_not_collapse_across_feeds():
    u = _ev(feed="usgs", source_id="shared")
    g = _ev(feed="gdacs", source_id="shared")
    result = union_by_id([u, g])
    assert {(e.feed, e.source_id) for e in result} == {("usgs", "shared"), ("gdacs", "shared")}


def test_union_empty_input():
    assert union_by_id([]) == []


# --- same_event tier 1: GLIDE + same hazard ---

def test_tier1_glide_match_same_hazard():
    a = _ev(feed="usgs", source_id="a", hazard="FL", glide="FL-2026-01", lat=0.0, lon=0.0)
    b = _ev(feed="gdacs", source_id="b", hazard="FL", glide="fl-2026-01", lat=80.0, lon=80.0)
    assert same_event(a, b) is True  # normalized-equal glide wins even far apart & non-EQ


def test_tier1_glide_requires_same_hazard():
    a = _ev(source_id="a", hazard="FL", glide="G-1")
    b = _ev(source_id="b", hazard="TC", glide="G-1")
    assert same_event(a, b) is False


def test_empty_glide_does_not_match():
    a = _ev(source_id="a", hazard="FL", glide=None, lat=0.0, lon=0.0)
    b = _ev(source_id="b", hazard="FL", glide=None, lat=0.0, lon=0.0)
    assert same_event(a, b) is False


# --- same_event tier 2: shared external ids ---

def test_tier2_external_ids_intersection():
    a = _ev(feed="usgs", source_id="a", hazard="EQ",
            external_ids=frozenset({"ci123", "us456"}), lat=0.0, lon=0.0)
    b = _ev(feed="gdacs", source_id="b", hazard="TC",
            external_ids=frozenset({"us456"}), lat=80.0, lon=80.0)
    assert same_event(a, b) is True  # tier 2 ignores hazard & distance


def test_tier2_no_intersection_no_merge():
    a = _ev(source_id="a", hazard="FL", external_ids=frozenset({"x"}), lat=0.0, lon=0.0)
    b = _ev(source_id="b", hazard="FL", external_ids=frozenset({"y"}), lat=0.0, lon=0.0)
    assert same_event(a, b) is False


# --- same_event tier 3: EQ-only geo + time ---

def test_tier3_distance_boundary_inclusive(monkeypatch):
    monkeypatch.setattr("pipeline.dedup.great_circle_km", lambda *a: MAX_MERGE_KM)
    a = _ev(feed="usgs", source_id="a", hazard="EQ", time=NOW)
    b = _ev(feed="gdacs", source_id="b", hazard="EQ", time=NOW)
    assert same_event(a, b) is True  # 100.0 km is IN


def test_tier3_distance_boundary_exclusive(monkeypatch):
    monkeypatch.setattr("pipeline.dedup.great_circle_km", lambda *a: MAX_MERGE_KM + 0.1)
    a = _ev(feed="usgs", source_id="a", hazard="EQ", time=NOW)
    b = _ev(feed="gdacs", source_id="b", hazard="EQ", time=NOW)
    assert same_event(a, b) is False  # 100.1 km is OUT


def test_tier3_time_boundary_inclusive():
    a = _ev(feed="usgs", source_id="a", hazard="EQ", time=NOW, lat=0.0, lon=0.0)
    b = _ev(feed="gdacs", source_id="b", hazard="EQ",
            time=NOW + timedelta(minutes=MERGE_TIME_WINDOW_MIN), lat=0.0, lon=0.0)
    assert same_event(a, b) is True  # 60 min is IN


def test_tier3_time_boundary_exclusive():
    a = _ev(feed="usgs", source_id="a", hazard="EQ", time=NOW, lat=0.0, lon=0.0)
    b = _ev(feed="gdacs", source_id="b", hazard="EQ",
            time=NOW + timedelta(minutes=MERGE_TIME_WINDOW_MIN + 1), lat=0.0, lon=0.0)
    assert same_event(a, b) is False  # 61 min is OUT


def test_tier3_requires_eq_different_hazard_no_merge():
    a = _ev(source_id="a", hazard="EQ", time=NOW, lat=0.0, lon=0.0)
    b = _ev(source_id="b", hazard="FL", time=NOW, lat=0.0, lon=0.0)
    assert same_event(a, b) is False


def test_tc_never_tier3_merges():
    a = _ev(source_id="a", hazard="TC", time=NOW, lat=0.0, lon=0.0)
    b = _ev(source_id="b", hazard="TC", time=NOW, lat=0.0, lon=0.0)
    assert same_event(a, b) is False


# --- cross_feed_clusters: union-find, order-independent, transitive ---

def test_cross_feed_clusters_order_independent():
    a = _ev(feed="usgs", source_id="a", hazard="EQ", time=NOW, lat=0.0, lon=0.0)
    b = _ev(feed="gdacs", source_id="b", hazard="EQ", time=NOW, lat=0.0, lon=0.0)
    c = _ev(feed="usgs", source_id="c", hazard="TC", time=NOW, lat=50.0, lon=50.0)
    forward = _shape(cross_feed_clusters([a, b, c]))
    reverse = _shape(cross_feed_clusters([c, b, a]))
    assert forward == reverse
    assert forward == {
        frozenset({("usgs", "a"), ("gdacs", "b")}),
        frozenset({("usgs", "c")}),
    }


def test_cross_feed_clusters_transitivity():
    a = _ev(feed="usgs", source_id="a", hazard="EQ", glide="G-9", lat=0.0, lon=0.0)
    b = _ev(feed="gdacs", source_id="b", hazard="EQ", glide="g-9",
            external_ids=frozenset({"link"}), lat=80.0, lon=80.0)
    c = _ev(feed="other", source_id="c", hazard="TC",
            external_ids=frozenset({"link"}), lat=-80.0, lon=-80.0)
    clusters = cross_feed_clusters([a, b, c])  # a~b (glide), b~c (ext id), a≁c directly
    assert len(clusters) == 1
    assert _shape(clusters) == {frozenset({("usgs", "a"), ("gdacs", "b"), ("other", "c")})}
