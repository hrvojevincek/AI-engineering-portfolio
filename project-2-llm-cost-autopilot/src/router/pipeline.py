"""End-to-end: classify → route → send → verify/escalate → audit log."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from typing import Any, Literal

from src.audit.db import get_conn
from src.audit.store import log_request
from src.providers.client import send_request
from src.router.classify import predict_tier
from src.router.routing import model_for_tier
from src.verify.escalate import respond_with_escalation

Kind = Literal["exact", "label", "open"]


@dataclass
class CompletionResult:
    text: str
    tier: int
    routed_model: str
    final_model: str
    escalated: bool
    cost: float
    latency_ms: float
    quality_score: float
    verify_reason: str
    input_tokens: int
    output_tokens: int
    kind: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


async def complete(
    prompt: str,
    *,
    kind: Kind = "open",
    log: bool = True,
) -> CompletionResult:
    t0 = time.perf_counter()
    tier = predict_tier(prompt)
    model = model_for_tier(tier)

    response = await send_request(prompt, model)
    esc = await respond_with_escalation(
        prompt,
        response.text,
        kind=kind,
        routed_model_id=model.model_id,
        routed_tier=tier,
        candidate_cost=response.cost,
    )

    # Candidate + verifier reference call (0 if verify skipped)
    total_cost = response.cost + esc.verify.reference_cost
    latency_ms = (time.perf_counter() - t0) * 1000

    if log:
        with get_conn() as conn:
            log_request(
                conn,
                prompt=prompt,
                complexity_tier=tier,
                routed_model=model.model_id,
                final_model=esc.final_model_id,
                cost=total_cost,
                latency_ms=latency_ms,
                quality_score=esc.verify.score,
                escalated=esc.escalated,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
            )

    return CompletionResult(
        text=esc.text,
        tier=tier,
        routed_model=model.model_id,
        final_model=esc.final_model_id,
        escalated=esc.escalated,
        cost=total_cost,
        latency_ms=latency_ms,
        quality_score=esc.verify.score,
        verify_reason=esc.verify.reason,
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
        kind=kind,
    )


if __name__ == "__main__":
    import asyncio

    from dotenv import load_dotenv

    load_dotenv()

    async def _main() -> None:
        r = await complete(
            "What is 17 + 25? Answer with the number only.",
            kind="exact",
        )
        print(r.to_dict())

    asyncio.run(_main())
