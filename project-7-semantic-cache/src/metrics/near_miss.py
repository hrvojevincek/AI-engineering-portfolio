"""Phase 4.3 — near-miss event log and export."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from datetime import datetime, timezone

FILLER_WORDS = {
    "a",
    "an",
    "the",
    "please",
    "could",
    "would",
    "you",
    "tell",
    "me",
    "about",
    "just",
    "kind",
    "of",
    "to",
    "for",
    "can",
}


def suggest_normalization(query_text: str) -> str:
    """Strip filler words so near-misses can be compared as tighter embeddings."""
    tokens = [token.strip("?.!,;:").lower() for token in query_text.split()]
    kept = [token for token in tokens if token and token not in FILLER_WORDS]
    return " ".join(kept) or query_text.lower().strip()


@dataclass(frozen=True)
class NearMiss:
    query_text: str
    model: str
    best_similarity: float
    threshold: float
    matched_prompt_text: str | None
    timestamp: datetime

    @property
    def gap(self) -> float:
        return round(self.threshold - self.best_similarity, 4)

    @property
    def normalization_suggestion(self) -> str:
        return suggest_normalization(self.query_text)


@dataclass
class NearMissLog:
    max_entries: int = 500
    _entries: list[NearMiss] = field(default_factory=list)

    def append(
        self,
        *,
        query_text: str,
        model: str,
        best_similarity: float,
        threshold: float,
        matched_prompt_text: str | None,
        timestamp: datetime | None = None,
    ) -> None:
        entry = NearMiss(
            query_text=query_text,
            model=model,
            best_similarity=best_similarity,
            threshold=threshold,
            matched_prompt_text=matched_prompt_text,
            timestamp=timestamp or datetime.now(timezone.utc),
        )
        self._entries.append(entry)
        if len(self._entries) > self.max_entries:
            self._entries = self._entries[-self.max_entries :]

    def entries(self) -> list[NearMiss]:
        return list(self._entries)

    def to_dicts(self) -> list[dict[str, object]]:
        return [
            {
                "query_text": item.query_text,
                "model": item.model,
                "best_similarity": item.best_similarity,
                "threshold": item.threshold,
                "gap": item.gap,
                "matched_prompt_text": item.matched_prompt_text,
                "normalization_suggestion": item.normalization_suggestion,
                "timestamp": item.timestamp.isoformat(),
            }
            for item in self._entries
        ]

    def to_csv(self) -> str:
        buffer = io.StringIO()
        writer = csv.DictWriter(
            buffer,
            fieldnames=[
                "timestamp",
                "model",
                "query_text",
                "best_similarity",
                "threshold",
                "gap",
                "matched_prompt_text",
                "normalization_suggestion",
            ],
        )
        writer.writeheader()
        for item in self._entries:
            writer.writerow(
                {
                    "timestamp": item.timestamp.isoformat(),
                    "model": item.model,
                    "query_text": item.query_text,
                    "best_similarity": item.best_similarity,
                    "threshold": item.threshold,
                    "gap": item.gap,
                    "matched_prompt_text": item.matched_prompt_text or "",
                    "normalization_suggestion": item.normalization_suggestion,
                }
            )
        return buffer.getvalue()
