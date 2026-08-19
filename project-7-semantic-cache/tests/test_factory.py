"""Phase 5 factory tests."""

from src.cache.factory import create_cache_service, create_embedder, create_provider_router
from src.cache.load_test_embedder import LoadTestEmbedder
from src.cache.store import MemoryCacheStore
from src.providers.base import FakeChatProvider


def test_demo_mode_uses_fake_provider_and_load_test_embedder(monkeypatch):
    monkeypatch.setenv("CACHE_DEMO_MODE", "true")
    router = create_provider_router()
    embedder = create_embedder()
    assert isinstance(router.resolve("gpt-4o-mini"), FakeChatProvider)
    assert isinstance(embedder, LoadTestEmbedder)


def test_memory_store_by_default(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setenv("CACHE_STORE", "memory")
    service = create_cache_service(demo_mode=True)
    assert isinstance(service.store, MemoryCacheStore)
