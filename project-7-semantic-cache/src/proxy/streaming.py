"""SSE helpers for OpenAI-compatible streaming chat completions."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from src.models.types import CacheEntry


def format_sse(payload: dict[str, Any] | str) -> str:
    if isinstance(payload, str):
        return f"data: {payload}\n\n"
    return f"data: {json.dumps(payload)}\n\n"


def parse_sse_payload(line: str) -> dict[str, Any] | None:
    """Parse a single SSE line; return None for [DONE] or non-data lines."""
    if not line.startswith("data: "):
        return None
    payload = line[6:].strip()
    if payload == "[DONE]":
        return None
    return json.loads(payload)


def accumulate_stream_chunk(
    data: dict[str, Any],
    *,
    content: str,
    finish_reason: str | None,
    usage: dict[str, Any] | None,
) -> tuple[str, str | None, dict[str, Any] | None]:
    """Update buffered content/finish_reason/usage from one stream chunk."""
    choices = data.get("choices") or []
    if not choices:
        if usage_data := data.get("usage"):
            usage = usage_data
        return content, finish_reason, usage

    choice = choices[0]
    delta = choice.get("delta") or {}
    if delta_content := delta.get("content"):
        content += delta_content
    if fr := choice.get("finish_reason"):
        finish_reason = fr
    if usage_data := data.get("usage"):
        usage = usage_data
    return content, finish_reason, usage


def build_completion_dict(
    *,
    model: str,
    content: str,
    finish_reason: str,
    usage: dict[str, Any] | None = None,
    response_id: str = "chatcmpl-stream",
) -> dict[str, Any]:
    usage = usage or {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }
    return {
        "id": response_id,
        "object": "chat.completion",
        "created": 1700000000,
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": finish_reason,
            }
        ],
        "usage": usage,
    }


async def stream_cached_entry(entry: CacheEntry) -> AsyncIterator[str]:
    """Synthesize OpenAI SSE from a cached non-stream response."""
    response = entry.response
    model = response.get("model", entry.namespace.model)
    content = response["choices"][0]["message"]["content"]
    response_id = response.get("id", "chatcmpl-cached")

    yield format_sse(
        {
            "id": response_id,
            "object": "chat.completion.chunk",
            "created": response.get("created", 1700000000),
            "model": model,
            "choices": [{"index": 0, "delta": {"role": "assistant", "content": content}, "finish_reason": None}],
        }
    )
    yield format_sse(
        {
            "id": response_id,
            "object": "chat.completion.chunk",
            "created": response.get("created", 1700000000),
            "model": model,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
        }
    )
    yield format_sse("[DONE]")
