"""Phase 1.2 — decide HIT/MISS from nearest-neighbor similarity."""

from __future__ import annotations

from dataclasses import dataclass

from src.cache.similarity import cosine_similarity
from src.models.types import LookupResult, LookupStatus

DEFAULT_THRESHOLD = 0.95
NEAR_MISS_GAP = 0.03  # similarity within this band below threshold → NEAR_MISS


@dataclass(frozen=True)
class VectorCandidate:
    """In-memory stand-in until RedisVL storage (Phase 1.3)."""

    entry_id: str
    embedding: list[float]


def find_best_match(
    query: list[float],
    candidates: list[VectorCandidate],
) -> tuple[VectorCandidate | None, float | None]:
    """Return the closest candidate and its similarity score."""
    if not candidates:
        return None, None

    best = candidates[0]
    best_score = cosine_similarity(query, best.embedding)

    for candidate in candidates[1:]:
        score = cosine_similarity(query, candidate.embedding)
        if score > best_score:
            best, best_score = candidate, score

    return best, best_score


def classify_lookup(
    similarity: float | None,
    *,
    threshold: float = DEFAULT_THRESHOLD,
    entry_id: str | None = None,
) -> LookupResult:
    """Map a similarity score to HIT / NEAR_MISS / MISS."""
    if similarity is None:
        return LookupResult(
            status=LookupStatus.MISS,
            similarity=None,
            entry_id=None,
            threshold=threshold,
        )

    if similarity >= threshold:
        status = LookupStatus.HIT
    elif similarity >= threshold - NEAR_MISS_GAP:
        status = LookupStatus.NEAR_MISS
    else:
        status = LookupStatus.MISS

    return LookupResult(
        status=status,
        similarity=similarity,
        entry_id=entry_id if status == LookupStatus.HIT else None,
        threshold=threshold,
    )


def lookup(
    query: list[float],
    candidates: list[VectorCandidate],
    *,
    threshold: float = DEFAULT_THRESHOLD,
) -> LookupResult:
    """End-to-end: find nearest neighbor, then classify."""
    best, score = find_best_match(query, candidates)
    return classify_lookup(
        score,
        threshold=threshold,
        entry_id=best.entry_id if best else None,
    )
