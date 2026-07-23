from src.models.registry import REGISTRY
from src.providers.client import send_request
from src.verify.score import score_exact, score_label, score_open
from src.verify.types import VerifyResult

REFERENCE_KEY = "gpt-4o"


async def verify(
    prompt: str,
    candidate_text: str,
    *,
    kind: str = "open",
    routed_model_id: str | None = None,
) -> VerifyResult:
    # 1) skip if already on reference model
    if routed_model_id == REFERENCE_KEY:
        return VerifyResult(
            passed=True,
            score=5.0,
            reason="skipped: already on reference",
            reference_text=candidate_text,
            reference_cost=0.0,
            reference_model_id=REFERENCE_KEY,
            kind=kind,
        )
    # 2) get reference answer
    ref = await send_request(prompt, REGISTRY[REFERENCE_KEY])

    # 3) score
    if kind in ["exact", "label"]:
        score, passed, reason = (
            score_exact(candidate_text, ref.text)
            if kind == "exact"
            else score_label(candidate_text, ref.text)
        )
    else:
        score, passed, reason = await score_open(
            prompt, candidate_text, ref.text
        )

    return VerifyResult(
        passed=passed,
        score=score,
        reason=reason,
        reference_text=ref.text,
        reference_cost=ref.cost,
        reference_model_id=ref.model_id,
        kind=kind,
    )
