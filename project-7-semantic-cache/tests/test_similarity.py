"""Phase 1.2 tests — run: pytest tests/test_similarity.py tests/test_lookup.py -v"""

import math

import pytest

from src.cache.lookup import (
    DEFAULT_THRESHOLD,
    VectorCandidate,
    classify_lookup,
    find_best_match,
    lookup,
)
from src.cache.similarity import cosine_similarity
from src.models.types import LookupStatus


def test_identical_vectors_similarity_is_one():
    vec = [1.0, 0.0, 0.0]
    assert cosine_similarity(vec, vec) == pytest.approx(1.0)


def test_orthogonal_vectors_similarity_is_zero():
    a = [1.0, 0.0]
    b = [0.0, 1.0]
    assert cosine_similarity(a, b) == pytest.approx(0.0)


def test_opposite_vectors_similarity_is_negative_one():
    a = [1.0, 0.0]
    b = [-1.0, 0.0]
    assert cosine_similarity(a, b) == pytest.approx(-1.0)


def test_zero_vector_returns_zero():
    assert cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0
