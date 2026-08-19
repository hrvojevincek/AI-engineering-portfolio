"""Phase 3.1 TTL tier tests — run: pytest tests/test_ttl.py -v"""

import pytest
from src.policies.ttl import TTLPolicy, TTLTier, classify_prompt


@pytest.mark.parametrize(
    ("prompt", "expected"),
    [
        ("What is Python?", TTLTier.STABLE),
        ("Explain recursion to me", TTLTier.STABLE),
        ("Define semantic caching", TTLTier.STABLE),
        ("What's the weather today?", TTLTier.TIME_SENSITIVE),
        ("Latest news about AI", TTLTier.TIME_SENSITIVE),
        ("Give me live stock prices in real time", TTLTier.NO_CACHE),
        ("Write a haiku about autumn", TTLTier.DEFAULT),
    ],
)
def test_classify_prompt(prompt: str, expected: TTLTier) -> None:
    assert classify_prompt(prompt) == expected


def test_ttl_policy_seconds_by_tier() -> None:
    policy = TTLPolicy(
        stable_seconds=86_400,
        default_seconds=43_200,
        time_sensitive_seconds=3_600,
    )

    assert policy.ttl_seconds_for("What is Python?") == 86_400
    assert policy.ttl_seconds_for("What's the weather today?") == 3_600
    assert policy.ttl_seconds_for("Write a poem") == 43_200
    assert policy.ttl_seconds_for("Give me live stock prices in real time") is None


def test_no_cache_prompt_skips_storage_in_proxy():
    from fastapi.testclient import TestClient
    from src.cache.embed import MockEmbedder
    from src.cache.store import CacheService, MemoryCacheStore
    from src.providers.base import FakeChatProvider
    from src.providers.router import ProviderRouter
    from src.proxy.app import create_app

    fake = FakeChatProvider()
    cache = CacheService(MemoryCacheStore(), MockEmbedder())
    app = create_app(cache=cache, router=ProviderRouter(openai=fake))
    client = TestClient(app)

    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "Give me live stock prices in real time"}],
    }

    first = client.post("/v1/chat/completions", json=payload)
    second = client.post("/v1/chat/completions", json=payload)

    assert first.status_code == 200
    assert first.headers["x-cache"] == "MISS"
    assert first.headers["x-cache-ttl-tier"] == "no_cache"
    assert second.status_code == 200
    assert second.headers["x-cache"] == "MISS"
    assert fake.call_count == 2
