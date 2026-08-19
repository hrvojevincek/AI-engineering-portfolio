"""Phase 3.4 — adaptive similarity thresholds by request type."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from enum import Enum

from src.cache.lookup import DEFAULT_THRESHOLD


class RequestType(str, Enum):
    CLASSIFICATION = "classification"
    CREATIVE = "creative"
    DEFAULT = "default"


CLASSIFICATION_PATTERNS = (
    r"\bclassify\b",
    r"\bcategor(y|ize|ise)\b",
    r"\blabel\b",
    r"\bsentiment\b",
    r"\btrue or false\b",
    r"\byes or no\b",
    r"\bwhich of\b",
    r"\bpick one\b",
    r"\bis this\b",
    r"\bdoes this\b",
    r"\bspam or not\b",
)

CREATIVE_PATTERNS = (
    r"\bwrite\b",
    r"\bpoem\b",
    r"\bstory\b",
    r"\bcreative\b",
    r"\bbrainstorm\b",
    r"\bimagine\b",
    r"\bjoke\b",
    r"\bsong\b",
    r"\bcompose\b",
    r"\bhaiku\b",
    r"\bnovel\b",
)


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def classify_request_type(prompt_text: str) -> RequestType:
    normalized = prompt_text.lower().strip()
    if not normalized:
        return RequestType.DEFAULT
    if _matches_any(normalized, CLASSIFICATION_PATTERNS):
        return RequestType.CLASSIFICATION
    if _matches_any(normalized, CREATIVE_PATTERNS):
        return RequestType.CREATIVE
    return RequestType.DEFAULT


@dataclass(frozen=True)
class AdaptiveThresholdPolicy:
    classification_threshold: float = 0.90
    default_threshold: float = DEFAULT_THRESHOLD
    creative_threshold: float = 0.98
    skip_creative: bool = False

    @classmethod
    def from_env(cls) -> AdaptiveThresholdPolicy:
        default = float(os.getenv("CACHE_SIMILARITY_THRESHOLD", str(DEFAULT_THRESHOLD)))
        return cls(
            classification_threshold=float(os.getenv("CACHE_THRESHOLD_CLASSIFICATION", "0.90")),
            default_threshold=float(os.getenv("CACHE_THRESHOLD_DEFAULT", str(default))),
            creative_threshold=float(os.getenv("CACHE_THRESHOLD_CREATIVE", "0.98")),
            skip_creative=os.getenv("CACHE_SKIP_CREATIVE", "false").lower() == "true",
        )

    def request_type_for(self, prompt_text: str) -> RequestType:
        return classify_request_type(prompt_text)

    def threshold_for(self, prompt_text: str) -> float | None:
        request_type = self.request_type_for(prompt_text)
        if request_type == RequestType.CREATIVE and self.skip_creative:
            return None
        if request_type == RequestType.CLASSIFICATION:
            return self.classification_threshold
        if request_type == RequestType.CREATIVE:
            return self.creative_threshold
        return self.default_threshold

    def caching_enabled_for(self, prompt_text: str) -> bool:
        return self.threshold_for(prompt_text) is not None
