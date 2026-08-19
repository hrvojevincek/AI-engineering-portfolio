"""Phase 1.3 — cache entry storage and semantic lookup."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from typing import Protocol

from src.cache.embed import Embedder
from src.cache.lookup import DEFAULT_THRESHOLD, VectorCandidate, find_best_match, lookup
from src.models.types import CacheEntry, CacheNamespace, LookupResult, LookupStatus
from src.policies.invalidation import InvalidateBy, entry_matches


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
    tags: list[str] | None = None,
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
        tags=tags or [],
    )


class CacheStore(Protocol):
    def store(self, entry: CacheEntry) -> str: ...

    def find_best_match(
        self,
        namespace: CacheNamespace,
        query_embedding: list[float],
        *,
        now: datetime | None = None,
    ) -> tuple[float | None, CacheEntry | None]: ...

    def lookup(
        self,
        namespace: CacheNamespace,
        query_embedding: list[float],
        *,
        threshold: float = DEFAULT_THRESHOLD,
        now: datetime | None = None,
    ) -> LookupResult: ...

    def invalidate(self, by: InvalidateBy, value: str) -> int: ...

    def count_active(self, now: datetime | None = None) -> int: ...


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

    def find_best_match(
        self,
        namespace: CacheNamespace,
        query_embedding: list[float],
        *,
        now: datetime | None = None,
    ) -> tuple[float | None, CacheEntry | None]:
        now = now or datetime.now(timezone.utc)
        candidates = self._active_candidates(namespace, now)
        best, score = find_best_match(query_embedding, candidates)
        if best is None:
            return None, None
        return score, self._entries[best.entry_id]

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

    def invalidate(self, by: InvalidateBy, value: str) -> int:
        to_delete = [
            entry_id
            for entry_id, entry in self._entries.items()
            if entry_matches(entry, by, value)
        ]
        for entry_id in to_delete:
            del self._entries[entry_id]
        return len(to_delete)

    def count_active(self, now: datetime | None = None) -> int:
        now = now or datetime.now(timezone.utc)
        return sum(1 for entry in self._entries.values() if not entry.is_expired(now))


class CacheService:
    """High-level get/put using an embedder + store."""

    def __init__(self, store: CacheStore, embedder: Embedder) -> None:
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
        tags: list[str] | None = None,
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
            tags=tags,
        )
        return self.store.store(entry)

    def peek(
        self,
        namespace: CacheNamespace,
        prompt_text: str,
    ) -> tuple[float | None, str | None]:
        embedding = self.embedder.embed(prompt_text)
        similarity, entry = self.store.find_best_match(namespace, embedding)
        matched_prompt = entry.prompt_text if entry else None
        return similarity, matched_prompt

    def get(
        self,
        namespace: CacheNamespace,
        prompt_text: str,
        *,
        threshold: float = DEFAULT_THRESHOLD,
    ) -> LookupResult:
        embedding = self.embedder.embed(prompt_text)
        return self.store.lookup(namespace, embedding, threshold=threshold)

    def invalidate(self, by: InvalidateBy, value: str) -> int:
        return self.store.invalidate(by, value)

    def active_entry_count(self) -> int:
        return self.store.count_active()
