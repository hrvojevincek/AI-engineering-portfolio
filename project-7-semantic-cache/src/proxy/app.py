"""FastAPI proxy — OpenAI-compatible chat completions with semantic cache."""

from __future__ import annotations

from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse, Response, StreamingResponse

from src.cache.embed import OpenAIEmbedder
from src.cache.lookup import DEFAULT_THRESHOLD
from src.cache.namespace import build_namespace, extract_user_text
from src.cache.store import CacheService, MemoryCacheStore
from src.models.types import CacheNamespace, LookupResult, LookupStatus
from src.policies.adaptive_threshold import AdaptiveThresholdPolicy
from src.policies.query_log import QueryLog, QueryRecord
from src.policies.threshold_tuner import simulate_thresholds
from src.policies.ttl import TTLPolicy
from src.providers.router import ProviderRouter
from src.proxy.schemas import (
    ChatCompletionRequest,
    InvalidateRequest,
    InvalidateResponse,
    ThresholdResult,
    ThresholdTunerRequest,
    ThresholdTunerResponse,
    TunerQuery,
)
from src.proxy.streaming import (
    accumulate_stream_chunk,
    build_completion_dict,
    parse_sse_payload,
    stream_cached_entry,
)

load_dotenv()


def _cache_hit_headers(
    similarity: float,
    *,
    threshold_policy: AdaptiveThresholdPolicy,
    prompt_text: str,
) -> dict[str, str]:
    return {
        "X-Cache": "HIT",
        "X-Cache-Similarity": f"{similarity:.4f}",
        "X-Cache-Request-Type": threshold_policy.request_type_for(prompt_text).value,
        "X-Cache-Threshold": f"{threshold_policy.threshold_for(prompt_text):.4f}",
    }


def _cache_miss_headers(
    prompt_text: str,
    *,
    ttl_policy: TTLPolicy,
    threshold_policy: AdaptiveThresholdPolicy,
) -> dict[str, str]:
    tier = ttl_policy.tier_for(prompt_text)
    threshold = threshold_policy.threshold_for(prompt_text)
    headers = {
        "X-Cache": "MISS",
        "X-Cache-TTL-Tier": tier.value,
        "X-Cache-Request-Type": threshold_policy.request_type_for(prompt_text).value,
    }
    if threshold is not None:
        headers["X-Cache-Threshold"] = f"{threshold:.4f}"
    else:
        headers["X-Cache-Threshold"] = "disabled"
    return headers


def _should_cache_upstream(upstream: dict[str, Any]) -> bool:
    choices = upstream.get("choices") or []
    if not choices:
        return False
    choice = choices[0]
    if choice.get("finish_reason") != "stop":
        return False
    message = choice.get("message") or {}
    return bool(message.get("content"))


def _parse_cache_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [tag.strip() for tag in raw.split(",") if tag.strip()]


def _log_query(
    query_log: QueryLog,
    cache_service: CacheService,
    namespace: CacheNamespace,
    prompt_text: str,
) -> None:
    similarity, matched_prompt = cache_service.peek(namespace, prompt_text)
    query_log.append(
        namespace,
        prompt_text,
        best_similarity=similarity,
        matched_prompt_text=matched_prompt,
    )


def _records_for_tuner(
    cache_service: CacheService,
    query_log: QueryLog,
    queries: list[TunerQuery] | None,
) -> list[QueryRecord]:
    if queries:
        records: list[QueryRecord] = []
        for item in queries:
            messages: list[dict[str, str]] = []
            if item.system_prompt:
                messages.append({"role": "system", "content": item.system_prompt})
            messages.append({"role": "user", "content": item.prompt_text})
            namespace = build_namespace(
                messages,
                model=item.model,
                temperature=item.temperature,
                max_tokens=item.max_tokens,
            )
            similarity, matched_prompt = cache_service.peek(namespace, item.prompt_text)
            records.append(
                QueryRecord(
                    namespace_key=namespace.cache_key(),
                    prompt_text=item.prompt_text,
                    best_similarity=similarity,
                    matched_prompt_text=matched_prompt,
                )
            )
        return records
    return query_log.records()


def _store_upstream_response(
    cache_service: CacheService,
    namespace: CacheNamespace,
    prompt_text: str,
    upstream: dict[str, Any],
    *,
    ttl_policy: TTLPolicy,
    cache_tags: list[str] | None = None,
    threshold_policy: AdaptiveThresholdPolicy,
) -> None:
    if not threshold_policy.caching_enabled_for(prompt_text):
        return
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
        tags=cache_tags,
    )


def create_app(
    *,
    cache: CacheService | None = None,
    router: ProviderRouter | None = None,
    ttl_policy: TTLPolicy | None = None,
    query_log: QueryLog | None = None,
    threshold_policy: AdaptiveThresholdPolicy | None = None,
) -> FastAPI:
    app = FastAPI(
        title="Semantic Cache Proxy",
        description="Drop-in OpenAI-compatible proxy with semantic response caching.",
        version="0.1.0",
    )
    app.state.cache = cache or CacheService(MemoryCacheStore(), OpenAIEmbedder())
    app.state.router = router or ProviderRouter()
    app.state.ttl_policy = ttl_policy or TTLPolicy.from_env()
    app.state.query_log = query_log or QueryLog()
    app.state.threshold_policy = threshold_policy or AdaptiveThresholdPolicy.from_env()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/v1/cache/invalidate")
    def invalidate_cache(body: InvalidateRequest) -> InvalidateResponse:
        cache_service: CacheService = app.state.cache
        deleted = cache_service.invalidate(body.by, body.value)
        return InvalidateResponse(deleted=deleted, by=body.by, value=body.value)

    @app.post("/v1/cache/threshold-tuner")
    def threshold_tuner(body: ThresholdTunerRequest) -> ThresholdTunerResponse:
        cache_service: CacheService = app.state.cache
        query_log: QueryLog = app.state.query_log
        records = _records_for_tuner(cache_service, query_log, body.queries)
        simulations = simulate_thresholds(records, body.thresholds)
        return ThresholdTunerResponse(
            query_count=len(records),
            results=[
                ThresholdResult(
                    threshold=item.threshold,
                    hit_rate=item.hit_rate,
                    miss_rate=item.miss_rate,
                    near_miss_rate=item.near_miss_rate,
                    paraphrase_hit_rate=item.paraphrase_hit_rate,
                )
                for item in simulations
            ],
        )

    @app.post("/v1/chat/completions", response_model=None)
    async def chat_completions(
        body: ChatCompletionRequest,
        x_cache_tags: str | None = Header(default=None, alias="X-Cache-Tags"),
    ) -> Response:
        cache_service: CacheService = app.state.cache
        provider_router: ProviderRouter = app.state.router
        ttl_policy: TTLPolicy = app.state.ttl_policy
        query_log: QueryLog = app.state.query_log
        threshold_policy: AdaptiveThresholdPolicy = app.state.threshold_policy
        messages = body.as_message_dicts()
        namespace = build_namespace(
            messages,
            model=body.model,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
        )
        prompt_text = extract_user_text(messages)
        cache_tags = _parse_cache_tags(x_cache_tags)
        miss_headers = _cache_miss_headers(
            prompt_text,
            ttl_policy=ttl_policy,
            threshold_policy=threshold_policy,
        )
        threshold = threshold_policy.threshold_for(prompt_text)
        _log_query(query_log, cache_service, namespace, prompt_text)
        if threshold is None:
            cached = LookupResult(
                status=LookupStatus.MISS,
                similarity=None,
                entry_id=None,
                entry=None,
                threshold=DEFAULT_THRESHOLD,
            )
        else:
            cached = cache_service.get(namespace, prompt_text, threshold=threshold)

        if body.stream:
            if cached.status == LookupStatus.HIT and cached.entry is not None:
                return StreamingResponse(
                    stream_cached_entry(cached.entry),
                    media_type="text/event-stream",
                    headers=_cache_hit_headers(
                        cached.similarity or 0.0,
                        threshold_policy=threshold_policy,
                        prompt_text=prompt_text,
                    ),
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
                    cache_tags=cache_tags,
                    threshold_policy=threshold_policy,
                ),
                media_type="text/event-stream",
                headers=miss_headers,
            )

        if cached.status == LookupStatus.HIT and cached.entry is not None:
            return JSONResponse(
                content=cached.entry.response,
                headers=_cache_hit_headers(
                    cached.similarity or 0.0,
                    threshold_policy=threshold_policy,
                    prompt_text=prompt_text,
                ),
            )

        provider = provider_router.resolve(body.model)
        upstream = await provider.chat_completion(body)
        _store_upstream_response(
            cache_service,
            namespace,
            prompt_text,
            upstream,
            ttl_policy=ttl_policy,
            cache_tags=cache_tags,
            threshold_policy=threshold_policy,
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
    cache_tags: list[str] | None = None,
    threshold_policy: AdaptiveThresholdPolicy,
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
            cache_tags=cache_tags,
            threshold_policy=threshold_policy,
        )


# Use: uvicorn src.proxy.app:create_app --factory --reload --port 8080
