import json
import os

from openai import AsyncOpenAI

from src.models import (
    CaseResult,
    ClassificationResult,
    GoldenTestCase,
    ThresholdConfig,
)

JUDGE_MODEL = "gpt-4o-mini"

JUDGE_PROMPT = """You rate how well an AI-generated summary captures the same meaning as the reference summary for a customer support email.

Score 1-5:
5 = same meaning, would satisfy a support agent
4 = mostly correct, minor wording differences
3 = partially correct, misses something important
2 = mostly wrong or too vague
1 = completely wrong or unrelated

Respond with JSON only: {"score": <1-5>, "reason": "<brief>"}"""


async def score_summary(
    case: GoldenTestCase,
    actual_summary: str,
    client: AsyncOpenAI,
    judge_model: str = JUDGE_MODEL,
) -> int:
    response = await client.chat.completions.create(
        model=judge_model,
        messages=[
            {"role": "system", "content": JUDGE_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Email:\n{case.input}\n\n"
                    f"Reference summary:\n{case.expected.summary}\n\n"
                    f"AI summary:\n{actual_summary}"
                ),
            },
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )

    content = response.choices[0].message.content
    if not content:
        return 1

    data = json.loads(content)
    score = int(data["score"])
    return max(1, min(5, score))


async def score_case(
    case: GoldenTestCase,
    actual: ClassificationResult,
    latency_ms: float,
    tokens_in: int,
    tokens_out: int,
    client: AsyncOpenAI,
    thresholds: ThresholdConfig,
    skip_judge: bool = False,
) -> CaseResult:
    category_match = actual.category == case.expected.category

    if skip_judge:
        summary_score = 5 if category_match else 1
    else:
        summary_score = await score_summary(case, actual.summary, client)

    passed = category_match and summary_score >= thresholds.summary_pass_score

    return CaseResult(
        case_id=case.id,
        actual=actual,
        category_match=category_match,
        summary_score=summary_score,
        latency_ms=latency_ms,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        passed=passed,
    )


def make_client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
