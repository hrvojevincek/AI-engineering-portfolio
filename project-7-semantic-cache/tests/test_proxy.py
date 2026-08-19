"""Phase 2 proxy tests — run: pytest tests/test_proxy.py -v"""

from fastapi.testclient import TestClient
from src.cache.embed import MockEmbedder
from src.cache.store import CacheService, MemoryCacheStore
from src.providers.base import FakeChatProvider
from src.providers.router import ProviderRouter
from src.proxy.app import create_app

MESSAGES = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is Python?"},
]

PAYLOAD = {
    "model": "gpt-4o-mini",
    "messages": MESSAGES,
    "temperature": 0.0,
}

STREAM_PAYLOAD = {**PAYLOAD, "stream": True}


def make_client() -> tuple[TestClient, FakeChatProvider]:
    fake = FakeChatProvider()
    cache = CacheService(MemoryCacheStore(), MockEmbedder())
    app = create_app(
        cache=cache,
        router=ProviderRouter(openai=fake),
    )
    return TestClient(app), fake


def test_health():
    client, _ = make_client()
    assert client.get("/health").json() == {"status": "ok"}


def test_miss_then_hit_calls_provider_once():
    client, fake = make_client()

    first = client.post("/v1/chat/completions", json=PAYLOAD)
    second = client.post("/v1/chat/completions", json=PAYLOAD)

    assert first.status_code == 200
    assert first.headers["x-cache"] == "MISS"
    assert second.status_code == 200
    assert second.headers["x-cache"] == "HIT"
    assert "x-cache-similarity" in second.headers
    assert fake.call_count == 1


def test_semantic_paraphrase_hit():
    client, fake = make_client()

    client.post("/v1/chat/completions", json=PAYLOAD)
    paraphrase = {
        **PAYLOAD,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Explain Python to me"},
        ],
    }
    result = client.post("/v1/chat/completions", json=paraphrase)

    assert result.status_code == 200
    assert result.headers["x-cache"] == "HIT"
    assert fake.call_count == 1


def test_stream_miss_then_hit_calls_provider_once():
    client, fake = make_client()

    first = client.post("/v1/chat/completions", json=STREAM_PAYLOAD)
    second = client.post("/v1/chat/completions", json=STREAM_PAYLOAD)

    assert first.status_code == 200
    assert first.headers["x-cache"] == "MISS"
    assert "text/event-stream" in first.headers["content-type"]
    assert "[DONE]" in first.text

    assert second.status_code == 200
    assert second.headers["x-cache"] == "HIT"
    assert "x-cache-similarity" in second.headers
    assert second.json()["choices"][0]["message"]["content"]
    assert fake.call_count == 1


def test_stream_hit_after_non_stream_seed():
    client, fake = make_client()

    client.post("/v1/chat/completions", json=PAYLOAD)
    result = client.post("/v1/chat/completions", json=STREAM_PAYLOAD)

    assert result.status_code == 200
    assert result.headers["x-cache"] == "HIT"
    assert result.json()["choices"][0]["message"]["content"] == "Python is a programming language."
    assert fake.call_count == 1


def test_non_stream_truncated_response_is_not_cached():
    fake = FakeChatProvider(finish_reason="length")
    cache = CacheService(MemoryCacheStore(), MockEmbedder())
    app = create_app(cache=cache, router=ProviderRouter(openai=fake))
    client = TestClient(app)

    first = client.post("/v1/chat/completions", json=PAYLOAD)
    second = client.post("/v1/chat/completions", json=PAYLOAD)

    assert first.status_code == 200
    assert first.headers["x-cache"] == "MISS"
    assert second.status_code == 200
    assert second.headers["x-cache"] == "MISS"
    assert fake.call_count == 2


def test_stream_miss_caches_for_non_stream_repeat():
    client, fake = make_client()

    client.post("/v1/chat/completions", json=STREAM_PAYLOAD)
    result = client.post("/v1/chat/completions", json=PAYLOAD)

    assert result.status_code == 200
    assert result.headers["x-cache"] == "HIT"
    assert fake.call_count == 1


def test_lookup_embeds_once_per_request():
    fake = FakeChatProvider()
    embedder = MockEmbedder()
    cache = CacheService(MemoryCacheStore(), embedder)
    client = TestClient(create_app(cache=cache, router=ProviderRouter(openai=fake)))

    client.post("/v1/chat/completions", json=PAYLOAD)
    after_miss = embedder.call_count
    client.post("/v1/chat/completions", json=PAYLOAD)

    assert after_miss == 2
    assert embedder.call_count == after_miss + 1
