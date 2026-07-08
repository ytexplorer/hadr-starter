"""GDACS per-event exposure ("affected") extraction — carried verbatim, never computed (ADR 0007)."""

from typing import Any

# Per-hazard population-EXPOSURE field inside the GDACS `geteventdata` properties, as
# (detail_object_key, population_field, description_field). Only EQ is retained: it is
# API-verified — earthquakedetails.rapidpop (+ rapidpopdescription) is a genuine
# exposed-population count. The non-EQ hazards were checked against captured detail fixtures
# (Step 8): TC and FL carry NO exposed-population count (their `severitydata` block holds the
# physical magnitude — max wind speed / flood magnitude — not a population); VO and DR had no
# active event in the list feed this slice and stay unverified. All non-EQ hazards are therefore
# omitted from this map and fall through to (None, reason): we carry the figure VERBATIM, never
# fabricate or derive one, and ship no unverified extraction path (ADR 0007). feeds/gdacs.md
# records the per-hazard field map.
_EXPOSURE_FIELDS: dict[str, tuple[str, str, str]] = {
    "EQ": ("earthquakedetails", "rapidpop", "rapidpopdescription"),
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
