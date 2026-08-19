"""Phase 1.2 lookup tests — uses fake vectors, no OpenAI/Redis yet."""

import pytest

from src.cache.lookup import (
    DEFAULT_THRESHOLD,
    VectorCandidate,
    classify_lookup,
    find_best_match,
    lookup,
)
from src.models.types import LookupStatus


@pytest.fixture
def candidates() -> list[VectorCandidate]:
    return [
        VectorCandidate(entry_id="python", embedding=[1.0, 0.0, 0.0]),
        VectorCandidate(entry_id="java", embedding=[0.0, 1.0, 0.0]),
    ]


def test_find_best_match_returns_closest(candidates):
    query = [0.99, 0.01, 0.0]  # closer to python
    best, score = find_best_match(query, candidates)
    assert best is not None
    assert best.entry_id == "python"
    assert score is not None
    assert score > 0.9


def test_classify_hit_at_or_above_threshold():
    result = classify_lookup(0.97, threshold=0.95, entry_id="abc")
    assert result.status == LookupStatus.HIT
    assert result.similarity == 0.97
    assert result.entry_id == "abc"


def test_classify_miss_below_near_miss_band():
    result = classify_lookup(0.80, threshold=0.95, entry_id="abc")
    assert result.status == LookupStatus.MISS


def test_classify_near_miss_just_below_threshold():
    result = classify_lookup(0.93, threshold=0.95, entry_id="abc")
    assert result.status == LookupStatus.NEAR_MISS


def test_classify_miss_when_no_candidate():
    result = classify_lookup(None, threshold=DEFAULT_THRESHOLD)
    assert result.status == LookupStatus.MISS
    assert result.entry_id is None


def test_lookup_hit_on_paraphrase_direction(candidates):
    # Same direction as "python" entry → should HIT at 0.95 threshold
    query = [1.0, 0.0, 0.0]
    result = lookup(query, candidates, threshold=0.95)
    assert result.status == LookupStatus.HIT
    assert result.entry_id == "python"


def test_lookup_miss_on_unrelated_query(candidates):
    query = [0.0, 0.0, 1.0]  # orthogonal to both stored entries
    result = lookup(query, candidates, threshold=0.95)
    assert result.status == LookupStatus.MISS
