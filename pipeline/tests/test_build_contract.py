import json
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator

from pipeline.build import FeedFetch, build_contract
from pipeline.severity import base_signal

CONTRACT = Path(__file__).resolve().parents[2] / "contract"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
NOW = datetime(2026, 7, 8, 12, 0, 0, tzinfo=timezone.utc)

# GDACS EQ detail (geteventdata) shape per spec §7.5: earthquakedetails.rapidpop + description.
EQ_DETAIL = {"earthquakedetails": {"rapidpop": 43996,
                                   "rapidpopdescription": "40 thousand in MMI IV or higher"}}


def _schema() -> dict:
    return json.loads((CONTRACT / "schema" / "contract.v2.schema.json").read_text("utf-8"))


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text("utf-8"))


def _fetch(source: str, window: str, status: str = "ok",
           payload: dict | None = None, error: str | None = None) -> FeedFetch:
    return FeedFetch(source=source, window=window, status=status,
                     payload=payload, error=error, fetched_at=NOW)


def _only(feed: dict, event_id: str) -> dict:
    return {"type": "FeatureCollection",
            "features": [f for f in feed["features"] if f["id"] == event_id]}


def test_hard_usgs_gdacs_duplicate_collapses_to_one_merged_event():
    usgs_one = _only(_load("usgs_all_day.json"), "us6000takd")
    contract = build_contract(
        [_fetch("usgs", "all_day", payload=usgs_one),
         _fetch("gdacs", "events4app", payload=_load("gdacs_dup_of_usgs.json"))],
        {"1550421": EQ_DETAIL},
        NOW,
    )
    Draft202012Validator(_schema()).validate(contract)          # whole contract valid vs v2
    assert len(contract["events"]) == 1                          # collapsed to exactly one
    ev = contract["events"][0]
    assert ev["id"] == "usgs:us6000takd"                         # USGS-present id wins
    assert {s["feed"] for s in ev["sources"]} == {"usgs", "gdacs"}
    assert ev["sources"][0]["feed"] == "usgs"                    # primary is USGS
    assert len(ev["sources"]) == 2
    assert ev["magnitude"] == 7.2                                # magnitude/geometry from USGS
    assert ev["severity"]["inputs"]["alert"] == "orange"         # alert from GDACS
    assert ev["affected"]["estimate"] == 43996                   # affected from GDACS detail
    assert ev["affected"]["source"] == "gdacs"
    assert "MMI IV" in ev["affected"]["basis"]


def test_near_city_outscores_equal_magnitude_mid_ocean_and_emits_boost_audit():
    contract = build_contract(
        [_fetch("usgs", "all_day", payload=_load("usgs_all_day.json"))], {}, NOW,
    )
    by_id = {e["id"]: e for e in contract["events"]}
    near = by_id["usgs:us6000takd"]      # 20 km S of Hachinohe
    ocean = by_id["usgs:us6000ocpc"]     # remote South Pacific, same magnitude
    assert near["magnitude"] == ocean["magnitude"] == 7.2
    assert near["severity"]["score"] > ocean["severity"]["score"]
    assert ocean["severity"]["boost"]["applied"] == 0.0
    boost = near["severity"]["boost"]
    assert set(boost) == {"nearest_place", "population", "distance_km", "applied"}
    assert boost["applied"] > 0.0
    base = base_signal("EQ", near["severity"]["inputs"])
    assert near["severity"]["score"] == base + boost["applied"]  # score = base + applied


def test_multi_hazard_null_magnitude_event_validates():
    contract = build_contract(
        [_fetch("gdacs", "events4app", payload=_load("gdacs_events4app.json"))], {}, NOW,
    )
    Draft202012Validator(_schema()).validate(contract)
    tc = next(e for e in contract["events"] if e["hazard"] == "TC")
    assert tc["magnitude"] is None
    assert tc["geometry"]["depth_km"] is None
    assert tc["severity"]["inputs"]["mag"] is None


def test_events_sorted_by_score_descending():
    contract = build_contract(
        [_fetch("usgs", "all_day", payload=_load("usgs_all_day.json")),
         _fetch("gdacs", "events4app", payload=_load("gdacs_events4app.json"))],
        {}, NOW,
    )
    scores = [e["severity"]["score"] for e in contract["events"]]
    assert scores == sorted(scores, reverse=True)


def test_meta_feeds_carries_all_three_rows_including_gdacs():
    contract = build_contract(
        [_fetch("usgs", "all_day", payload=_load("usgs_all_day.json")),
         _fetch("usgs", "significant_week", payload=_load("usgs_significant_week.json")),
         _fetch("gdacs", "events4app", payload=_load("gdacs_events4app.json"))],
        {}, NOW,
    )
    rows = {(f["source"], f["window"]) for f in contract["meta"]["feeds"]}
    assert rows == {("usgs", "all_day"), ("usgs", "significant_week"), ("gdacs", "events4app")}
    assert len(contract["meta"]["feeds"]) == 3


def test_one_feed_down_still_emits_others_and_marks_meta():
    contract = build_contract(
        [_fetch("usgs", "all_day", payload=_load("usgs_all_day.json")),
         _fetch("gdacs", "events4app", status="error", error="HTTP 503")],
        {}, NOW,
    )
    Draft202012Validator(_schema()).validate(contract)
    meta = {f["source"]: f for f in contract["meta"]["feeds"]}
    assert meta["gdacs"]["status"] == "error"
    assert meta["gdacs"]["error"] == "HTTP 503"
    assert meta["usgs"]["status"] == "ok"
    assert any(e["id"].startswith("usgs:") for e in contract["events"])
    assert all(not e["id"].startswith("gdacs:") for e in contract["events"])
