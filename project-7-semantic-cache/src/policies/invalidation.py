"""Phase 3.2 — cache invalidation rules."""

from __future__ import annotations

from enum import Enum

from src.models.types import CacheEntry


class InvalidateBy(str, Enum):
    SYSTEM_PROMPT_HASH = "system_prompt_hash"
    MODEL = "model"
    TAG = "tag"
    PREFIX = "prefix"


def entry_matches(entry: CacheEntry, by: InvalidateBy, value: str) -> bool:
    if by == InvalidateBy.SYSTEM_PROMPT_HASH:
        return entry.namespace.system_prompt_hash == value
    if by == InvalidateBy.MODEL:
        return entry.namespace.model == value
    if by == InvalidateBy.TAG:
        return value in entry.tags
    if by == InvalidateBy.PREFIX:
        return entry.prompt_text.startswith(value)
    return False
