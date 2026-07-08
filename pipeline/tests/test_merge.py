from datetime import datetime, timezone

from pipeline.merge import FEED_PRIORITY, MergedEvent, SourceLink, merge_cluster
from pipeline.models import NormalizedEvent


def _ev(
    feed: str,
    source_id: str,
    *,
    hazard: str = "EQ",
    updated_min: int = 0,
    lat: float = 40.0,
    lon: float = 142.0,
    depth_km: float | None = None,
    mag: float | None = None,
    sig: int | None = None,
    alert: str | None = None,
    alert_score: float | None = None,
    affected_population: int | None = None,
    affected_basis: str | None = None,
    status: str = "reviewed",
    url: str = "http://example",
) -> NormalizedEvent:
    return NormalizedEvent(
        feed=feed,
        source_id=source_id,
        hazard=hazard,
        title=f"{feed}-title",
        place=f"{feed}-place",
        time=datetime(2026, 7, 6, 11, 0, tzinfo=timezone.utc),
        updated=datetime(2026, 7, 6, 11, updated_min, tzinfo=timezone.utc),
        lat=lat,
        lon=lon,
        url=url,
        status=status,
        depth_km=depth_km,
        mag=mag,
        sig=sig,
        alert=alert,
        alert_score=alert_score,
        glide=None,
        external_ids=frozenset(),
        iso3=None,
        country=None,
        affected_population=affected_population,
        affected_basis=affected_basis,
    )


def test_feed_priority_is_usgs_then_gdacs():
    assert FEED_PRIORITY == ("usgs", "gdacs")


def test_usgs_gdacs_cluster_prefers_correct_fields():
    usgs = _ev(
        "usgs", "us6000takd", mag=6.0, sig=640, lat=40.47, lon=142.03,
        depth_km=35.0, status="reviewed", url="http://usgs",
    )
    gdacs = _ev(
        "gdacs", "1550421", mag=None, sig=None, lat=40.40, lon=141.80,
        depth_km=None, alert="orange", alert_score=1.5,
        affected_population=43996, affected_basis="40 thousand in MMI IV",
        url="http://gdacs",
    )
    merged = merge_cluster([usgs, gdacs])
    # magnitude / geometry / sig from the USGS member
    assert merged.event.mag == 6.0
    assert merged.event.sig == 640
    assert merged.event.lat == 40.47
    assert merged.event.lon == 142.03
    assert merged.event.depth_km == 35.0
    # alert / alert_score / affected_* from the GDACS member
    assert merged.event.alert == "orange"
    assert merged.event.alert_score == 1.5
    assert merged.event.affected_population == 43996
    assert merged.event.affected_basis == "40 thousand in MMI IV"
    # canonical identity is USGS -> drives id "usgs:us6000takd"
    assert merged.event.feed == "usgs"
    assert merged.event.source_id == "us6000takd"
    # sources: USGS-first, both retained
    assert [s.feed for s in merged.sources] == ["usgs", "gdacs"]
    assert len(merged.sources) == 2
    assert merged.sources[0] == SourceLink("usgs", "us6000takd", "http://usgs")
    assert merged.sources[1] == SourceLink("gdacs", "1550421", "http://gdacs")


def test_single_member_cluster_passthrough():
    usgs = _ev("usgs", "us6000takd", mag=5.5, lat=1.0, lon=2.0, url="http://usgs")
    merged = merge_cluster([usgs])
    assert merged.event == usgs
    assert merged.sources == (SourceLink("usgs", "us6000takd", "http://usgs"),)


def test_gdacs_only_cluster_id_is_gdacs():
    gdacs = _ev(
        "gdacs", "1550421", hazard="TC", mag=None, alert="orange",
        alert_score=2.0, affected_population=1000,
        affected_basis="1 thousand exposed", url="http://gdacs",
    )
    merged = merge_cluster([gdacs])
    assert merged.event.feed == "gdacs"
    assert merged.event.source_id == "1550421"
    assert merged.event.alert == "orange"
    assert merged.event.affected_population == 1000
    assert merged.sources == (SourceLink("gdacs", "1550421", "http://gdacs"),)


def test_merge_is_order_independent():
    usgs = _ev("usgs", "us6000takd", mag=6.0, lat=40.47, lon=142.03, url="http://usgs")
    gdacs = _ev(
        "gdacs", "1550421", alert="orange", affected_population=43996,
        url="http://gdacs",
    )
    forward = merge_cluster([usgs, gdacs])
    backward = merge_cluster([gdacs, usgs])
    assert forward == backward
    assert isinstance(forward, MergedEvent)


def test_same_feed_tie_prefers_max_updated():
    older = _ev("usgs", "usAAA", updated_min=1, mag=5.0, url="http://a")
    newer = _ev("usgs", "usBBB", updated_min=9, mag=6.0, url="http://b")
    merged = merge_cluster([older, newer])
    # newer (max updated) is canonical and sources[0]
    assert merged.event.source_id == "usBBB"
    assert merged.event.mag == 6.0
    assert [s.id for s in merged.sources] == ["usBBB", "usAAA"]


def test_same_feed_equal_updated_breaks_by_source_id():
    a = _ev("usgs", "usAAA", updated_min=5, mag=5.0, url="http://a")
    b = _ev("usgs", "usBBB", updated_min=5, mag=6.0, url="http://b")
    merged = merge_cluster([b, a])
    # equal updated -> lexicographically smallest source_id wins
    assert merged.event.source_id == "usAAA"
    assert merged.event.mag == 5.0
    assert [s.id for s in merged.sources] == ["usAAA", "usBBB"]
