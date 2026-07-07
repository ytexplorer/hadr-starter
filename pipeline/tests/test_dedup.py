from datetime import datetime, timezone

from pipeline.dedup import union_by_id
from pipeline.models import NormalizedQuake


def _q(source_id: str, updated_min: int, mag: float = 5.0) -> NormalizedQuake:
    return NormalizedQuake(
        source_id=source_id, title="t", place="p",
        time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated=datetime(2026, 1, 1, minute=updated_min, tzinfo=timezone.utc),
        lat=0.0, lon=0.0, depth_km=None, mag=mag, sig=None, alert=None,
        status="reviewed", url="http://u",
    )


def test_collapses_same_id_keeping_higher_updated():
    old = _q("shared", updated_min=1, mag=5.0)
    new = _q("shared", updated_min=9, mag=5.4)
    result = union_by_id([old, new])
    assert len(result) == 1
    assert result[0].mag == 5.4  # the newer record won


def test_newer_wins_regardless_of_input_order():
    old = _q("shared", updated_min=1, mag=5.0)
    new = _q("shared", updated_min=9, mag=5.4)
    # newer record placed FIRST — must still win
    result = union_by_id([new, old])
    assert len(result) == 1
    assert result[0].mag == 5.4


def test_distinct_ids_all_survive():
    result = union_by_id([_q("a", 1), _q("b", 1)])
    assert {q.source_id for q in result} == {"a", "b"}


def test_empty_input():
    assert union_by_id([]) == []
