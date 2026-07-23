"""Log escalations as new classifier training examples (flywheel)."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

ANALYZE_VERBS = (
    "analyze",
    "compare",
    "evaluate",
    "reason",
    "assess",
    "contrast",
    "critique",
    "justify",
)

ROOT = Path(__file__).resolve().parents[2]
FAILURES_PATH = ROOT / "data" / "prompts" / "failures.jsonl"


def extract_features(prompt: str) -> dict:
    """Best-effort features from raw prompt text (same fields as v1.0.0.json)."""
    lower = prompt.lower()
    words = prompt.split()
    # Heuristic constraints: quoted rules / "only" / bullet counts
    num_constraints = sum(
        1
        for marker in (
            " only",
            " under ",
            " in ",
            " bullets",
            " sentences",
            " paragraphs",
        )
        if marker in lower
    )
    has_context = any(
        m in lower
        for m in ("given:", "from '", "extract", "contact ", "total due")
    )
    if "json" in lower or "markdown" in lower or "paragraph" in lower:
        fmt = "high"
    elif "bullet" in lower or "summar" in lower or "list" in lower:
        fmt = "medium"
    else:
        fmt = "low"
    return {
        "token_count": len(words),
        "has_analyze_verb": any(v in lower for v in ANALYZE_VERBS),
        "num_constraints": max(1, num_constraints) if num_constraints else 1,
        "has_context": has_context,
        "output_format_complexity": fmt,
    }


def bump_tier(routed_tier: int | None) -> int:
    """Mis-route → label one tier higher (cap at 3)."""
    if routed_tier is None:
        return 2
    return min(3, max(1, routed_tier) + 1)


def log_escalation_failure(
    prompt: str,
    *,
    routed_tier: int | None = None,
    routed_model_id: str | None = None,
    verify_score: float | None = None,
    reason: str | None = None,
    path: Path | None = None,
) -> dict:
    """
    Append one JSONL row matching the complexity dataset schema.
    Returns the row written.
    """
    path = path or FAILURES_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    tier = bump_tier(routed_tier)
    row = {
        "id": f"fail-{uuid.uuid4().hex[:10]}",
        "prompt": prompt,
        "tier": tier,
        "features": extract_features(prompt),
        "notes": (
            f"auto: escalated from verify "
            f"(routed_tier={routed_tier}, model={routed_model_id}, "
            f"score={verify_score}, reason={reason!r})"
        ),
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    return row


def load_failure_rows(path: Path | None = None) -> list[dict]:
    path = path or FAILURES_PATH
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows
