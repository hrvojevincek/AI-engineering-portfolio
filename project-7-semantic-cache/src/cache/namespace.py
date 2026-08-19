"""Phase 1.1 — derive cache namespace + embeddable user text from chat messages."""

from __future__ import annotations

import hashlib
from typing import Any

from src.models.types import CacheNamespace, Provider


def hash_system_prompt(system_content: str) -> str:
    """SHA-256 hex digest of the system message content."""
    return hashlib.sha256(system_content.encode("utf-8")).hexdigest()


def _extract_role_content(messages: list[dict[str, Any]], role: str) -> str:
    parts = [
        msg["content"]
        for msg in messages
        if msg.get("role") == role and msg.get("content")
    ]
    return "\n".join(parts)


def extract_system_prompt(messages: list[dict[str, Any]]) -> str:
    """Return concatenated system message content, or empty string if none."""
    return _extract_role_content(messages, "system")


def extract_user_text(messages: list[dict[str, Any]]) -> str:
    """Return text we will embed for similarity search.

    Hint: concatenate user-role message content in order.
    Skip system/assistant for the embedding input.
    """
    return _extract_role_content(messages, "user")


def infer_provider(model: str) -> Provider:
    """Rough model → provider mapping for V1."""
    name = model.lower()
    if name.startswith("gpt-"):
        return Provider.OPENAI
    elif name.startswith("claude-"):
        return Provider.ANTHROPIC
    else:
        return Provider.OLLAMA


def build_namespace(
    messages: list[dict[str, Any]],
    *,
    model: str,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> CacheNamespace:
    """Build the namespace that scopes semantic lookup for this request."""
    system = extract_system_prompt(messages)
    system_prompt_hash = hash_system_prompt(system)
    provider = infer_provider(model)

    return CacheNamespace(
        system_prompt_hash=system_prompt_hash,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        provider=provider,
    )
