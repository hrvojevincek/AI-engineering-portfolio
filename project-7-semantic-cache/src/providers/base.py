"""Provider adapters for cache misses."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any, Protocol

from src.proxy.schemas import ChatCompletionRequest


class ChatProvider(Protocol):
    async def chat_completion(self, request: ChatCompletionRequest) -> dict[str, Any]: ...

    async def chat_completion_stream(
        self, request: ChatCompletionRequest
    ) -> AsyncIterator[str]: ...


class FakeChatProvider:
    """Test double — returns a deterministic OpenAI-shaped response."""

    def __init__(
        self,
        content: str = "Python is a programming language.",
        *,
        finish_reason: str = "stop",
    ) -> None:
        self.content = content
        self.finish_reason = finish_reason
        self.call_count = 0
        self.last_request: ChatCompletionRequest | None = None

    async def chat_completion(self, request: ChatCompletionRequest) -> dict[str, Any]:
        self.call_count += 1
        self.last_request = request
        return self._completion_dict(request)

    async def chat_completion_stream(self, request: ChatCompletionRequest) -> AsyncIterator[str]:
        self.call_count += 1
        self.last_request = request
        response_id = "chatcmpl-test"
        words = self.content.split()
        for index, word in enumerate(words):
            delta = word if index == 0 else f" {word}"
            yield self._sse_line(
                {
                    "id": response_id,
                    "object": "chat.completion.chunk",
                    "created": 1700000000,
                    "model": request.model,
                    "choices": [{"index": 0, "delta": {"content": delta}, "finish_reason": None}],
                }
            )
        yield self._sse_line(
            {
                "id": response_id,
                "object": "chat.completion.chunk",
                "created": 1700000000,
                "model": request.model,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 12, "completion_tokens": 8, "total_tokens": 20},
            }
        )
        yield "data: [DONE]\n\n"

    def _completion_dict(self, request: ChatCompletionRequest) -> dict[str, Any]:
        return {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "created": 1700000000,
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": self.content},
                    "finish_reason": self.finish_reason,
                }
            ],
            "usage": {"prompt_tokens": 12, "completion_tokens": 8, "total_tokens": 20},
        }

    @staticmethod
    def _sse_line(payload: dict[str, Any]) -> str:
        return f"data: {json.dumps(payload)}\n\n"
