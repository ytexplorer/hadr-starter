import csv
from pathlib import Path

from pipeline import boost
from pipeline.boost import BOOST_CAP, BOOST_RADIUS_KM, compute_boost

DATA_CSV = Path(boost.__file__).parent / "data" / "cities.csv"


def _rows() -> list[dict[str, str]]:
    with DATA_CSV.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_dataset_is_committed_and_loads_locally():
    assert DATA_CSV.exists()
    rows = _rows()
    assert list(rows[0].keys()) == ["name", "country", "lat", "lon", "population", "capital"]
    assert len(rows) > 1000  # trimmed cities15000 is still thousands of rows
    # A valid result with only this committed file present proves compute_boost works offline.
    result = compute_boost(0.0, 0.0)
    assert set(result) == {"nearest_place", "population", "distance_km", "applied"}


def test_near_capital_gets_high_boost():
    caps = [r for r in _rows() if r["capital"] == "1"]
    top = max(caps, key=lambda r: int(r["population"]))
    b = compute_boost(float(top["lat"]), float(top["lon"]))
    assert b["nearest_place"] == top["name"]
    assert b["population"] == int(top["population"])
    assert b["distance_km"] == 0.0
    assert 18.0 <= b["applied"] <= BOOST_CAP


def test_remote_point_zero_boost_but_nearest_still_populated():
    # Point Nemo — oceanic pole of inaccessibility, thousands of km from any city.
    b = compute_boost(-48.876667, -123.393333)
    assert b["applied"] == 0.0
    assert isinstance(b["nearest_place"], str) and b["nearest_place"]
    assert isinstance(b["population"], int)
    assert isinstance(b["distance_km"], float)
    assert b["distance_km"] > BOOST_RADIUS_KM


def test_closer_scores_at_least_as_high():
    # Honolulu is the only Hawaiian city above the 100k cut, so within ~1000 km it is
    # unambiguously the nearest; stepping south into open ocean only increases distance.
    base_lat, base_lon = 21.3069, -157.8583
    b0 = compute_boost(base_lat, base_lon)
    b1 = compute_boost(base_lat - 1.0, base_lon)
    b2 = compute_boost(base_lat - 2.0, base_lon)
    assert b0["nearest_place"] == b1["nearest_place"] == b2["nearest_place"]
    assert b0["distance_km"] <= b1["distance_km"] <= b2["distance_km"]
    assert b0["applied"] >= b1["applied"] >= b2["applied"]


def test_larger_population_scores_at_least_as_high():
    non_caps = [r for r in _rows() if r["capital"] == "0" and int(r["population"]) > 0]
    big = max(non_caps, key=lambda r: int(r["population"]))
    small = min(non_caps, key=lambda r: int(r["population"]))
    b_big = compute_boost(float(big["lat"]), float(big["lon"]))
    b_small = compute_boost(float(small["lat"]), float(small["lon"]))
    assert b_big["population"] >= b_small["population"]
    assert b_big["applied"] >= b_small["applied"]


def test_deterministic_same_input_twice():
    first = compute_boost(35.0, 139.0)
    second = compute_boost(35.0, 139.0)
    assert first == second
