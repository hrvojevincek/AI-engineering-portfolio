import time

from src.models.registry import ModelConfig
from src.models.types import Response
from src.providers.openai import openai_complete


async def send_request(prompt: str, model: ModelConfig) -> Response:
    t0 = time.perf_counter()
    if model.provider == "openai":
        text, in_tok, out_tok = await openai_complete(prompt, model.model_id)
    elif model.provider == "anthropic":
        raise NotImplementedError("Anthropic adapter not wired yet")
    else:
        raise NotImplementedError(f"Provider {model.provider} not implemented")
    latency_ms = (time.perf_counter() - t0) * 1000
    cost = (
        in_tok * model.cost_per_input_token
        + out_tok * model.cost_per_output_token
    )
    return Response(
        text=text,
        latency_ms=latency_ms,
        cost=cost,
        model_id=model.model_id,
        provider=model.provider,
        input_tokens=in_tok,
        output_tokens=out_tok,
    )
