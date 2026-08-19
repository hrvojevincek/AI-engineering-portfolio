"""Phase 3.2 invalidation tests — run: pytest tests/test_invalidation.py -v"""

from fastapi.testclient import TestClient

from src.cache.embed import MockEmbedder
from src.cache.namespace import build_namespace, hash_system_prompt
from src.cache.store import CacheService, MemoryCacheStore
from src.models.types import LookupStatus
from src.policies.invalidation import InvalidateBy
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


def make_client() -> tuple[TestClient, CacheService]:
    cache = CacheService(MemoryCacheStore(), MockEmbedder())
    app = create_app(cache=cache, router=ProviderRouter(openai=FakeChatProvider()))
    return TestClient(app), cache


def test_invalidate_by_model():
    client, cache = make_client()
    client.post("/v1/chat/completions", json=PAYLOAD)

    response = client.post(
        "/v1/cache/invalidate",
        json={"by": "model", "value": "gpt-4o-mini"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["deleted"] == 1
    assert cache.get(build_namespace(MESSAGES, model="gpt-4o-mini"), "What is Python?").status == LookupStatus.MISS


def test_invalidate_by_system_prompt_hash():
    client, cache = make_client()
    client.post("/v1/chat/completions", json=PAYLOAD)
    system_hash = hash_system_prompt("You are a helpful assistant.")

    response = client.post(
        "/v1/cache/invalidate",
        json={"by": "system_prompt_hash", "value": system_hash},
    )

    assert response.json()["deleted"] == 1
    assert cache.get(build_namespace(MESSAGES, model="gpt-4o-mini"), "What is Python?").status == LookupStatus.MISS


def test_invalidate_by_prefix():
    client, cache = make_client()
    client.post("/v1/chat/completions", json=PAYLOAD)

    response = client.post(
        "/v1/cache/invalidate",
        json={"by": "prefix", "value": "What is"},
    )

    assert response.json()["deleted"] == 1
    assert cache.get(build_namespace(MESSAGES, model="gpt-4o-mini"), "What is Python?").status == LookupStatus.MISS


def test_invalidate_by_tag():
    client, _ = make_client()
    client.post(
        "/v1/chat/completions",
        json=PAYLOAD,
        headers={"X-Cache-Tags": "docs,python"},
    )
    client.post(
        "/v1/chat/completions",
        json={
            **PAYLOAD,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is Java?"},
            ],
        },
        headers={"X-Cache-Tags": "docs,java"},
    )

    response = client.post(
        "/v1/cache/invalidate",
        json={"by": "tag", "value": "python"},
    )

    assert response.json()["deleted"] == 1

    python = client.post("/v1/chat/completions", json=PAYLOAD)
    java = client.post(
        "/v1/chat/completions",
        json={
            **PAYLOAD,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is Java?"},
            ],
        },
    )

    assert python.headers["x-cache"] == "MISS"
    assert java.headers["x-cache"] == "HIT"


def test_model_upgrade_scenario():
    """After invalidating old model, cached answers for that model are gone."""
    client, cache = make_client()
    client.post("/v1/chat/completions", json=PAYLOAD)

    deleted = client.post(
        "/v1/cache/invalidate",
        json={"by": "model", "value": "gpt-4o-mini"},
    ).json()["deleted"]
    assert deleted == 1

    upgraded_payload = {**PAYLOAD, "model": "gpt-4o-mini-2024-07-18"}
    result = client.post("/v1/chat/completions", json=upgraded_payload)
    assert result.headers["x-cache"] == "MISS"
    assert len(cache.store._entries) == 1
