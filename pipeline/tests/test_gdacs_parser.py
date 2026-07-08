from datetime import datetime, timezone

import pytest

from pipeline.feeds import PARSERS
from pipeline.feeds.gdacs import parse_gdacs


def _feature(**props):
    """A single valid GDACS EVENTS4APP feature; kwargs override individual properties."""
    base = {
        "eventtype": "EQ",
        "eventid": 1550421,
        "glide": "",
        "name": "Earthquake in Japan",
        "alertlevel": "Green",
        "alertscore": 1,
        "istemporary": "false",
        "country": "Japan",
        "fromdate": "2026-07-06T11:29:36",
        "datemodified": "2026-07-06T12:09:48",
        "iso3": "JPN",
        "source": "NEIC",
        "url": {"report": "https://www.gdacs.org/report.aspx?eventid=1550421"},
    }
    base.update(props)
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [141.845, 40.4353]},
        "properties": base,
    }


def _one(**props):
    events = parse_gdacs({"features": [_feature(**props)]})
    assert len(events) == 1
    return events[0]


def test_parses_core_fields_lonlat_order_and_utc_times():
    e = _one()
    assert e.feed == "gdacs"
    assert e.source_id == "1550421"
    assert e.hazard == "EQ"
    assert e.title == "Earthquake in Japan"
    assert e.place == "Japan" and e.country == "Japan" and e.iso3 == "JPN"
    # coordinates arrive [lon, lat]
    assert e.lat == 40.4353 and e.lon == 141.845
    assert e.depth_km is None and e.mag is None and e.sig is None
    assert e.url == "https://www.gdacs.org/report.aspx?eventid=1550421"
    assert e.external_ids == frozenset()
    assert e.affected_population is None and e.affected_basis is None
    # naive GDACS ISO strings are assumed UTC
    assert e.time == datetime(2026, 7, 6, 11, 29, 36, tzinfo=timezone.utc)
    assert e.updated == datetime(2026, 7, 6, 12, 9, 48, tzinfo=timezone.utc)
    assert e.time.tzinfo == timezone.utc and e.updated.tzinfo == timezone.utc


@pytest.mark.parametrize("hazard", ["EQ", "TC", "FL", "VO", "DR"])
def test_maps_each_modelled_hazard_type(hazard):
    assert _one(eventtype=hazard).hazard == hazard


def test_skips_wildfire_and_unknown_eventtypes():
    feats = [
        _feature(eventtype="WF", eventid=1),
        _feature(eventtype="XX", eventid=2),
        _feature(eventtype="TC", eventid=3),
    ]
    events = parse_gdacs({"features": feats})
    assert [e.source_id for e in events] == ["3"]
    assert events[0].hazard == "TC"


def test_lowercases_alert_colour_and_reads_score():
    e = _one(alertlevel="Orange", alertscore=1.5)
    assert e.alert == "orange" and e.alert_score == 1.5


def test_empty_glide_becomes_none_but_real_glide_kept():
    assert _one(glide="").glide is None
    assert _one(glide="EQ-2026-000123").glide == "EQ-2026-000123"


def test_skips_features_missing_eventid_coords_or_unparseable_date():
    good = _feature(eventid=999)
    no_id = _feature()
    no_id["properties"].pop("eventid")
    no_coords = _feature(eventid=1001)
    no_coords["geometry"] = {"type": "Point", "coordinates": []}
    bad_date = _feature(eventid=1002, fromdate="not-a-date")
    events = parse_gdacs({"features": [good, no_id, no_coords, bad_date]})
    assert [e.source_id for e in events] == ["999"]


def test_empty_or_missing_features_yield_nothing():
    assert parse_gdacs({"features": []}) == []
    assert parse_gdacs({}) == []


def test_parsers_registry_exposes_both_feeds():
    assert set(PARSERS) == {"usgs", "gdacs"}
    assert PARSERS["gdacs"] is parse_gdacs


def test_registry_dispatch_parses_gdacs_feature():
    events = PARSERS["gdacs"]({"features": [_feature()]})
    assert len(events) == 1 and events[0].feed == "gdacs"
