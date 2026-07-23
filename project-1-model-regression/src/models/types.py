from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EmailCategory(str, Enum):
    BILLING = "billing"
    TECHNICAL = "technical"
    ACCOUNT = "account"
    GENERAL = "general"


class ClassificationResult(BaseModel):
    category: EmailCategory
    summary: str = Field(..., description="One-sentence summary of the email")


class FewShotExample(BaseModel):
    input: str
    output: ClassificationResult


class PromptConfig(BaseModel):
    version: str
    created_at: datetime
    model: str
    system_prompt: str
    few_shot_examples: list[FewShotExample] = Field(default_factory=list)


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class GoldenTestCase(BaseModel):
    id: str
    input: str
    expected: ClassificationResult
    expected_difficulty: Difficulty
    notes: Optional[str] = None


class GoldenDataset(BaseModel):
    version: str
    created_at: datetime
    cases: list[GoldenTestCase]


class ClassifyOutput(BaseModel):
    result: ClassificationResult
    latency_ms: float
    tokens_in: int
    tokens_out: int


class CaseResult(BaseModel):
    case_id: str
    actual: ClassificationResult
    category_match: bool
    summary_score: int = Field(..., ge=1, le=5)
    latency_ms: float
    tokens_in: int
    tokens_out: int
    passed: bool


class EvalRun(BaseModel):
    run_id: UUID = Field(default_factory=uuid4)
    prompt_version: str
    model: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    case_results: List[CaseResult]
    pass_rate: float
    category_accuracy: Dict[str, float]
    avg_latency_ms: float
    total_tokens: int


class Severity(str, Enum):
    PASS = "pass"
    WARN = "warn"
    CRITICAL = "critical"


class CaseFlip(BaseModel):
    case_id: str
    baseline: CaseResult
    current: CaseResult


class RunComparison(BaseModel):
    baseline_run_id: UUID
    current_run_id: UUID
    pass_rate_delta: float
    category_deltas: Dict[str, float]
    regressions: List[CaseFlip]
    improvements: List[CaseFlip]
    severity: Severity


class ThresholdConfig(BaseModel):
    warn_delta_pct: float = 0.03
    critical_delta_pct: float = 0.08
    drift_window_runs: int = 7
    drift_threshold_pct: float = 0.05
    summary_pass_score: int = 4

    @classmethod
    def from_env(cls) -> "ThresholdConfig":
        import os

        return cls(
            warn_delta_pct=float(os.getenv("THRESHOLD_WARN", "0.03")),
            critical_delta_pct=float(os.getenv("THRESHOLD_CRITICAL", "0.08")),
            drift_window_runs=int(os.getenv("DRIFT_WINDOW_RUNS", "7")),
            drift_threshold_pct=float(os.getenv("DRIFT_THRESHOLD_PCT", "0.05")),
            summary_pass_score=int(os.getenv("SUMMARY_PASS_SCORE", "4")),
        )
