from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class NormalizedQuake:
    """A single earthquake normalized from a feed, independent of any source's wire format."""

    source_id: str
    title: str
    place: str
    time: datetime
    updated: datetime
    lat: float
    lon: float
    depth_km: float | None
    mag: float
    sig: int | None
    alert: str | None
    status: str
    url: str
