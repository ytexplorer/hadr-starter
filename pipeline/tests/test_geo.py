from pipeline.geo import great_circle_km


def test_known_city_pair_london_to_paris():
    # London (51.5074, -0.1278) -> Paris (48.8566, 2.3522) is ~343.5 km.
    dist = great_circle_km(51.5074, -0.1278, 48.8566, 2.3522)
    assert abs(dist - 343.5) < 1.0


def test_identity_same_point_is_zero():
    assert great_circle_km(51.5074, -0.1278, 51.5074, -0.1278) == 0.0


def test_symmetric_in_argument_order():
    ab = great_circle_km(51.5074, -0.1278, 48.8566, 2.3522)
    ba = great_circle_km(48.8566, 2.3522, 51.5074, -0.1278)
    assert ab == ba
