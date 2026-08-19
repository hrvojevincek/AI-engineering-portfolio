"""Phase 5 — wire cache store and providers from environment."""

from __future__ import annotations

import os

from src.cache.embed import Embedder, MockEmbedder, OpenAIEmbedder
from src.cache.load_test_embedder import LoadTestEmbedder
from src.cache.redis_store import RedisCacheStore
from src.cache.store import CacheService, MemoryCacheStore
from src.providers.base import FakeChatProvider
from src.providers.router import ProviderRouter


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def create_cache_store() -> MemoryCacheStore | RedisCacheStore:
    store_type = os.getenv("CACHE_STORE", "").strip().lower()
    redis_url = os.getenv("REDIS_URL", "").strip()

    if store_type == "redis" or (store_type != "memory" and redis_url):
        return RedisCacheStore(redis_url or "redis://localhost:6379")
    return MemoryCacheStore()


def create_embedder(*, demo_mode: bool | None = None) -> Embedder:
    demo = _env_bool("CACHE_DEMO_MODE") if demo_mode is None else demo_mode
    if demo:
        return LoadTestEmbedder.from_seed_file()
    if _env_bool("CACHE_USE_MOCK_EMBEDDER"):
        return MockEmbedder()
    return OpenAIEmbedder()


def create_provider_router(*, demo_mode: bool | None = None) -> ProviderRouter:
    demo = _env_bool("CACHE_DEMO_MODE") if demo_mode is None else demo_mode
    if demo:
        return ProviderRouter(openai=FakeChatProvider())
    return ProviderRouter()


def create_cache_service(*, demo_mode: bool | None = None) -> CacheService:
    return CacheService(create_cache_store(), create_embedder(demo_mode=demo_mode))
