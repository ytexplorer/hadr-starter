import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

CONTRACT = Path(__file__).resolve().parents[2] / "contract"
SCHEMA = CONTRACT / "schema" / "contract.v1.schema.json"
FIXTURES = [
    "contract.v1.example.json",
    "contract.v1.no-major.json",
    "contract.v1.feed-down.json",
]


def _schema() -> dict:
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def test_schema_is_valid_draft_2020_12() -> None:
    Draft202012Validator.check_schema(_schema())


@pytest.mark.parametrize("name", FIXTURES)
def test_fixture_validates_against_schema(name: str) -> None:
    instance = json.loads((CONTRACT / "fixtures" / name).read_text(encoding="utf-8"))
    Draft202012Validator(_schema()).validate(instance)


def test_example_has_a_provisional_and_a_nonmajor_event() -> None:
    events = json.loads((CONTRACT / "fixtures" / "contract.v1.example.json").read_text("utf-8"))["events"]
    assert any(e["provisional"] for e in events), "need a provisional event to exercise the badge"
    assert any(not e["major"] for e in events), "need a below-threshold event carried in the contract"
    assert any(e["major"] for e in events), "need a major event for the default view"
