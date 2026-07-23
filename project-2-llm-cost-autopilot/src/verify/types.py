from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VerifyResult:
    passed: bool
    score: float
    reason: str
    reference_text: str
    reference_cost: float
    reference_model_id: str
    kind: str


@dataclass
class EscalationResult:
    """Final text after optional escalate-to-reference."""

    text: str
    escalated: bool
    verify: VerifyResult
    # Extra $ spent on the reference call when we escalate (0 if already paid only for verify)
    cost_delta: float
    original_model_id: str | None
    final_model_id: str
