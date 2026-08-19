from enum import Enum

from pydantic import BaseModel


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
    entry_id: str | None = None  # CacheEntry.id once storage lands in 1.3
    threshold: float
