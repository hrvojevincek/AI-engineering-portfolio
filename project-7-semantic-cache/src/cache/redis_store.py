"""Phase 1.3 — Redis + RedisVL vector cache (requires redis-stack)."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from redis import Redis
from redisvl.index import SearchIndex
from redisvl.query import VectorQuery
from redisvl.query.filter import Tag

from src.cache.embed import EMBEDDING_DIMS
from src.cache.lookup import DEFAULT_THRESHOLD, NEAR_MISS_GAP
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
        {"name": "tags_json", "type": "text"},
    ],
}


class RedisCacheStore:
    def __init__(self, redis_url: str = "redis://localhost:6379") -> None:
        self.redis = Redis.from_url(redis_url, decode_responses=True)
        self.index = SearchIndex.from_dict(CACHE_INDEX_SCHEMA, redis_url=redis_url)
        self.index.create(overwrite=False)

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
                    "tags_json": json.dumps(entry.tags),
                }
            ],
            id=f"cache:{entry.id}",
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
                "tags_json",
            ],
        )
        results = self.index.query(query)
        return results[0] if results else None

    @staticmethod
    def _entry_from_record(
        namespace: CacheNamespace,
        record: dict,
        *,
        query_embedding: list[float],
        similarity: float,
    ) -> CacheEntry:
        created_at = datetime.fromtimestamp(float(record["created_at"]), tz=timezone.utc)
        expires_at = datetime.fromtimestamp(float(record["expires_at"]), tz=timezone.utc)
        tags_raw = record.get("tags_json") or "[]"
        return CacheEntry(
            id=record["entry_id"],
            namespace=namespace,
            prompt_text=record["prompt_text"],
            embedding=query_embedding,
            response=json.loads(record["response_json"]),
            created_at=created_at,
            expires_at=expires_at,
            hit_count=int(float(record["hit_count"])),
            prompt_tokens=int(float(record["prompt_tokens"])),
            completion_tokens=int(float(record["completion_tokens"])),
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
        expires_at = datetime.fromtimestamp(float(top["expires_at"]), tz=timezone.utc)
        if now >= expires_at:
            return similarity, None

        entry = self._entry_from_record(
            namespace,
            top,
            query_embedding=query_embedding,
            similarity=similarity,
        )
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
        top = self._query_top(namespace, query_embedding)
        if not top:
            return LookupResult(status=LookupStatus.MISS, threshold=threshold)

        similarity = 1.0 - float(top.get("vector_distance", 1.0))
        expires_at = datetime.fromtimestamp(float(top["expires_at"]), tz=timezone.utc)
        if now >= expires_at:
            return LookupResult(
                status=LookupStatus.MISS,
                similarity=similarity,
                threshold=threshold,
            )

        if similarity < threshold:
            near_miss = similarity >= threshold - NEAR_MISS_GAP
            return LookupResult(
                status=LookupStatus.NEAR_MISS if near_miss else LookupStatus.MISS,
                similarity=similarity,
                threshold=threshold,
            )

        entry_id = top["entry_id"]
        hit_count = int(float(top["hit_count"])) + 1
        self.redis.hset(f"cache:{entry_id}", "hit_count", hit_count)

        entry = self._entry_from_record(
            namespace,
            top,
            query_embedding=query_embedding,
            similarity=similarity,
        )
        entry.hit_count = hit_count

        return LookupResult(
            status=LookupStatus.HIT,
            similarity=similarity,
            entry_id=entry_id,
            entry=entry,
            threshold=threshold,
        )

    def invalidate(self, by: InvalidateBy, value: str) -> int:
        deleted = 0
        for key in self.redis.scan_iter("cache:*"):
            record = self.redis.hgetall(key)
            if not record:
                continue
            entry = self._entry_from_scan(record)
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
            if not record:
                continue
            expires_at = datetime.fromtimestamp(float(record["expires_at"]), tz=timezone.utc)
            if now < expires_at:
                active += 1
        return active

    @staticmethod
    def _entry_from_scan(record: dict[str, str]) -> CacheEntry | None:
        namespace_key = record.get("namespace_key")
        if not namespace_key:
            return None
        parts = namespace_key.split(":", 4)
        if len(parts) != 5:
            return None
        provider_raw, model, system_prompt_hash, temp_raw, tokens_raw = parts
        temperature = None if temp_raw == "none" else float(temp_raw)
        max_tokens = None if tokens_raw == "none" else int(tokens_raw)
        namespace = CacheNamespace(
            provider=Provider(provider_raw),
            model=model,
            system_prompt_hash=system_prompt_hash,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        created_at = datetime.fromtimestamp(float(record["created_at"]), tz=timezone.utc)
        expires_at = datetime.fromtimestamp(float(record["expires_at"]), tz=timezone.utc)
        tags_raw = record.get("tags_json") or "[]"
        return CacheEntry(
            id=record["entry_id"],
            namespace=namespace,
            prompt_text=record.get("prompt_text", ""),
            embedding=[],
            response=json.loads(record.get("response_json") or "{}"),
            created_at=created_at,
            expires_at=expires_at,
            hit_count=int(float(record.get("hit_count") or 0)),
            prompt_tokens=int(float(record.get("prompt_tokens") or 0)),
            completion_tokens=int(float(record.get("completion_tokens") or 0)),
            tags=json.loads(tags_raw),
        )
