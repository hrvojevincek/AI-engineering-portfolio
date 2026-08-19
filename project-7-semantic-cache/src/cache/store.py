"""Phase 1.3 — cache entry storage and semantic lookup."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.cache.embed import Embedder
from src.cache.lookup import DEFAULT_THRESHOLD, VectorCandidate, lookup
from src.models.types import CacheEntry, CacheNamespace, LookupResult, LookupStatus


def build_entry(
    namespace: CacheNamespace,
    prompt_text: str,
    embedding: list[float],
    response: dict,
    *,
    ttl_seconds: int,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    finish_reason: str | None = None,
    now: datetime | None = None,
) -> CacheEntry:
    now = now or datetime.now(timezone.utc)
    return CacheEntry(
        namespace=namespace,
        prompt_text=prompt_text,
        embedding=embedding,
        response=response,
        created_at=now,
        expires_at=now + timedelta(seconds=ttl_seconds),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        finish_reason=finish_reason,
    )


class MemoryCacheStore:
    """In-memory vector cache for dev/tests. Redis lands in redis_store.py."""

    def __init__(self) -> None:
        self._entries: dict[str, CacheEntry] = {}

    def store(self, entry: CacheEntry) -> str:
        self._entries[entry.id] = entry
        return entry.id

    def get(self, entry_id: str) -> CacheEntry | None:
        return self._entries.get(entry_id)

    def _active_candidates(self, namespace: CacheNamespace, now: datetime) -> list[VectorCandidate]:
        key = namespace.cache_key()
        candidates: list[VectorCandidate] = []
        for entry in self._entries.values():
            if entry.namespace.cache_key() != key:
                continue
            if entry.is_expired(now):
                continue
            candidates.append(VectorCandidate(entry_id=entry.id, embedding=entry.embedding))
        return candidates

    def lookup(
        self,
        namespace: CacheNamespace,
        query_embedding: list[float],
        *,
        threshold: float = DEFAULT_THRESHOLD,
        now: datetime | None = None,
    ) -> LookupResult:
        now = now or datetime.now(timezone.utc)
        result = lookup(
            query_embedding,
            self._active_candidates(namespace, now),
            threshold=threshold,
        )

        if result.status != LookupStatus.HIT or not result.entry_id:
            return LookupResult(
                status=result.status,
                similarity=result.similarity,
                entry_id=result.entry_id,
                entry=None,
                threshold=result.threshold,
            )

        entry = self._entries[result.entry_id]
        entry.hit_count += 1
        return LookupResult(
            status=LookupStatus.HIT,
            similarity=result.similarity,
            entry_id=entry.id,
            entry=entry,
            threshold=result.threshold,
        )


class CacheService:
    """High-level get/put using an embedder + store."""

    def __init__(self, store: MemoryCacheStore, embedder: Embedder) -> None:
        self.store = store
        self.embedder = embedder

    def put(
        self,
        namespace: CacheNamespace,
        prompt_text: str,
        response: dict,
        *,
        ttl_seconds: int = 86400,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        finish_reason: str | None = None,
    ) -> str:
        embedding = self.embedder.embed(prompt_text)
        entry = build_entry(
            namespace,
            prompt_text,
            embedding,
            response,
            ttl_seconds=ttl_seconds,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            finish_reason=finish_reason,
        )
        return self.store.store(entry)

    def get(
        self,
        namespace: CacheNamespace,
        prompt_text: str,
        *,
        threshold: float = DEFAULT_THRESHOLD,
    ) -> LookupResult:
        embedding = self.embedder.embed(prompt_text)
        return self.store.lookup(namespace, embedding, threshold=threshold)
