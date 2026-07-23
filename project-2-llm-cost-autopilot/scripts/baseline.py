"""Baseline: same prompts through every OpenAI model; log cost/latency."""

import asyncio
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from src.models.registry import REGISTRY
from src.providers.client import send_request

# Project root on sys.path so `src.*` imports work when run as a script
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")


PROMPTS = [
    "Extract the email address: Contact jane@acme.com about billing.",
    "Rewrite in lowercase: HELLO WORLD",
    "What is 17 + 25? Answer with the number only.",
    "Classify sentiment as positive/negative/neutral: 'This product is okay.'",
    "Summarize in one sentence: The team shipped v2 on Monday after fixing three bugs in checkout.",
    "List three bullet points of risks for migrating a monolith to microservices.",
    "Compare PostgreSQL vs SQLite for a small internal tool. Two short paragraphs.",
    "Write a polite rejection email for a late job application. Keep it under 80 words.",
    "Given: 'Order #4421 was refunded yesterday.' Answer: was it refunded? yes/no.",
    "Explain recursion to a beginner in 3 sentences.",
]

OUT = ROOT / "data" / "baseline_results.json"


async def main() -> None:
    models = [m for m in REGISTRY.values() if m.provider == "openai"]
    rows = []

    for i, prompt in enumerate(PROMPTS):
        for model in models:
            r = await send_request(prompt, model)
            rows.append(
                {
                    "prompt_id": i,
                    "prompt": prompt,
                    "model_id": r.model_id,
                    "latency_ms": r.latency_ms,
                    "input_tokens": r.input_tokens,
                    "output_tokens": r.output_tokens,
                    "cost": r.cost,
                    "text_preview": r.text[:120],
                }
            )
            print(f"[{i}] {r.model_id}: ${r.cost:.6f} {r.latency_ms:.0f}ms")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rows, indent=2))
    print(f"Saved {len(rows)} rows to {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
