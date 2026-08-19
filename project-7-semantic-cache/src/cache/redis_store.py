"""Phase 1.3 — Redis + RedisVL vector cache (requires redis-stack)."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from redis import Redis
from redisvl.index import SearchIndex
from redisvl.query import VectorQuery
from redisvl.query.filter import Tag

from src.cache.embed import EMBEDDING_DIMS
from src.cache.lookup import DEFAULT_THRESHOLD
from src.cache.store import build_entry
from src.models.types import CacheEntry, CacheNamespace, LookupResult, LookupStatus

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
                }
            ],
            id=f"cache:{entry.id}",
        )
        return entry.id

    def lookup(
        self,
        namespace: CacheNamespace,
        query_embedding: list[float],
        *,
        threshold: float = DEFAULT_THRESHOLD,
        now: datetime | None = None,
    ) -> LookupResult:
        now = now or datetime.now(timezone.utc)
        namespace_filter = Tag("namespace_key") == namespace.cache_key()

        query = VectorQuery(
            vector=query_embedding,
            vector_field_name="embedding",
            filter_expression=namespace_filter,
            num_results=1,
            return_fields=[
                "entry_id",
                "prompt_text",
                "response_json",
                "expires_at",
                "hit_count",
                "prompt_tokens",
                "completion_tokens",
            ],
        )
        results = self.index.query(query)
        if not results:
            return LookupResult(status=LookupStatus.MISS, threshold=threshold)

        top = results[0]
        distance = float(top.get("vector_distance", 1.0))
        similarity = 1.0 - distance

        if similarity < threshold:
            near_miss = similarity >= threshold - 0.03
            return LookupResult(
                status=LookupStatus.NEAR_MISS if near_miss else LookupStatus.MISS,
                similarity=similarity,
                threshold=threshold,
            )

        expires_at = datetime.fromtimestamp(float(top["expires_at"]), tz=timezone.utc)
        if now >= expires_at:
            return LookupResult(
                status=LookupStatus.MISS,
                similarity=similarity,
                threshold=threshold,
            )

        entry_id = top["entry_id"]
        hit_count = int(float(top["hit_count"])) + 1
        self.redis.hset(f"cache:{entry_id}", "hit_count", hit_count)

        entry = CacheEntry(
            id=entry_id,
            namespace=namespace,
            prompt_text=top["prompt_text"],
            embedding=query_embedding,
            response=json.loads(top["response_json"]),
            created_at=now,
            expires_at=expires_at,
            hit_count=hit_count,
            prompt_tokens=int(float(top["prompt_tokens"])),
            completion_tokens=int(float(top["completion_tokens"])),
        )

        return LookupResult(
            status=LookupStatus.HIT,
            similarity=similarity,
            entry_id=entry_id,
            entry=entry,
            threshold=threshold,
        )
