"""FastAPI proxy — OpenAI-compatible chat completions with semantic cache."""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response, StreamingResponse

from src.cache.embed import OpenAIEmbedder
from src.cache.lookup import DEFAULT_THRESHOLD
from src.cache.namespace import build_namespace, extract_user_text
from src.cache.store import CacheService, MemoryCacheStore
from src.models.types import CacheNamespace, LookupStatus
from src.policies.ttl import TTLPolicy
from src.providers.router import ProviderRouter
from src.proxy.schemas import ChatCompletionRequest
from src.proxy.streaming import (
    accumulate_stream_chunk,
    build_completion_dict,
    parse_sse_payload,
    stream_cached_entry,
)

load_dotenv()


def _threshold() -> float:
    return float(os.getenv("CACHE_SIMILARITY_THRESHOLD", DEFAULT_THRESHOLD))


def _cache_hit_headers(similarity: float) -> dict[str, str]:
    return {
        "X-Cache": "HIT",
        "X-Cache-Similarity": f"{similarity:.4f}",
    }


def _cache_miss_headers(prompt_text: str, *, ttl_policy: TTLPolicy) -> dict[str, str]:
    tier = ttl_policy.tier_for(prompt_text)
    return {
        "X-Cache": "MISS",
        "X-Cache-TTL-Tier": tier.value,
    }


def _should_cache_upstream(upstream: dict[str, Any]) -> bool:
    choices = upstream.get("choices") or []
    if not choices:
        return False
    choice = choices[0]
    if choice.get("finish_reason") != "stop":
        return False
    message = choice.get("message") or {}
    return bool(message.get("content"))


def _store_upstream_response(
    cache_service: CacheService,
    namespace: CacheNamespace,
    prompt_text: str,
    upstream: dict[str, Any],
    *,
    ttl_policy: TTLPolicy,
) -> None:
    if not _should_cache_upstream(upstream):
        return

    ttl_seconds = ttl_policy.ttl_seconds_for(prompt_text)
    if ttl_seconds is None:
        return

    usage = upstream.get("usage") or {}
    choices = upstream.get("choices") or [{}]
    finish_reason = choices[0].get("finish_reason") if choices else None
    cache_service.put(
        namespace,
        prompt_text,
        upstream,
        ttl_seconds=ttl_seconds,
        prompt_tokens=int(usage.get("prompt_tokens") or 0),
        completion_tokens=int(usage.get("completion_tokens") or 0),
        finish_reason=finish_reason,
    )


def create_app(
    *,
    cache: CacheService | None = None,
    router: ProviderRouter | None = None,
    ttl_policy: TTLPolicy | None = None,
) -> FastAPI:
    app = FastAPI(
        title="Semantic Cache Proxy",
        description="Drop-in OpenAI-compatible proxy with semantic response caching.",
        version="0.1.0",
    )
    app.state.cache = cache or CacheService(MemoryCacheStore(), OpenAIEmbedder())
    app.state.router = router or ProviderRouter()
    app.state.ttl_policy = ttl_policy or TTLPolicy.from_env()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/v1/chat/completions", response_model=None)
    async def chat_completions(body: ChatCompletionRequest) -> Response:
        cache_service: CacheService = app.state.cache
        provider_router: ProviderRouter = app.state.router
        ttl_policy: TTLPolicy = app.state.ttl_policy
        messages = body.as_message_dicts()
        namespace = build_namespace(
            messages,
            model=body.model,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
        )
        prompt_text = extract_user_text(messages)
        miss_headers = _cache_miss_headers(prompt_text, ttl_policy=ttl_policy)
        threshold = _threshold()
        cached = cache_service.get(namespace, prompt_text, threshold=threshold)

        if body.stream:
            if cached.status == LookupStatus.HIT and cached.entry is not None:
                return StreamingResponse(
                    stream_cached_entry(cached.entry),
                    media_type="text/event-stream",
                    headers=_cache_hit_headers(cached.similarity or 0.0),
                )
            provider = provider_router.resolve(body.model)
            return StreamingResponse(
                _stream_miss(
                    provider=provider,
                    body=body,
                    cache_service=cache_service,
                    namespace=namespace,
                    prompt_text=prompt_text,
                    ttl_policy=ttl_policy,
                ),
                media_type="text/event-stream",
                headers=miss_headers,
            )

        if cached.status == LookupStatus.HIT and cached.entry is not None:
            return JSONResponse(
                content=cached.entry.response,
                headers=_cache_hit_headers(cached.similarity or 0.0),
            )

        provider = provider_router.resolve(body.model)
        upstream = await provider.chat_completion(body)
        _store_upstream_response(
            cache_service,
            namespace,
            prompt_text,
            upstream,
            ttl_policy=ttl_policy,
        )
        return JSONResponse(content=upstream, headers=miss_headers)

    return app


async def _stream_miss(
    *,
    provider: Any,
    body: ChatCompletionRequest,
    cache_service: CacheService,
    namespace: CacheNamespace,
    prompt_text: str,
    ttl_policy: TTLPolicy,
):
    content = ""
    finish_reason: str | None = None
    usage: dict[str, Any] | None = None

    async for sse_line in provider.chat_completion_stream(body):
        yield sse_line
        data = parse_sse_payload(sse_line)
        if data is None:
            continue
        content, finish_reason, usage = accumulate_stream_chunk(
            data,
            content=content,
            finish_reason=finish_reason,
            usage=usage,
        )

    if finish_reason == "stop" and content:
        upstream = build_completion_dict(
            model=body.model,
            content=content,
            finish_reason=finish_reason,
            usage=usage,
        )
        _store_upstream_response(
            cache_service,
            namespace,
            prompt_text,
            upstream,
            ttl_policy=ttl_policy,
        )


# Use: uvicorn src.proxy.app:create_app --factory --reload --port 8080
