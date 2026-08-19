"""Phase 3.3 — replay queries at different similarity thresholds."""

from __future__ import annotations

from dataclasses import dataclass

from src.cache.lookup import classify_lookup
from src.models.types import LookupStatus
from src.policies.query_log import QueryRecord


@dataclass(frozen=True)
class ThresholdSimulation:
    threshold: float
    hit_rate: float
    miss_rate: float
    near_miss_rate: float
    paraphrase_hit_rate: float


def _is_paraphrase_hit(record: QueryRecord, threshold: float) -> bool:
    if record.best_similarity is None or record.best_similarity < threshold:
        return False
    if not record.matched_prompt_text:
        return False
    return record.matched_prompt_text.strip() != record.prompt_text.strip()


def simulate_threshold(records: list[QueryRecord], threshold: float) -> ThresholdSimulation:
    if not records:
        return ThresholdSimulation(
            threshold=threshold,
            hit_rate=0.0,
            miss_rate=0.0,
            near_miss_rate=0.0,
            paraphrase_hit_rate=0.0,
        )

    hits = near_misses = misses = paraphrase_hits = 0
    for record in records:
        result = classify_lookup(record.best_similarity, threshold=threshold)
        if result.status == LookupStatus.HIT:
            hits += 1
            if _is_paraphrase_hit(record, threshold):
                paraphrase_hits += 1
        elif result.status == LookupStatus.NEAR_MISS:
            near_misses += 1
        else:
            misses += 1

    total = len(records)
    return ThresholdSimulation(
        threshold=threshold,
        hit_rate=round(hits / total, 4),
        miss_rate=round(misses / total, 4),
        near_miss_rate=round(near_misses / total, 4),
        paraphrase_hit_rate=round(paraphrase_hits / total, 4),
    )


def simulate_thresholds(
    records: list[QueryRecord],
    thresholds: list[float],
) -> list[ThresholdSimulation]:
    unique = sorted(set(thresholds))
    return [simulate_threshold(records, threshold) for threshold in unique]
