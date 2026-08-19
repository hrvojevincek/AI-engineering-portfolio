"""OpenAI provider — forwards cache misses to the real API."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from typing import Any

from openai import AsyncOpenAI

from src.proxy.schemas import ChatCompletionRequest
from src.proxy.streaming import format_sse


class OpenAIChatProvider:
    def __init__(self, client: AsyncOpenAI | None = None) -> None:
        self.client = client or AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    async def chat_completion(self, request: ChatCompletionRequest) -> dict[str, Any]:
        response = await self.client.chat.completions.create(
            model=request.model,
            messages=request.as_message_dicts(),
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=False,
        )
        return response.model_dump()

    async def chat_completion_stream(
        self, request: ChatCompletionRequest
    ) -> AsyncIterator[str]:
        stream = await self.client.chat.completions.create(
            model=request.model,
            messages=request.as_message_dicts(),
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=True,
        )
        async for chunk in stream:
            yield format_sse(chunk.model_dump(exclude_none=True))
        yield format_sse("[DONE]")
