"""Cost savings vs always using the baseline (gpt-4o) model."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from src.models.registry import REGISTRY

BASELINE_KEY = "gpt-4o"


@dataclass(frozen=True)
class CostStats:
    n_requests: int
    n_with_tokens: int
    actual_cost: float
    baseline_cost: float
    saved: float
    saved_pct: float
    escalation_rate: float


def _baseline_cost_for_row(row: sqlite3.Row) -> float | None:
    """What this call would cost on gpt-4o given token counts."""
    in_tok = row["input_tokens"]
    out_tok = row["output_tokens"]
    if in_tok is None or out_tok is None:
        return None
    base = REGISTRY[BASELINE_KEY]
    return (
        int(in_tok) * base.cost_per_input_token
        + int(out_tok) * base.cost_per_output_token
    )


def compute_savings(rows: list[sqlite3.Row]) -> CostStats:
    actual = 0.0
    baseline = 0.0
    n_tokens = 0
    n_escalated = 0

    for row in rows:
        actual += float(row["cost"] or 0.0)
        n_escalated += int(row["escalated"] or 0)
        b = _baseline_cost_for_row(row)
        if b is None:
            # No tokens: fall back to logged cost (no savings attributed)
            baseline += float(row["cost"] or 0.0)
        else:
            baseline += b
            n_tokens += 1

    n = len(rows)
    saved = baseline - actual
    saved_pct = (saved / baseline * 100.0) if baseline > 0 else 0.0
    esc_rate = (n_escalated / n) if n else 0.0

    return CostStats(
        n_requests=n,
        n_with_tokens=n_tokens,
        actual_cost=actual,
        baseline_cost=baseline,
        saved=saved,
        saved_pct=saved_pct,
        escalation_rate=esc_rate,
    )
