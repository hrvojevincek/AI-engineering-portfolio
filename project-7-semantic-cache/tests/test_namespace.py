"""Phase 1.1 tests — run: pytest tests/test_namespace.py -v"""

from src.cache.namespace import build_namespace, extract_user_text, hash_system_prompt
from src.models.types import Provider


MESSAGES_WITH_SYSTEM = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is Python?"},
]

MESSAGES_DIFFERENT_SYSTEM = [
    {"role": "system", "content": "You are a terse assistant."},
    {"role": "user", "content": "What is Python?"},
]


def test_hash_system_prompt_is_stable():
  # TODO: once implemented, same input → same hash
  assert hash_system_prompt("hello") == hash_system_prompt("hello")
  assert hash_system_prompt("hello") != hash_system_prompt("world")


def test_extract_user_text_concatenates_user_messages():
    messages = [
        {"role": "user", "content": "First question"},
        {"role": "assistant", "content": "An answer"},
        {"role": "user", "content": "Follow-up"},
    ]
    # TODO: adjust expected string to match your join strategy
    assert "First question" in extract_user_text(messages)
    assert "Follow-up" in extract_user_text(messages)


def test_different_system_prompt_different_namespace():
    ns_a = build_namespace(MESSAGES_WITH_SYSTEM, model="gpt-4o-mini", temperature=0.0)
    ns_b = build_namespace(MESSAGES_DIFFERENT_SYSTEM, model="gpt-4o-mini", temperature=0.0)
    assert ns_a.system_prompt_hash != ns_b.system_prompt_hash


def test_same_config_same_namespace_key():
    ns_a = build_namespace(MESSAGES_WITH_SYSTEM, model="gpt-4o-mini", temperature=0.0)
    ns_b = build_namespace(MESSAGES_WITH_SYSTEM, model="gpt-4o-mini", temperature=0.0)
    assert ns_a.cache_key() == ns_b.cache_key()


def test_different_temperature_different_namespace_key():
    ns_a = build_namespace(MESSAGES_WITH_SYSTEM, model="gpt-4o-mini", temperature=0.0)
    ns_b = build_namespace(MESSAGES_WITH_SYSTEM, model="gpt-4o-mini", temperature=0.7)
    assert ns_a.cache_key() != ns_b.cache_key()
