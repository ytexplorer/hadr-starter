"""GDACS per-event exposure ("affected") extraction — carried verbatim, never computed (ADR 0007)."""

from typing import Any

# Per-hazard population-EXPOSURE fields inside the GDACS `geteventdata` properties, as
# (detail_object_key, population_field, description_field). EQ is API-verified
# (earthquakedetails.rapidpop + rapidpopdescription). The non-EQ hazards use GDACS's
# `severitydata` block (population + severitytext) — the EXPECTED path, CONFIRMED or corrected
# per hazard against captured detail fixtures in Step 8-9 (feeds/gdacs.md records the final map).
# If a detail lacks its pinned field, extract_exposure returns (None, reason): we carry the
# figure VERBATIM and never fabricate or derive one (ADR 0007). Any hazard we cannot verify is
# removed from this map (ships null + reason) rather than shipping an unverified extraction path.
_EXPOSURE_FIELDS: dict[str, tuple[str, str, str]] = {
    "EQ": ("earthquakedetails", "rapidpop", "rapidpopdescription"),
    "TC": ("severitydata", "population", "severitytext"),
    "FL": ("severitydata", "population", "severitytext"),
    "VO": ("severitydata", "population", "severitytext"),
    # DR (drought) is intentionally absent: GDACS publishes no per-event population count for
    # droughts, so DR always ships (None, reason). Confirmed by the Step 8 capture.
}

_NO_FIGURE_REASON: dict[str, str] = {
    "EQ": "GDACS earthquake detail carried no rapidpop figure",
    "TC": "GDACS tropical-cyclone detail publishes no exposed-population figure",
    "FL": "GDACS flood detail publishes no exposed-population figure",
    "VO": "GDACS volcano detail publishes no exposed-population figure",
    "DR": "GDACS drought detail publishes no exposed-population figure",
}
_UNKNOWN_REASON = "no GDACS exposure figure for this hazard"


def _properties(detail_json: dict[str, Any]) -> dict[str, Any]:
    """Locate the event `properties` in a GDACS geteventdata response.

    geteventdata returns a GeoJSON Feature (properties inline) or, defensively, a
    FeatureCollection; a bare properties dict is also accepted. Mirrors the parsers'
    defensive shape-reading (feeds/usgs.py).
    """
    if "features" in detail_json:
        feats = detail_json.get("features") or []
        first = feats[0] if feats else {}
        props: dict[str, Any] = first.get("properties") or {}
        return props
    inline: dict[str, Any] = detail_json.get("properties") or detail_json
    return inline


def extract_exposure(hazard: str, detail_json: dict[str, Any]) -> tuple[int | None, str]:
    """Return (population_exposed, basis_text) read VERBATIM from a GDACS geteventdata detail.

    A hazard GDACS does not quantify, or a detail missing its exposure field, returns
    (None, <documented reason>) — never a computed or derived number (ADR 0007).
    """
    fields = _EXPOSURE_FIELDS.get(hazard)
    if fields is not None:
        obj_key, pop_field, desc_field = fields
        detail: dict[str, Any] = _properties(detail_json).get(obj_key) or {}
        pop = detail.get(pop_field)
        if pop is not None:
            desc = detail.get(desc_field)
            return int(pop), (str(desc) if desc is not None else "")
    return None, _NO_FIGURE_REASON.get(hazard, _UNKNOWN_REASON)


def affected_block(population: int | None, basis_text: str | None) -> dict[str, Any]:
    """Shape the contract `affected` object (always present; FE branches on estimate===null)."""
    if population is None:
        return {
            "estimate": None,
            "basis": basis_text or "no GDACS exposure figure available",
            "source": None,
        }
    return {"estimate": int(population), "basis": basis_text or "", "source": "gdacs"}
