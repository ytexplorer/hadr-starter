import json
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator

from pipeline.build import WindowFetch, build_contract

CONTRACT = Path(__file__).resolve().parents[2] / "contract"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
NOW = datetime(2026, 7, 8, 12, 0, 0, tzinfo=timezone.utc)


def _schema() -> dict:
    return json.loads((CONTRACT / "schema" / "contract.v1.schema.json").read_text("utf-8"))


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text("utf-8"))


def _fetch(window: str, ok: bool = True, payload: dict | None = None, error: str | None = None) -> WindowFetch:
    return WindowFetch(window=window, ok=ok, payload=payload, error=error, fetched_at=NOW)


def test_emits_schema_valid_contract_from_both_windows():
    contract = build_contract(
        [_fetch("all_day", payload=_load("usgs_all_day.json")),
         _fetch("significant_week", payload=_load("usgs_significant_week.json"))],
        NOW,
    )
    Draft202012Validator(_schema()).validate(contract)
    assert contract["schema_version"] == "1.0.0"
    assert contract["generated_at"] == "2026-07-08T12:00:00Z"
    assert {f["window"] for f in contract["meta"]["feeds"]} == {"all_day", "significant_week"}


def test_union_by_id_across_windows_yields_no_duplicate_ids():
    contract = build_contract(
        [_fetch("all_day", payload=_load("usgs_all_day.json")),
         _fetch("significant_week", payload=_load("usgs_significant_week.json"))],
        NOW,
    )
    ids = [e["id"] for e in contract["events"]]
    assert len(ids) == len(set(ids))  # the shared quake appears once


def test_flags_and_ids_and_provisional_are_correct():
    contract = build_contract([_fetch("all_day", payload=_load("usgs_all_day.json"))], NOW)
    by_severity = {e["severity"]["level"] for e in contract["events"]}
    assert "severe" in by_severity
    assert all(e["id"].startswith("usgs:") for e in contract["events"])
    assert any(e["provisional"] for e in contract["events"])  # the automatic M7 red
    assert any(not e["major"] for e in contract["events"])    # the below-threshold quake
    assert all(e["hazard"] == "EQ" for e in contract["events"])


def test_events_sorted_newest_first():
    contract = build_contract([_fetch("all_day", payload=_load("usgs_all_day.json"))], NOW)
    times = [e["time"] for e in contract["events"]]
    assert times == sorted(times, reverse=True)


def test_one_window_down_still_emits_other_and_marks_meta():
    contract = build_contract(
        [_fetch("all_day", payload=_load("usgs_all_day.json")),
         _fetch("significant_week", ok=False, error="HTTP 503")],
        NOW,
    )
    Draft202012Validator(_schema()).validate(contract)
    meta = {f["window"]: f for f in contract["meta"]["feeds"]}
    assert meta["significant_week"]["status"] == "error"
    assert meta["significant_week"]["error"] == "HTTP 503"
    assert meta["all_day"]["status"] == "ok"
    assert len(contract["events"]) > 0


def test_all_windows_down_yields_empty_events():
    contract = build_contract(
        [_fetch("all_day", ok=False, error="HTTP 503"),
         _fetch("significant_week", ok=False, error="HTTP 503")],
        NOW,
    )
    Draft202012Validator(_schema()).validate(contract)
    assert contract["events"] == []
    assert all(f["status"] == "error" for f in contract["meta"]["feeds"])
