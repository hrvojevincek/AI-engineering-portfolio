import asyncio
import json
import os
import time
from typing import Any, Optional

from openai import AsyncOpenAI

from src.models import ClassificationResult, ClassifyOutput, PromptConfig


def _build_messages(config: PromptConfig, email: str) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": config.system_prompt},
    ]

    for example in config.few_shot_examples:
        messages.append({"role": "user", "content": example.input})
        messages.append(
            {
                "role": "assistant",
                "content": json.dumps(example.output.model_dump(mode="json")),
            }
        )

    messages.append({"role": "user", "content": email})
    return messages


async def classify_email(
    email: str,
    config: PromptConfig,
    client: Optional[AsyncOpenAI] = None,
) -> ClassifyOutput:
    """
    Classify a support email using the prompt config (not hardcoded prompts).

    This is the LLM feature under test — every eval run calls this function.
    """
    owns_client = client is None
    if owns_client:
        client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

    start = time.perf_counter()
    response = await client.chat.completions.create(
        model=config.model,
        messages=_build_messages(config, email),
        response_format={"type": "json_object"},
        temperature=0,
    )
    latency_ms = (time.perf_counter() - start) * 1000

    content = response.choices[0].message.content
    if not content:
        raise ValueError("Empty response from LLM")

    usage = response.usage
    return ClassifyOutput(
        result=ClassificationResult.model_validate_json(content),
        latency_ms=latency_ms,
        tokens_in=usage.prompt_tokens if usage else 0,
        tokens_out=usage.completion_tokens if usage else 0,
    )


async def _demo() -> None:
    from src.feature.prompts import load_prompt

    config = load_prompt("1.0.0")
    sample_email = (
        "Hello, I upgraded to the Pro plan yesterday but my dashboard "
        "still shows Free. Can you fix my account?"
    )

    output = await classify_email(sample_email, config)
    print(f"Prompt version: {config.version}")
    print(f"Model: {config.model}")
    print(f"Category: {output.result.category.value}")
    print(f"Summary: {output.result.summary}")
    print(
        f"Latency: {output.latency_ms:.0f}ms | Tokens: {output.tokens_in}+{output.tokens_out}"
    )


if __name__ == "__main__":
    asyncio.run(_demo())
