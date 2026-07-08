"""Deterministic per-hazard severity: base band (`level`) + 0–100 `base_signal` + `major` gate.

Routes by *hazard*, not feed (ADR 0003). `level` (the frozen 4-value band) and the numeric
`base_signal` (which feeds `score = base_signal + boost.applied` and gates `major`) stay
separate. `severity_level` is FROZEN verbatim from Slice 1. The EQ `base_signal` arms are
constructed so `base_signal >= MAJOR_CUTOFF` holds IFF the v1 rule
`is_major(mag>=5.5 or sig>=600 or alert is not None)` held — a provable regression that
preserves the v1 "green EQ -> major" quirk (deviation §10.6).
"""

from typing import Any

Level = str  # one of: "minor" | "moderate" | "serious" | "severe"

MAJOR_CUTOFF = 60.0

# EQ arm: any non-null PAGER alert already cleared the v1 gate, so every colour maps >= 60.
_EQ_ALERT_ARM: dict[str | None, float] = {
    None: 0.0,
    "green": 60.0,
    "yellow": 70.0,
    "orange": 85.0,
    "red": 100.0,
}

# GDACS non-EQ colour -> base points and base band. alert_score (clamped to 0–3) only refines
# ordering *within* a colour; it never crosses a level band.
_COLOUR_BASE: dict[str | None, float] = {"green": 45.0, "yellow": 55.0, "orange": 75.0, "red": 90.0}
_COLOUR_LEVEL: dict[str | None, Level] = {
    "green": "minor",
    "yellow": "moderate",
    "orange": "serious",
    "red": "severe",
}


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def severity_level(mag: float, sig: int | None, alert: str | None) -> Level:
    s = sig or 0
    if alert in ("orange", "red") or mag >= 7.0 or s >= 1000:
        return "severe"
    if alert == "yellow" or mag >= 6.0 or s >= 600:
        return "serious"
    if mag >= 4.5 or s >= 300:
        return "moderate"
    return "minor"


def base_signal(hazard: str, inputs: dict[str, Any]) -> float:
    """Numeric 0–100 base signal, routed by hazard. The boost is added later (contract.py)."""
    if hazard == "EQ":
        mag = float(inputs.get("mag") or 0.0)
        sig = inputs.get("sig") or 0
        mag_arm = _clamp(mag / 5.5 * 60.0, 0.0, 100.0)
        sig_arm = _clamp(sig * 0.1, 0.0, 100.0)
        alert_arm = _EQ_ALERT_ARM.get(inputs.get("alert"), 0.0)
        return max(mag_arm, sig_arm, alert_arm)
    base = _COLOUR_BASE.get(inputs.get("alert"), 0.0)
    return base + _clamp(inputs.get("alert_score") or 0.0, 0.0, 3.0) * 3.0


def level_for(hazard: str, inputs: dict[str, Any]) -> Level:
    """Base band (`level`), routed by hazard. Never moved by the boost."""
    if hazard == "EQ":
        mag = float(inputs.get("mag") or 0.0)
        return severity_level(mag, inputs.get("sig"), inputs.get("alert"))
    return _COLOUR_LEVEL.get(inputs.get("alert"), "minor")


def is_major(score: float) -> bool:
    return score >= MAJOR_CUTOFF
