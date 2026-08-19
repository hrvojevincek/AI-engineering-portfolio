"""Phase 1.3 tests — run: pytest tests/test_store.py -v"""

from datetime import datetime, timedelta, timezone

import pytest

from src.cache.embed import MockEmbedder
from src.cache.namespace import build_namespace
from src.cache.store import CacheService, MemoryCacheStore, build_entry
from src.models.types import LookupStatus

MESSAGES = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is Python?"},
]

OTHER_MESSAGES = [
    {"role": "system", "content": "You are a terse assistant."},
    {"role": "user", "content": "What is Python?"},
]


@pytest.fixture
def service() -> CacheService:
    return CacheService(MemoryCacheStore(), MockEmbedder())


@pytest.fixture
def namespace():
    return build_namespace(MESSAGES, model="gpt-4o-mini", temperature=0.0)


def test_store_and_semantic_paraphrase_hit(service, namespace):
    service.put(
        namespace,
        "What is Python?",
        {"choices": [{"message": {"content": "Python is a programming language."}}]},
    )

    result = service.get(namespace, "Explain Python to me")
    assert result.status == LookupStatus.HIT
    assert result.entry is not None
    assert "programming language" in result.entry.response["choices"][0]["message"]["content"]


def test_miss_on_unrelated_query(service, namespace):
    service.put(
        namespace,
        "What is Python?",
        {"choices": [{"message": {"content": "Python is a programming language."}}]},
    )

    result = service.get(namespace, "What is Java?")
    assert result.status == LookupStatus.MISS


def test_namespace_isolation(service):
    ns_a = build_namespace(MESSAGES, model="gpt-4o-mini", temperature=0.0)
    ns_b = build_namespace(OTHER_MESSAGES, model="gpt-4o-mini", temperature=0.0)

    service.put(ns_a, "What is Python?", {"answer": "python"})
    result = service.get(ns_b, "Explain Python to me")

    assert result.status == LookupStatus.MISS


def test_expired_entry_is_miss(namespace):
    store = MemoryCacheStore()
    now = datetime.now(timezone.utc)
    entry = build_entry(
        namespace,
        "What is Python?",
        [1.0, 0.0, 0.0],
        {"answer": "python"},
        ttl_seconds=3600,
        now=now - timedelta(hours=2),
    )
    entry.expires_at = now - timedelta(seconds=1)
    store.store(entry)

    result = store.lookup(namespace, [1.0, 0.0, 0.0], now=now)
    assert result.status == LookupStatus.MISS


def test_hit_increments_hit_count(service, namespace):
    service.put(namespace, "What is Python?", {"answer": "python"})

    first = service.get(namespace, "What is Python?")
    second = service.get(namespace, "What is Python?")

    assert first.status == LookupStatus.HIT
    assert second.status == LookupStatus.HIT
    assert second.entry is not None
    assert second.entry.hit_count == 2
