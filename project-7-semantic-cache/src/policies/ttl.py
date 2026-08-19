"""Phase 3.1 — TTL tiers and prompt classifier."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from enum import Enum


class TTLTier(str, Enum):
    STABLE = "stable"
    DEFAULT = "default"
    TIME_SENSITIVE = "time_sensitive"
    NO_CACHE = "no_cache"


NO_CACHE_PATTERNS = (
    r"\breal[- ]?time\b",
    r"\blive feed\b",
    r"\bup to the minute\b",
    r"\bstreaming data\b",
)

TIME_SENSITIVE_PATTERNS = (
    r"\btoday\b",
    r"\btonight\b",
    r"\bright now\b",
    r"\bcurrently\b",
    r"\blatest\b",
    r"\bbreaking\b",
    r"\bweather\b",
    r"\bstock price\b",
    r"\bnews\b",
    r"\bscore\b",
    r"\bwho won\b",
    r"\bthis week\b",
    r"\bthis month\b",
    r"\byesterday\b",
    r"\btomorrow\b",
    r"\b20\d{2}\b",
)

STABLE_PATTERNS = (
    r"\bwhat is\b",
    r"\bwhat are\b",
    r"\bdefine\b",
    r"\bdefinition of\b",
    r"\bexplain\b",
    r"\bhow does\b",
    r"\bhow do\b",
    r"\bhistory of\b",
    r"\bdifference between\b",
)


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def classify_prompt(prompt_text: str) -> TTLTier:
    """Assign a TTL tier from prompt content using lightweight keyword rules."""
    normalized = prompt_text.lower().strip()
    if not normalized:
        return TTLTier.DEFAULT
    if _matches_any(normalized, NO_CACHE_PATTERNS):
        return TTLTier.NO_CACHE
    if _matches_any(normalized, TIME_SENSITIVE_PATTERNS):
        return TTLTier.TIME_SENSITIVE
    if _matches_any(normalized, STABLE_PATTERNS):
        return TTLTier.STABLE
    return TTLTier.DEFAULT


@dataclass(frozen=True)
class TTLPolicy:
    stable_seconds: int = 86_400
    default_seconds: int = 86_400
    time_sensitive_seconds: int = 3_600

    @classmethod
    def from_env(cls) -> TTLPolicy:
        default = int(os.getenv("CACHE_DEFAULT_TTL_SECONDS", "86400"))
        return cls(
            stable_seconds=int(os.getenv("CACHE_TTL_STABLE_SECONDS", str(default))),
            default_seconds=int(os.getenv("CACHE_TTL_DEFAULT_SECONDS", str(default))),
            time_sensitive_seconds=int(
                os.getenv("CACHE_TTL_TIME_SENSITIVE_SECONDS", "3600")
            ),
        )

    def tier_for(self, prompt_text: str) -> TTLTier:
        return classify_prompt(prompt_text)

    def ttl_seconds_for(self, prompt_text: str) -> int | None:
        tier = self.tier_for(prompt_text)
        if tier == TTLTier.NO_CACHE:
            return None
        if tier == TTLTier.STABLE:
            return self.stable_seconds
        if tier == TTLTier.TIME_SENSITIVE:
            return self.time_sensitive_seconds
        return self.default_seconds
