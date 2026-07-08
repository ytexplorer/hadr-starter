import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

from pipeline.contract import SCHEMA_VERSION

CONTRACT = Path(__file__).resolve().parents[2] / "contract"
SCHEMA = CONTRACT / "schema" / "contract.v2.schema.json"


def _schema() -> dict:
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


MINIMAL_V2 = {
    "schema_version": "2.0.0",
    "generated_at": "2026-07-08T12:00:00Z",
    "meta": {
        "feeds": [
            {
                "source": "gdacs",
                "window": "events4app",
                "status": "ok",
                "fetched_at": "2026-07-08T12:00:00Z",
                "event_count": 1,
                "error": None,
            }
        ]
    },
    "events": [
        {
            "id": "gdacs:1550421",
            "hazard": "TC",
            "title": "Tropical Cyclone Example",
            "place": "Off the coast",
            "time": "2026-07-08T06:00:00Z",
            "geometry": {"lat": 12.3, "lon": 45.6, "depth_km": None},
            "magnitude": None,
            "severity": {
                "level": "serious",
                "score": 78.0,
                "inputs": {"mag": None, "sig": None, "alert": "orange", "alert_score": 1.5},
                "boost": {
                    "nearest_place": None,
                    "population": None,
                    "distance_km": None,
                    "applied": 0.0,
                },
            },
            "major": True,
            "provisional": False,
            "sources": [
                {
                    "feed": "gdacs",
                    "id": "1550421",
                    "url": "https://www.gdacs.org/report.aspx?eventid=1550421",
                }
            ],
            "affected": {"estimate": 43996, "basis": "40 thousand in MMI IV", "source": "gdacs"},
        }
    ],
}


def test_v2_schema_is_valid_draft_2020_12() -> None:
    Draft202012Validator.check_schema(_schema())


def test_minimal_v2_instance_validates() -> None:
    Draft202012Validator(_schema()).validate(MINIMAL_V2)


def test_schema_rejects_unknown_property_and_wrong_version() -> None:
    validator = Draft202012Validator(_schema())
    with pytest.raises(ValidationError):
        validator.validate({**MINIMAL_V2, "surprise": 1})
    with pytest.raises(ValidationError):
        validator.validate({**MINIMAL_V2, "schema_version": "1.0.0"})


def test_pipeline_schema_version_is_bumped() -> None:
    assert SCHEMA_VERSION == "2.0.0"
