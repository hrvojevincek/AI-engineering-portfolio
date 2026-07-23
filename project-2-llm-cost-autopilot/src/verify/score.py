import json
import re

from src.models.registry import REGISTRY
from src.providers.client import send_request

ESCALATE_BELOW = 4


def normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def score_exact(candidate: str, reference: str) -> tuple[float, bool, str]:
    ok = normalize(candidate) == normalize(reference)
    return (1.0 if ok else 0.0, ok, "exact match" if ok else "mismatch")


def score_label(candidate: str, reference: str) -> tuple[float, bool, str]:
    return score_exact(candidate, reference)


JUDGE_MODEL = "gpt-4o-mini"


def _parse_judge_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < 0:
        raise ValueError(f"No JSON object in judge output: {text!r}")
    return json.loads(text[start : end + 1])


async def score_open(
    prompt: str,
    candidate: str,
    reference: str,
) -> tuple[float, bool, str]:
    judge_prompt = f"""You score whether CANDIDATE matches REFERENCE on the user task.
User task: {prompt}
REFERENCE:
{reference}
CANDIDATE:
{candidate}
Return ONLY JSON: {{"score": <1-5>, "reason": "<one sentence>"}}
Rubric: 5=same facts, 4=small omission OK, 3=important miss, 1-2=wrong."""

    response = await send_request(judge_prompt, REGISTRY[JUDGE_MODEL])
    #  parse JSON from response.text (strip md fences if present)
    data = _parse_judge_json(response.text)
    score = float(data["score"])
    reason = str(data["reason"])
    return score, score >= ESCALATE_BELOW, reason
