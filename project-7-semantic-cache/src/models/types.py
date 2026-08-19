from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class Provider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


class LookupStatus(str, Enum):
    HIT = "HIT"
    MISS = "MISS"
    NEAR_MISS = "NEAR_MISS"


class CacheNamespace(BaseModel):
    """Scopes vector search — same user text in different namespaces = different cache."""

    system_prompt_hash: str
    model: str
    temperature: float | None = None
    max_tokens: int | None = None
    provider: Provider = Provider.OPENAI

    def cache_key(self) -> str:
        """Stable string for RedisVL filter / index partitioning."""
        temp = "none" if self.temperature is None else str(self.temperature)
        tokens = "none" if self.max_tokens is None else str(self.max_tokens)
        return f"{self.provider.value}:{self.model}:{self.system_prompt_hash}:{temp}:{tokens}"


class LookupResult(BaseModel):
    status: LookupStatus
    similarity: float | None = None
    entry_id: str | None = None
    entry: "CacheEntry | None" = None
    threshold: float


class CacheEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    namespace: CacheNamespace
    prompt_text: str
    embedding: list[float]
    response: dict[str, Any]
    created_at: datetime
    expires_at: datetime
    hit_count: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    finish_reason: str | None = None

    def is_expired(self, now: datetime | None = None) -> bool:
        now = now or datetime.now(timezone.utc)
        return now >= self.expires_at
