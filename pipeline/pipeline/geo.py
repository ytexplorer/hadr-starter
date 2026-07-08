"""Great-circle distance on a spherical Earth (haversine).

Kept as one implementation, shared by the newsworthiness boost (§7.2) and the
dedup tier-3 geo test (§7.4), so distance semantics can't drift between ranking
and merging. Pure and deterministic; stdlib `math` only.
"""

import math

EARTH_RADIUS_KM = 6371.0088


def great_circle_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))
