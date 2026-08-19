"""Phase 3.4 adaptive threshold tests — run: pytest tests/test_adaptive_threshold.py -v"""

from fastapi.testclient import TestClient

from src.cache.embed import MockEmbedder
from src.cache.store import CacheService, MemoryCacheStore
from src.policies.adaptive_threshold import (
    AdaptiveThresholdPolicy,
    RequestType,
    classify_request_type,
)
from src.providers.base import FakeChatProvider
from src.providers.router import ProviderRouter
from src.proxy.app import create_app

BASE_MESSAGES = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is Python?"},
]


def test_classify_request_types():
    assert classify_request_type("Classify this email as spam or not") == RequestType.CLASSIFICATION
    assert classify_request_type("Write a poem about the ocean") == RequestType.CREATIVE
    assert classify_request_type("What is Python?") == RequestType.DEFAULT


def test_threshold_for_request_type():
    policy = AdaptiveThresholdPolicy(
        classification_threshold=0.90,
        default_threshold=0.95,
        creative_threshold=0.98,
    )

    assert policy.threshold_for("Classify this sentiment") == 0.90
    assert policy.threshold_for("Write a short story") == 0.98
    assert policy.threshold_for("What is Python?") == 0.95


def test_skip_creative_disables_caching():
    policy = AdaptiveThresholdPolicy(skip_creative=True)
    assert policy.threshold_for("Write a poem") is None
    assert policy.caching_enabled_for("Write a poem") is False


def test_classification_headers_and_threshold_on_miss():
    cache = CacheService(MemoryCacheStore(), MockEmbedder())
    policy = AdaptiveThresholdPolicy(
        classification_threshold=0.90,
        default_threshold=0.95,
        creative_threshold=0.98,
    )
    app = create_app(
        cache=cache,
        router=ProviderRouter(openai=FakeChatProvider()),
        threshold_policy=policy,
    )
    client = TestClient(app)

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Classify this review sentiment: great product"},
        ],
        "temperature": 0.0,
    }
    result = client.post("/v1/chat/completions", json=payload)

    assert result.status_code == 200
    assert result.headers["x-cache"] == "MISS"
    assert result.headers["x-cache-request-type"] == "classification"
    assert result.headers["x-cache-threshold"] == "0.9000"


def test_creative_skip_never_caches():
    cache = CacheService(MemoryCacheStore(), MockEmbedder())
    policy = AdaptiveThresholdPolicy(skip_creative=True)
    app = create_app(
        cache=cache,
        router=ProviderRouter(openai=FakeChatProvider()),
        threshold_policy=policy,
    )
    client = TestClient(app)
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Write a poem about Python"},
        ],
        "temperature": 0.0,
    }

    first = client.post("/v1/chat/completions", json=payload)
    second = client.post("/v1/chat/completions", json=payload)

    assert first.headers["x-cache"] == "MISS"
    assert first.headers["x-cache-request-type"] == "creative"
    assert second.headers["x-cache"] == "MISS"
