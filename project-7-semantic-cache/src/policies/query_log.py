"""In-memory log of cache lookups for threshold tuning."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.models.types import CacheNamespace


@dataclass(frozen=True)
class QueryRecord:
    namespace_key: str
    prompt_text: str
    best_similarity: float | None
    matched_prompt_text: str | None


@dataclass
class QueryLog:
    max_entries: int = 1_000
    _records: list[QueryRecord] = field(default_factory=list)

    def append(
        self,
        namespace: CacheNamespace,
        prompt_text: str,
        *,
        best_similarity: float | None,
        matched_prompt_text: str | None,
    ) -> None:
        record = QueryRecord(
            namespace_key=namespace.cache_key(),
            prompt_text=prompt_text,
            best_similarity=best_similarity,
            matched_prompt_text=matched_prompt_text,
        )
        self._records.append(record)
        if len(self._records) > self.max_entries:
            self._records = self._records[-self.max_entries :]

    def records(self) -> list[QueryRecord]:
        return list(self._records)

    def clear(self) -> None:
        self._records.clear()
