"""Phase 1.3 — Redis + RedisVL vector cache (requires redis-stack)."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from redis import Redis
from redisvl.index import SearchIndex
from redisvl.query import VectorQuery
from redisvl.query.filter import Tag

from src.cache.embed import EMBEDDING_DIMS
from src.cache.lookup import DEFAULT_THRESHOLD, classify_lookup
from src.models.types import CacheEntry, CacheNamespace, LookupResult, LookupStatus, Provider
from src.policies.invalidation import InvalidateBy, entry_matches

CACHE_INDEX_SCHEMA = {
    "index": {
        "name": "semantic_cache",
        "prefix": "cache",
    },
    "fields": [
        {"name": "entry_id", "type": "tag"},
        {"name": "namespace_key", "type": "tag"},
        {"name": "prompt_text", "type": "text"},
        {
            "name": "embedding",
            "type": "vector",
            "attrs": {
                "dims": EMBEDDING_DIMS,
                "distance_metric": "cosine",
                "algorithm": "flat",
            },
        },
        {"name": "response_json", "type": "text"},
        {"name": "created_at", "type": "numeric"},
        {"name": "expires_at", "type": "numeric"},
        {"name": "hit_count", "type": "numeric"},
        {"name": "prompt_tokens", "type": "numeric"},
        {"name": "completion_tokens", "type": "numeric"},
        {"name": "tokens_saved", "type": "numeric"},
        {"name": "tags_json", "type": "text"},
    ],
}


def _parse_namespace(namespace_key: str) -> CacheNamespace | None:
    parts = namespace_key.split(":", 4)
    if len(parts) != 5:
        return None
    provider_raw, model, system_prompt_hash, temp_raw, tokens_raw = parts
    temperature = None if temp_raw == "none" else float(temp_raw)
    max_tokens = None if tokens_raw == "none" else int(tokens_raw)
    return CacheNamespace(
        provider=Provider(provider_raw),
        model=model,
        system_prompt_hash=system_prompt_hash,
        temperature=temperature,
        max_tokens=max_tokens,
    )


class RedisCacheStore:
    def __init__(self, redis_url: str = "redis://localhost:6379") -> None:
        self.redis = Redis.from_url(redis_url, decode_responses=True)
        self.index = SearchIndex.from_dict(CACHE_INDEX_SCHEMA, redis_url=redis_url)
        self.index.create(overwrite=False)

    def _redis_key(self, entry_id: str) -> str:
        return f"cache:{entry_id}"

    def store(self, entry: CacheEntry) -> str:
        self.index.load(
            [
                {
                    "entry_id": entry.id,
                    "namespace_key": entry.namespace.cache_key(),
                    "prompt_text": entry.prompt_text,
                    "embedding": entry.embedding,
                    "response_json": json.dumps(entry.response),
                    "created_at": int(entry.created_at.timestamp()),
                    "expires_at": int(entry.expires_at.timestamp()),
                    "hit_count": entry.hit_count,
                    "prompt_tokens": entry.prompt_tokens,
                    "completion_tokens": entry.completion_tokens,
                    "tokens_saved": entry.tokens_saved,
                    "tags_json": json.dumps(entry.tags),
                }
            ],
            id=entry.id,
        )
        return entry.id

    def _query_top(
        self,
        namespace: CacheNamespace,
        query_embedding: list[float],
    ) -> dict | None:
        namespace_filter = Tag("namespace_key") == namespace.cache_key()
        query = VectorQuery(
            vector=query_embedding,
            vector_field_name="embedding",
            filter_expression=namespace_filter,
            num_results=1,
            return_fields=[
                "entry_id",
                "namespace_key",
                "prompt_text",
                "response_json",
                "created_at",
                "expires_at",
                "hit_count",
                "prompt_tokens",
                "completion_tokens",
                "tokens_saved",
                "tags_json",
            ],
        )
        results = self.index.query(query)
        return results[0] if results else None

    def _entry_from_record(
        self,
        record: dict,
        *,
        namespace: CacheNamespace | None = None,
        query_embedding: list[float] | None = None,
    ) -> CacheEntry | None:
        resolved = namespace or _parse_namespace(record.get("namespace_key") or "")
        if resolved is None or not record.get("entry_id"):
            return None
        created_at = datetime.fromtimestamp(float(record["created_at"]), tz=timezone.utc)
        expires_at = datetime.fromtimestamp(float(record["expires_at"]), tz=timezone.utc)
        tags_raw = record.get("tags_json") or "[]"
        return CacheEntry(
            id=record["entry_id"],
            namespace=resolved,
            prompt_text=record.get("prompt_text", ""),
            embedding=query_embedding or [],
            response=json.loads(record.get("response_json") or "{}"),
            created_at=created_at,
            expires_at=expires_at,
            hit_count=int(float(record.get("hit_count") or 0)),
            prompt_tokens=int(float(record.get("prompt_tokens") or 0)),
            completion_tokens=int(float(record.get("completion_tokens") or 0)),
            tokens_saved=int(float(record.get("tokens_saved") or 0)),
            tags=json.loads(tags_raw),
        )

    def find_best_match(
        self,
        namespace: CacheNamespace,
        query_embedding: list[float],
        *,
        now: datetime | None = None,
    ) -> tuple[float | None, CacheEntry | None]:
        now = now or datetime.now(timezone.utc)
        top = self._query_top(namespace, query_embedding)
        if not top:
            return None, None

        similarity = 1.0 - float(top.get("vector_distance", 1.0))
        entry = self._entry_from_record(top, namespace=namespace, query_embedding=query_embedding)
        if entry is None or entry.is_expired(now):
            return similarity, None
        return similarity, entry

    def lookup(
        self,
        namespace: CacheNamespace,
        query_embedding: list[float],
        *,
        threshold: float = DEFAULT_THRESHOLD,
        now: datetime | None = None,
    ) -> LookupResult:
        now = now or datetime.now(timezone.utc)
        similarity, entry = self.find_best_match(namespace, query_embedding, now=now)
        result = classify_lookup(
            similarity,
            threshold=threshold,
            entry_id=entry.id if entry else None,
        )
        matched_prompt = entry.prompt_text if entry else None
        if result.status != LookupStatus.HIT or entry is None:
            return LookupResult(
                status=result.status,
                similarity=result.similarity,
                entry_id=None,
                entry=None,
                threshold=result.threshold,
                matched_prompt_text=matched_prompt,
            )

        entry.hit_count += 1
        entry.tokens_saved += entry.prompt_tokens + entry.completion_tokens
        self.redis.hset(
            self._redis_key(entry.id),
            mapping={"hit_count": entry.hit_count, "tokens_saved": entry.tokens_saved},
        )
        return LookupResult(
            status=LookupStatus.HIT,
            similarity=similarity,
            entry_id=entry.id,
            entry=entry,
            threshold=threshold,
            matched_prompt_text=matched_prompt,
        )

    def invalidate(self, by: InvalidateBy, value: str) -> int:
        deleted = 0
        for key in self.redis.scan_iter("cache:*"):
            record = self.redis.hgetall(key)
            if not record:
                continue
            entry = self._entry_from_record(record)
            if entry is None:
                continue
            if entry_matches(entry, by, value):
                self.redis.delete(key)
                deleted += 1
        return deleted

    def count_active(self, now: datetime | None = None) -> int:
        now = now or datetime.now(timezone.utc)
        active = 0
        for key in self.redis.scan_iter("cache:*"):
            record = self.redis.hgetall(key)
            if not record or "expires_at" not in record:
                continue
            expires_at = datetime.fromtimestamp(float(record["expires_at"]), tz=timezone.utc)
            if now < expires_at:
                active += 1
        return active

    def purge_expired(self, now: datetime | None = None) -> int:
        now = now or datetime.now(timezone.utc)
        deleted = 0
        for key in self.redis.scan_iter("cache:*"):
            record = self.redis.hgetall(key)
            if not record or "expires_at" not in record:
                continue
            expires_at = datetime.fromtimestamp(float(record["expires_at"]), tz=timezone.utc)
            if now >= expires_at:
                self.redis.delete(key)
                deleted += 1
        return deleted
