"""Deterministic earthquake severity band and `major` gate (ADR 0003, base signal only)."""

Level = str  # one of: "minor" | "moderate" | "serious" | "severe"


def severity_level(mag: float, sig: int | None, alert: str | None) -> Level:
    s = sig or 0
    if alert in ("orange", "red") or mag >= 7.0 or s >= 1000:
        return "severe"
    if alert == "yellow" or mag >= 6.0 or s >= 600:
        return "serious"
    if mag >= 4.5 or s >= 300:
        return "moderate"
    return "minor"


def is_major(mag: float, sig: int | None, alert: str | None) -> bool:
    return mag >= 5.5 or (sig or 0) >= 600 or alert is not None
