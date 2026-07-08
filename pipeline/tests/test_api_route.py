import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
from jsonschema import Draft202012Validator

from api.contract import GDACS_LIST_URL, USGS_URLS, build_response  # top-level `api` pkg (pythonpath=".")

CONTRACT = Path(__file__).resolve().parents[2] / "contract"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
NOW = datetime(2026, 7, 8, 12, 0, 0, tzinfo=timezone.utc)

# GDACS EVENTS4APP list: one Orange EQ duplicating USGS us6000takd (coords + time aligned ->
# tier-3 cross-feed merge) + one Green flood that must NOT trigger a phase-2 detail GET.
GDACS_LIST = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [142.03, 40.47]},
            "properties": {
                "eventtype": "EQ",
                "eventid": 1550421,
                "glide": "",
                "name": "Earthquake near Hachinohe, Japan",
                "alertlevel": "Orange",
                "alertscore": 1.5,
                "istemporary": "false",
                "country": "Japan",
                "fromdate": "2026-07-07T01:40:00",
                "datemodified": "2026-07-07T02:00:00",
                "iso3": "JPN",
                "source": "NEIC",
                "url": {
                    "report": "https://www.gdacs.org/report.aspx?eventid=1550421&eventtype=EQ",
                    "details": "https://www.gdacs.org/gdacsapi/api/events/geteventdata?eventtype=EQ&eventid=1550421",
                },
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [90.4, 23.7]},
            "properties": {
                "eventtype": "FL",
                "eventid": 1550999,
                "glide": "",
                "name": "Flood in Bangladesh",
                "alertlevel": "Green",
                "alertscore": 0.5,
                "istemporary": "false",
                "country": "Bangladesh",
                "fromdate": "2026-07-06T00:00:00",
                "datemodified": "2026-07-06T06:00:00",
                "iso3": "BGD",
                "source": "GDACS",
                "url": {
                    "report": "https://www.gdacs.org/report.aspx?eventid=1550999&eventtype=FL",
                    "details": "https://www.gdacs.org/gdacsapi/api/events/geteventdata?eventtype=FL&eventid=1550999",
                },
            },
        },
    ],
}

# GDACS geteventdata (EQ) — exposure lives in the detail feed, not the list feed (spec §7.5).
GDACS_DETAIL_EQ = {
    "earthquakedetails": {
        "rapidpop": 43996,
        "rapidpopdescription": "40 thousand in MMI IV or higher",
    },
}


def _schema() -> dict:
    return json.loads((CONTRACT / "schema" / "contract.v2.schema.json").read_text("utf-8"))


def _client(route):
    return httpx.Client(transport=httpx.MockTransport(route))


def _route(gdacs_list, detail_status, detail_calls):
    def route(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url == USGS_URLS["all_day"]:
            return httpx.Response(
                200,
                content=(FIXTURES / "usgs_all_day.json").read_text("utf-8"),
                headers={"content-type": "application/json"},
            )
        if url == USGS_URLS["significant_week"]:
            return httpx.Response(
                200,
                content=(FIXTURES / "usgs_significant_week.json").read_text("utf-8"),
                headers={"content-type": "application/json"},
            )
        if url == GDACS_LIST_URL:
            if gdacs_list is None:
                return httpx.Response(503)
            return httpx.Response(200, json=gdacs_list)
        if request.url.path.endswith("/geteventdata"):
            detail_calls.append(request.url.params["eventid"])
            if detail_status != 200:
                return httpx.Response(detail_status)
            return httpx.Response(200, json=GDACS_DETAIL_EQ)
        raise AssertionError(f"unexpected request: {url}")

    return route


def test_urls_cover_both_windows():
    assert set(USGS_URLS) == {"all_day", "significant_week"}


def test_gdacs_list_url_is_events4app():
    assert GDACS_LIST_URL.endswith("/geteventlist/EVENTS4APP")


def test_build_response_success_merges_and_affected():
    calls: list[str] = []
    contract = build_response(_client(_route(GDACS_LIST, 200, calls)), NOW)

    Draft202012Validator(_schema()).validate(contract)
    assert contract["schema_version"] == "2.0.0"

    feeds = {f["window"]: f for f in contract["meta"]["feeds"]}
    assert set(feeds) == {"all_day", "significant_week", "events4app"}
    assert feeds["events4app"]["source"] == "gdacs"
    assert feeds["events4app"]["status"] == "ok"

    by_id = {e["id"]: e for e in contract["events"]}
    merged = by_id["usgs:us6000takd"]
    assert {s["feed"] for s in merged["sources"]} == {"usgs", "gdacs"}
    assert merged["sources"][0]["feed"] == "usgs"
    assert merged["affected"]["source"] == "gdacs"
    assert merged["affected"]["estimate"] == 43996
    assert "MMI IV" in merged["affected"]["basis"]

    # phase-2 is bounded to Orange/Red — the Green flood is never fetched
    assert calls == ["1550421"]


def test_gdacs_list_down_marks_error_usgs_present():
    calls: list[str] = []
    contract = build_response(_client(_route(None, 200, calls)), NOW)

    Draft202012Validator(_schema()).validate(contract)
    feeds = {f["window"]: f for f in contract["meta"]["feeds"]}
    assert feeds["events4app"]["source"] == "gdacs"
    assert feeds["events4app"]["status"] == "error"
    assert feeds["all_day"]["status"] == "ok"
    assert feeds["significant_week"]["status"] == "ok"

    by_id = {e["id"]: e for e in contract["events"]}
    assert "usgs:us6000takd" in by_id  # USGS events survive a GDACS outage
    assert len(by_id["usgs:us6000takd"]["sources"]) == 1
    assert calls == []  # no list -> no detail fetches


def test_detail_down_nulls_affected():
    calls: list[str] = []
    contract = build_response(_client(_route(GDACS_LIST, 500, calls)), NOW)

    Draft202012Validator(_schema()).validate(contract)
    by_id = {e["id"]: e for e in contract["events"]}
    merged = by_id["usgs:us6000takd"]
    # merge is list-driven, so it still happens; only affected degrades
    assert {s["feed"] for s in merged["sources"]} == {"usgs", "gdacs"}
    assert merged["affected"]["estimate"] is None
    assert merged["affected"]["source"] is None
    assert calls == ["1550421"]  # detail was attempted, then failed
