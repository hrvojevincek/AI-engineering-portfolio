import os

from openai import AsyncOpenAI

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        _client = AsyncOpenAI(api_key=api_key)
    return _client


async def openai_complete(prompt: str, model_id: str) -> tuple[str, int, int]:
    """Call OpenAI chat completions. Returns (text, input_tokens, output_tokens)."""
    response = await _get_client().chat.completions.create(
        model=model_id,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.choices[0].message.content or ""
    usage = response.usage
    in_tok = usage.prompt_tokens if usage else 0
    out_tok = usage.completion_tokens if usage else 0
    return text, in_tok, out_tok
