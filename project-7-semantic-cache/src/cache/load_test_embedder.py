"""Deterministic embedder for demo and load-test runs without OpenAI embeddings."""

from __future__ import annotations

import json
import math
from pathlib import Path

from src.cache.embed import EMBEDDING_DIMS

DEFAULT_SEED_PATH = Path(__file__).resolve().parents[2] / "scripts" / "seed_queries.json"


class LoadTestEmbedder:
    """Maps query groups to shared unit vectors so paraphrases cluster for cache hits."""

    def __init__(self, groups: list[list[str]], *, dims: int = EMBEDDING_DIMS) -> None:
        self._dims = dims
        self._vectors: dict[str, list[float]] = {}
        for index, phrases in enumerate(groups):
            vector = self._unit_vector(index, dims)
            for phrase in phrases:
                self._vectors[phrase.lower().strip()] = vector

    @classmethod
    def from_seed_file(cls, path: Path | None = None) -> LoadTestEmbedder:
        seed_path = path or DEFAULT_SEED_PATH
        payload = json.loads(seed_path.read_text(encoding="utf-8"))
        return cls(payload["groups"])

    @staticmethod
    def _unit_vector(index: int, dims: int) -> list[float]:
        vector = [0.0] * dims
        vector[index % dims] = 1.0
        if dims > 1:
            vector[(index + 1) % dims] = 0.05
        magnitude = math.sqrt(sum(value * value for value in vector))
        return [value / magnitude for value in vector]

    def embed(self, text: str) -> list[float]:
        normalized = text.lower().strip()
        if normalized in self._vectors:
            return self._vectors[normalized]
        return self._unit_vector(abs(hash(normalized)) % self._dims, self._dims)
