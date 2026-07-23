"""Auto-escalate to the reference answer when verify fails."""

from __future__ import annotations

from src.verify.feedback import log_escalation_failure
from src.verify.types import EscalationResult
from src.verify.verifier import REFERENCE_KEY, verify


async def respond_with_escalation(
    prompt: str,
    candidate_text: str,
    *,
    kind: str = "open",
    routed_model_id: str | None = None,
    routed_tier: int | None = None,
    candidate_cost: float = 0.0,
    log_failure: bool = True,
) -> EscalationResult:
    """
    Verify the cheap answer; on failure reuse the reference text from verify
    (no second gpt-4o call) and optionally log a classifier training row.
    """
    result = await verify(
        prompt,
        candidate_text,
        kind=kind,
        routed_model_id=routed_model_id,
    )

    if result.passed:
        return EscalationResult(
            text=candidate_text,
            escalated=False,
            verify=result,
            cost_delta=0.0,
            original_model_id=routed_model_id,
            final_model_id=routed_model_id or "unknown",
        )

    if log_failure:
        log_escalation_failure(
            prompt,
            routed_tier=routed_tier,
            routed_model_id=routed_model_id,
            verify_score=result.score,
            reason=result.reason,
        )

    cost_delta = max(0.0, result.reference_cost - candidate_cost)
    return EscalationResult(
        text=result.reference_text,
        escalated=True,
        verify=result,
        cost_delta=cost_delta,
        original_model_id=routed_model_id,
        final_model_id=result.reference_model_id or REFERENCE_KEY,
    )
