"""Route cache misses to the correct upstream LLM provider."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from fastapi import HTTPException

from src.cache.namespace import infer_provider
from src.models.types import Provider
from src.providers.base import ChatProvider
from src.providers.openai_provider import OpenAIChatProvider
from src.proxy.schemas import ChatCompletionRequest


class ProviderRouter:
    def __init__(
        self,
        openai: ChatProvider | None = None,
        anthropic: ChatProvider | None = None,
        ollama: ChatProvider | None = None,
    ) -> None:
        self._providers: dict[Provider, ChatProvider] = {
            Provider.OPENAI: openai or OpenAIChatProvider(),
            Provider.ANTHROPIC: anthropic or _unsupported("Anthropic"),
            Provider.OLLAMA: ollama or _unsupported("Ollama"),
        }

    def resolve(self, model: str) -> ChatProvider:
        provider = infer_provider(model)
        return self._providers[provider]


def _unsupported(name: str) -> ChatProvider:
    class _Stub:
        async def chat_completion(self, request: ChatCompletionRequest) -> dict[str, Any]:
            raise HTTPException(
                status_code=501,
                detail=f"{name} provider not implemented yet; use an OpenAI gpt-* model for now.",
            )

        async def chat_completion_stream(
            self, request: ChatCompletionRequest
        ) -> AsyncIterator[str]:
            raise HTTPException(
                status_code=501,
                detail=f"{name} provider not implemented yet; use an OpenAI gpt-* model for now.",
            )
            yield ""  # pragma: no cover

    return _Stub()  # type: ignore[return-value]
