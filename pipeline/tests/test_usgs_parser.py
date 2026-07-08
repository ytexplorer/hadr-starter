from datetime import datetime, timezone

from pipeline.feeds.usgs import parse_usgs


EPOCH_MS = 1_735_689_600_000  # 2025-01-01T00:00:00Z (clean, easily verified)


def _feature(**props):
    return {
        "type": "Feature",
        "id": props.pop("id", "usgsX"),
        "properties": {"time": EPOCH_MS, "updated": EPOCH_MS + 3_600_000,
                       "title": "M 5.0", "place": "somewhere", "status": "reviewed",
                       "mag": 5.0, "sig": 400, "alert": None, "url": "http://u", **props},
        "geometry": {"type": "Point", "coordinates": [10.0, 20.0, 5.0]},
    }


def test_parses_core_fields_and_utc_times():
    q = parse_usgs({"features": [_feature(id="us1")]})[0]
    assert q.source_id == "us1"
    assert q.lat == 20.0 and q.lon == 10.0 and q.depth_km == 5.0  # note: coords are [lon, lat, depth]
    assert q.mag == 5.0 and q.sig == 400 and q.alert is None and q.status == "reviewed"
    assert q.time == datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc)
    assert q.time.tzinfo == timezone.utc


def test_keeps_null_alert_and_reads_status():
    q = parse_usgs({"features": [_feature(alert="orange", status="automatic")]})[0]
    assert q.alert == "orange" and q.status == "automatic"


def test_skips_features_missing_mag_or_coords_or_time():
    feats = [
        _feature(id="ok"),
        {"id": "nomag", "properties": {"time": 1, "updated": 1, "mag": None}, "geometry": {"coordinates": [1, 2]}},
        {"id": "nocoords", "properties": {"time": 1, "updated": 1, "mag": 5.0}, "geometry": {"coordinates": []}},
        {"id": "notime", "properties": {"time": None, "updated": 1, "mag": 5.0}, "geometry": {"coordinates": [1, 2]}},
    ]
    ids = [q.source_id for q in parse_usgs({"features": feats})]
    assert ids == ["ok"]


def test_empty_feature_collection_yields_nothing():
    assert parse_usgs({"features": []}) == []
    assert parse_usgs({}) == []


def test_sets_feed_hazard_and_gdacs_only_fields_none():
    q = parse_usgs({"features": [_feature(id="us1")]})[0]
    assert q.feed == "usgs"
    assert q.hazard == "EQ"
    # every GDACS-only signal is None for a USGS event
    assert q.alert_score is None
    assert q.glide is None
    assert q.iso3 is None
    assert q.country is None
    assert q.affected_population is None
    assert q.affected_basis is None


def test_parses_external_ids_from_comma_delimited_ids_string():
    # USGS properties.ids is a comma-delimited string with leading/trailing commas
    populated = parse_usgs({"features": [_feature(id="us1", ids=",us1,us6000t9kz,")]})[0]
    assert populated.external_ids == frozenset({"us1", "us6000t9kz"})
    # absent `ids` property -> empty frozenset, never None
    bare = parse_usgs({"features": [_feature(id="us2")]})[0]
    assert bare.external_ids == frozenset()
