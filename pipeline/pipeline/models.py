from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class NormalizedEvent:
    """A single hazard event normalized from a feed, independent of any source's wire format.

    Flat, hazard-generic superset (supersedes NormalizedQuake). EQ-only signals
    (mag, sig, depth_km) are Optional and None for non-earthquake hazards; GDACS-only
    signals (alert_score, glide, iso3, country, affected_*) are None for USGS events.
    """

    feed: str
    source_id: str
    hazard: str
    title: str
    place: str
    time: datetime
    updated: datetime
    lat: float
    lon: float
    url: str
    status: str
    depth_km: float | None
    mag: float | None
    sig: int | None
    alert: str | None
    alert_score: float | None
    glide: str | None
    external_ids: frozenset[str]
    iso3: str | None
    country: str | None
    affected_population: int | None
    affected_basis: str | None
