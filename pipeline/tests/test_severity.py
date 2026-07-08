import pytest

from pipeline.severity import (
    MAJOR_CUTOFF,
    base_signal,
    is_major,
    level_for,
    severity_level,
)


@pytest.mark.parametrize(
    "mag,sig,alert,level",
    [
        (7.5, 100, None, "severe"),      # mag >= 7.0
        (5.0, 100, "orange", "severe"),  # alert orange
        (5.0, 1000, None, "severe"),     # sig >= 1000
        (6.2, 100, None, "serious"),     # mag >= 6.0
        (5.0, 700, None, "serious"),     # sig >= 600
        (5.0, 100, "yellow", "serious"), # alert yellow
        (4.5, 100, None, "moderate"),    # mag >= 4.5
        (3.0, 300, None, "moderate"),    # sig >= 300
        (3.2, 158, None, "minor"),       # below all
        (2.4, None, None, "minor"),      # null sig treated as 0
        (7.0, 100, None, "severe"),      # mag exactly 7.0 -> severe
        (6.0, 100, None, "serious"),     # mag exactly 6.0 -> serious
        (5.0, 600, None, "serious"),     # sig exactly 600 -> serious
        (4.0, 100, "green", "minor"),    # green alert falls through band checks -> minor
    ],
)
def test_severity_bands(mag, sig, alert, level):
    assert severity_level(mag, sig, alert) == level


@pytest.mark.parametrize(
    "mag,sig,alert,expected_major",
    [
        (5.5, 0, None, True),        # mag threshold, inclusive
        (5.49, 0, None, False),
        (4.0, 600, None, True),      # sig threshold, inclusive
        (4.0, 599, None, False),
        (4.0, 0, "green", True),     # green EQ -> major, v1 quirk preserved
        (4.0, 0, None, False),
        (4.0, None, None, False),    # null sig, null alert
        (7.5, 100, "red", True),     # strongest arm dominates
    ],
)
def test_eq_base_signal_regression(mag, sig, alert, expected_major):
    inputs = {"mag": mag, "sig": sig, "alert": alert, "alert_score": None}
    score = base_signal("EQ", inputs)
    # Cross-check each row against the literal v1 rule, then prove the equivalence.
    v1_is_major = mag >= 5.5 or (sig or 0) >= 600 or alert is not None
    assert v1_is_major is expected_major
    assert (score >= MAJOR_CUTOFF) is expected_major


def test_is_major_threshold():
    assert is_major(59.999) is False
    assert is_major(60.0) is True
    assert is_major(100.0) is True


@pytest.mark.parametrize(
    "hazard,alert,expected_level,expected_major",
    [
        ("TC", "green", "minor", False),     # base 45 < 60
        ("FL", "yellow", "moderate", False), # base 55 < 60
        ("TC", "orange", "serious", True),   # base 75 >= 60
        ("VO", "red", "severe", True),       # base 90 >= 60
    ],
)
def test_gdacs_bands(hazard, alert, expected_level, expected_major):
    inputs = {"mag": None, "sig": None, "alert": alert, "alert_score": 0.0}
    assert level_for(hazard, inputs) == expected_level
    assert is_major(base_signal(hazard, inputs)) is expected_major


def test_gdacs_alert_score_monotonic_and_clamped_within_colour():
    hazard = "FL"

    def sig_in(alert_score):
        return {"mag": None, "sig": None, "alert": "green", "alert_score": alert_score}

    scores = [base_signal(hazard, sig_in(a)) for a in (0.0, 1.0, 2.0, 3.0)]
    # monotonic non-decreasing in alert_score, within the green colour
    assert scores == sorted(scores)
    assert scores[0] == 45.0
    assert scores[-1] == 54.0
    # clamp at 3.0: a larger alert_score cannot push base past the +9 ceiling
    assert base_signal(hazard, sig_in(99.0)) == 54.0
    # green never crosses the major cutoff and the level band never moves off "minor"
    assert all(not is_major(s) for s in scores)
    assert {level_for(hazard, sig_in(a)) for a in (0.0, 1.5, 3.0, 99.0)} == {"minor"}
