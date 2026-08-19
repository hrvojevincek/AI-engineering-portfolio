"""Phase 4 metrics tests — run: pytest tests/test_metrics.py -v"""

from fastapi.testclient import TestClient

from src.cache.embed import MockEmbedder
from src.cache.store import CacheService, MemoryCacheStore
from src.metrics.prometheus import CacheMetrics
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


def make_client() -> TestClient:
    fake = FakeChatProvider()
    cache = CacheService(MemoryCacheStore(), MockEmbedder())
    metrics = CacheMetrics()
    app = create_app(
        cache=cache,
        router=ProviderRouter(openai=fake),
        metrics=metrics,
    )
    return TestClient(app)


def test_metrics_endpoint_exposes_prometheus_format():
    client = make_client()
    client.post("/v1/chat/completions", json=PAYLOAD)
    client.post("/v1/chat/completions", json=PAYLOAD)

    response = client.get("/metrics")
    assert response.status_code == 200
    body = response.text
    assert "cache_requests_total" in body
    assert 'result="hit"' in body
    assert 'result="miss"' in body
    assert "cache_lookup_latency_seconds" in body
    assert "cache_entries_active" in body


def test_hit_increments_tokens_saved():
    client = make_client()
    client.post("/v1/chat/completions", json=PAYLOAD)
    client.post("/v1/chat/completions", json=PAYLOAD)

    metrics = client.get("/metrics").text
    assert "cache_tokens_saved_total" in metrics


def test_near_miss_endpoint_json():
    client = make_client()
    client.post("/v1/chat/completions", json=PAYLOAD)
    near_payload = {
        **PAYLOAD,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Tell me about Python"},
        ],
    }
    client.post("/v1/chat/completions", json=near_payload)

    response = client.get("/v1/cache/near-misses")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["near_misses"][0]["query_text"] == "Tell me about Python"
    assert data["near_misses"][0]["gap"] > 0


def test_near_miss_endpoint_csv():
    client = make_client()
    client.post("/v1/chat/completions", json=PAYLOAD)
    near_payload = {
        **PAYLOAD,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Tell me about Python"},
        ],
    }
    client.post("/v1/chat/completions", json=near_payload)

    response = client.get("/v1/cache/near-misses?format=csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "Tell me about Python" in response.text
    assert "best_similarity" in response.text
