"""OpenAI-compatible request/response models for the cache proxy."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from src.policies.invalidation import InvalidateBy


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "developer", "tool"]
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage] = Field(..., min_length=1)
    temperature: float | None = None
    max_tokens: int | None = None
    stream: bool = False

    def as_message_dicts(self) -> list[dict[str, str]]:
        return [message.model_dump() for message in self.messages]


class InvalidateRequest(BaseModel):
    by: InvalidateBy
    value: str = Field(..., min_length=1)


class InvalidateResponse(BaseModel):
    deleted: int
    by: InvalidateBy
    value: str


class TunerQuery(BaseModel):
    prompt_text: str = Field(..., min_length=1)
    model: str
    system_prompt: str = ""
    temperature: float | None = None
    max_tokens: int | None = None


class ThresholdTunerRequest(BaseModel):
    thresholds: list[float] = Field(default_factory=lambda: [0.90, 0.95, 0.98])
    queries: list[TunerQuery] | None = None


class ThresholdResult(BaseModel):
    threshold: float
    hit_rate: float
    miss_rate: float
    near_miss_rate: float
    paraphrase_hit_rate: float


class ThresholdTunerResponse(BaseModel):
    query_count: int
    results: list[ThresholdResult]
