"""Phase 1.3 — embed prompts for semantic cache lookup."""

from __future__ import annotations

import os
from typing import Protocol

from openai import OpenAI

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMS = 1536


class Embedder(Protocol):
    def embed(self, text: str) -> list[float]: ...


class OpenAIEmbedder:
    def __init__(self, client: OpenAI | None = None, model: str = EMBEDDING_MODEL) -> None:
        self.client = client or OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.model = model

    def embed(self, text: str) -> list[float]:
        response = self.client.embeddings.create(model=self.model, input=text)
        return response.data[0].embedding


class MockEmbedder:
    """Deterministic vectors for unit tests — maps known phrases to nearby embeddings."""

    PHRASE_VECTORS: dict[str, list[float]] = {
        "what is python?": [1.0, 0.0, 0.0],
        "explain python to me": [0.99, 0.01, 0.0],
        "tell me about python": [0.93, 0.37, 0.0],
        "what is java?": [0.0, 1.0, 0.0],
    }

    def embed(self, text: str) -> list[float]:
        normalized = text.lower().strip()
        return self.PHRASE_VECTORS.get(normalized, [0.0, 0.0, 1.0])
