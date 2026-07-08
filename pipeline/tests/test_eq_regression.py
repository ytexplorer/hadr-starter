import json
from datetime import datetime, timezone
from pathlib import Path

from pipeline.build import FeedFetch, build_contract
from pipeline.severity import severity_level

FIXTURES = Path(__file__).resolve().parent / "fixtures"
NOW = datetime(2026, 7, 8, 12, 0, 0, tzinfo=timezone.utc)

# v1 golden EQ semantics carried unchanged through the v2 build (level/id/geometry/
# magnitude/provisional are boost-free). `major` is only boost-free where applied == 0,
# so it is asserted conditionally against GOLDEN_MAJOR.
GOLDEN = {
    "usgs:us6000takd": {"level": "severe", "magnitude": 7.2, "provisional": True,
                        "geometry": {"lat": 40.4353, "lon": 141.845, "depth_km": 35.0}},
    "usgs:ci41288735": {"level": "minor", "magnitude": 1.49, "provisional": True,
                        "geometry": {"lat": 35.2941666666667, "lon": -117.807, "depth_km": 7.34}},
    "usgs:uw714040221": {"level": "serious", "magnitude": 3.8, "provisional": False,
                         "geometry": {"lat": 48.2888333333333, "lon": -122.6065, "depth_km": 25.38}},
    "usgs:us6000ocpc": {"level": "severe", "magnitude": 7.2, "provisional": False,
                        "geometry": {"lat": -40.0, "lon": -140.0, "depth_km": 10.0}},
    "usgs:us6000t9bg": {"level": "serious", "magnitude": 6.1, "provisional": False,
                        "geometry": {"lat": 37.8295, "lon": 95.3273, "depth_km": 10.0}},
}
GOLDEN_MAJOR = {
    "usgs:us6000takd": True, "usgs:ci41288735": False, "usgs:uw714040221": True,
    "usgs:us6000ocpc": True, "usgs:us6000t9bg": True,
}


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text("utf-8"))


def _fetch(source: str, window: str, payload: dict) -> FeedFetch:
    return FeedFetch(source=source, window=window, status="ok",
                     payload=payload, error=None, fetched_at=NOW)


def _usgs_only_events() -> dict:
    contract = build_contract(
        [_fetch("usgs", "all_day", _load("usgs_all_day.json")),
         _fetch("usgs", "significant_week", _load("usgs_significant_week.json"))],
        {}, NOW,
    )
    return {e["id"]: e for e in contract["events"]}


def test_usgs_only_level_id_geometry_magnitude_provisional_match_v1():
    events = _usgs_only_events()
    assert set(events) == set(GOLDEN)
    for eid, want in GOLDEN.items():
        e = events[eid]
        assert e["severity"]["level"] == want["level"]
        assert e["magnitude"] == want["magnitude"]
        assert e["provisional"] == want["provisional"]
        assert e["geometry"] == want["geometry"]


def test_major_unchanged_for_every_unboosted_event():
    events = _usgs_only_events()
    unboosted = {eid: e for eid, e in events.items()
                 if e["severity"]["boost"]["applied"] == 0.0}
    assert unboosted  # at least the mid-ocean quake carries no boost
    for eid, e in unboosted.items():
        assert e["major"] == GOLDEN_MAJOR[eid]


def test_boost_never_changes_level():
    near = _usgs_only_events()["usgs:us6000takd"]
    assert near["severity"]["boost"]["applied"] > 0.0            # this event IS boosted
    inputs = near["severity"]["inputs"]
    assert near["severity"]["level"] == severity_level(
        inputs["mag"], inputs["sig"], inputs["alert"])           # band = the frozen EQ path
