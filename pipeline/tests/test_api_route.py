import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
from jsonschema import Draft202012Validator

from api.contract import USGS_URLS, build_response  # top-level `api` package (pythonpath=".")

CONTRACT = Path(__file__).resolve().parents[2] / "contract"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
NOW = datetime(2026, 7, 8, 12, 0, 0, tzinfo=timezone.utc)


def _schema() -> dict:
    return json.loads((CONTRACT / "schema" / "contract.v1.schema.json").read_text("utf-8"))


def _client(route):
    return httpx.Client(transport=httpx.MockTransport(route))


def test_urls_cover_both_windows():
    assert set(USGS_URLS) == {"all_day", "significant_week"}


def test_build_response_returns_valid_contract_on_success():
    all_day = (FIXTURES / "usgs_all_day.json").read_text("utf-8")
    sig_week = (FIXTURES / "usgs_significant_week.json").read_text("utf-8")

    def route(request: httpx.Request) -> httpx.Response:
        body = all_day if request.url == USGS_URLS["all_day"] else sig_week
        return httpx.Response(200, content=body, headers={"content-type": "application/json"})

    contract = build_response(_client(route), NOW)
    Draft202012Validator(_schema()).validate(contract)
    assert len(contract["events"]) > 0


def test_build_response_marks_feed_error_on_non_200():
    def route(request: httpx.Request) -> httpx.Response:
        if request.url == USGS_URLS["all_day"]:
            return httpx.Response(503)
        return httpx.Response(200, json={"type": "FeatureCollection", "features": []})

    contract = build_response(_client(route), NOW)
    Draft202012Validator(_schema()).validate(contract)
    meta = {f["window"]: f for f in contract["meta"]["feeds"]}
    assert meta["all_day"]["status"] == "error"
    assert meta["significant_week"]["status"] == "ok"
