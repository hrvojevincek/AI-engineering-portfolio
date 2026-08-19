"""Phase 3.3 threshold tuner tests — run: pytest tests/test_threshold_tuner.py -v"""

import pytest
from fastapi.testclient import TestClient
from src.cache.embed import MockEmbedder
from src.cache.store import CacheService, MemoryCacheStore
from src.policies.query_log import QueryLog
from src.policies.threshold_tuner import simulate_thresholds
from src.providers.base import FakeChatProvider
from src.providers.router import ProviderRouter
from src.proxy.app import create_app

PAYLOAD = {
    "model": "gpt-4o-mini",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Python?"},
    ],
    "temperature": 0.0,
}


def make_client() -> TestClient:
    cache = CacheService(MemoryCacheStore(), MockEmbedder())
    app = create_app(
        cache=cache,
        router=ProviderRouter(openai=FakeChatProvider()),
        query_log=QueryLog(),
    )
    return TestClient(app)


def test_threshold_tuner_from_logged_queries():
    client = make_client()
    client.post("/v1/chat/completions", json=PAYLOAD)
    client.post(
        "/v1/chat/completions",
        json={
            **PAYLOAD,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Explain Python to me"},
            ],
        },
    )

    response = client.post(
        "/v1/cache/threshold-tuner",
        json={"thresholds": [0.90, 0.95, 0.98]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["query_count"] == 2
    assert len(body["results"]) == 3

    by_threshold = {item["threshold"]: item for item in body["results"]}
    assert by_threshold[0.90]["hit_rate"] >= by_threshold[0.98]["hit_rate"]
    assert by_threshold[0.90]["paraphrase_hit_rate"] >= 0


def test_threshold_tuner_with_explicit_queries():
    client = make_client()
    client.post("/v1/chat/completions", json=PAYLOAD)

    response = client.post(
        "/v1/cache/threshold-tuner",
        json={
            "thresholds": [0.95],
            "queries": [
                {
                    "prompt_text": "Explain Python to me",
                    "model": "gpt-4o-mini",
                    "system_prompt": "You are a helpful assistant.",
                    "temperature": 0.0,
                }
            ],
        },
    )

    body = response.json()
    assert body["query_count"] == 1
    assert body["results"][0]["hit_rate"] == 1.0
    assert body["results"][0]["paraphrase_hit_rate"] == 1.0


def test_simulate_thresholds_unit():
    from src.policies.query_log import QueryRecord

    records = [
        QueryRecord("ns", "What is Python?", 0.99, "What is Python?"),
        QueryRecord("ns", "Explain Python to me", 0.96, "What is Python?"),
        QueryRecord("ns", "What is Java?", 0.2, "What is Python?"),
    ]

    results = simulate_thresholds(records, [0.90, 0.98])
    low, high = results

    assert low.hit_rate == pytest.approx(2 / 3, rel=1e-3)
    assert low.paraphrase_hit_rate == pytest.approx(1 / 3, rel=1e-3)
    assert low.wrong_answer_rate == low.paraphrase_hit_rate
    assert high.hit_rate == pytest.approx(1 / 3, rel=1e-3)
    assert high.paraphrase_hit_rate == 0.0
