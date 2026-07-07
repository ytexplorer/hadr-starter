import pytest

from pipeline.severity import is_major, severity_level


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
    "mag,sig,alert,expected",
    [
        (5.5, 0, None, True),        # mag threshold, inclusive
        (5.49, 0, None, False),
        (4.0, 600, None, True),      # sig threshold, inclusive
        (4.0, 599, None, False),
        (4.0, 0, "green", True),     # any non-null alert
        (4.0, None, None, False),    # null sig, null alert
    ],
)
def test_major_gate(mag, sig, alert, expected):
    assert is_major(mag, sig, alert) is expected
