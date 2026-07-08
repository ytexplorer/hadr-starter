import json
from pathlib import Path

from pipeline.affected import affected_block, extract_exposure

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text("utf-8"))


def test_extract_eq_exposure_verbatim_from_detail():
    pop, basis = extract_exposure("EQ", _load("gdacs_detail_eq.json"))
    assert pop == 43996            # GDACS rapidpop, carried verbatim
    assert isinstance(pop, int)
    assert "MMI IV" in basis       # rapidpopdescription text


def test_eq_exposure_is_the_raw_field_not_derived():
    detail = _load("gdacs_detail_eq.json")
    raw = detail["properties"]["earthquakedetails"]["rapidpop"]
    pop, _ = extract_exposure("EQ", detail)
    assert pop == int(raw)         # identical to the source field, never recomputed


def test_extract_eq_without_rapidpop_returns_none_and_reason():
    detail = {"properties": {"eventtype": "EQ", "earthquakedetails": {"magnitude": 5.0}}}
    pop, basis = extract_exposure("EQ", detail)
    assert pop is None
    assert basis and isinstance(basis, str)


def test_extract_unquantified_hazard_returns_none_and_reason():
    detail = {"properties": {"eventtype": "DR", "name": "Drought in Somewhere"}}
    pop, basis = extract_exposure("DR", detail)
    assert pop is None
    assert "drought" in basis.lower()


def test_affected_block_null_is_grounded_and_sourceless():
    assert affected_block(None, None) == {
        "estimate": None,
        "basis": "no GDACS exposure figure available",
        "source": None,
    }


def test_affected_block_carries_number_and_gdacs_provenance():
    assert affected_block(43996, "40 thousand in MMI IV") == {
        "estimate": 43996,
        "basis": "40 thousand in MMI IV",
        "source": "gdacs",
    }
