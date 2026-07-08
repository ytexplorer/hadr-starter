"""Deterministic, model-free newsworthiness boost from a committed population-centres dataset.

Pure function of ``(lat, lon)`` and the static committed ``data/cities.csv`` (trimmed GeoNames
``cities15000`` — see ``data/NOTICE.md``). The dataset is loaded once, ``__file__``-relative, so
the boost never touches the network (CLAUDE.md conv. 1; spec §7.2). The returned dict is copied
verbatim into ``severity.boost``.
"""

import csv
import math
from functools import lru_cache
from pathlib import Path
from typing import Any, NamedTuple

from pipeline.geo import great_circle_km

BOOST_RADIUS_KM = 300.0
MAX_BOOST = 15.0
CAPITAL_BONUS = 5.0
BOOST_CAP = 20.0

_CITIES_CSV = Path(__file__).parent / "data" / "cities.csv"


class _City(NamedTuple):
    name: str
    lat: float
    lon: float
    population: int
    capital: bool


@lru_cache(maxsize=1)
def _load_cities() -> tuple[_City, ...]:
    with _CITIES_CSV.open(encoding="utf-8", newline="") as fh:
        return tuple(
            _City(
                name=row["name"],
                lat=float(row["lat"]),
                lon=float(row["lon"]),
                population=int(row["population"]),
                capital=row["capital"] == "1",
            )
            for row in csv.DictReader(fh)
        )


def compute_boost(lat: float, lon: float) -> dict[str, Any]:
    """Newsworthiness boost (points on the 0–100 severity scale) for an event at ``(lat, lon)``.

    Finds the nearest committed population centre (argmin over the dataset, tiebroken by
    ``(round(distance, 6), -population, name)`` to defeat libm ULP noise), then scores
    proximity × population, plus a capital bonus, capped at ``BOOST_CAP``. ``applied`` is
    ``0.0`` beyond ``BOOST_RADIUS_KM`` but ``nearest_place``/``population``/``distance_km`` are
    still populated so the ranking stays auditable ("nearest is X, N km away, no boost").
    """
    cities = _load_cities()
    if not cities:
        return {"nearest_place": None, "population": None, "distance_km": None, "applied": 0.0}
    nearest = min(
        cities,
        key=lambda c: (round(great_circle_km(lat, lon, c.lat, c.lon), 6), -c.population, c.name),
    )
    distance = great_circle_km(lat, lon, nearest.lat, nearest.lon)
    proximity = max(0.0, 1.0 - distance / BOOST_RADIUS_KM)
    pop_weight = min(1.0, math.log10(max(nearest.population, 1)) / 7.0)
    applied = MAX_BOOST * proximity * pop_weight
    if nearest.capital:
        applied += CAPITAL_BONUS * proximity
    applied = min(applied, BOOST_CAP)
    return {
        "nearest_place": nearest.name,
        "population": nearest.population,
        "distance_km": round(distance, 1),
        "applied": round(applied, 3),
    }
