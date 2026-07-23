"""Predict complexity tier (1|2|3) from a raw prompt."""

from __future__ import annotations

from pathlib import Path

import joblib

from src.verify.feedback import extract_features

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL = ROOT / "data" / "models" / "complexity_clf.joblib"

FMT = {"low": 0, "medium": 1, "high": 2}

_clf = None


def features_to_vector(features: dict) -> list[float]:
    """Same order as scripts/train_classifier.row_to_features."""
    return [
        float(features["token_count"]),
        float(features["has_analyze_verb"]),
        float(features["num_constraints"]),
        float(features["has_context"]),
        float(FMT[features["output_format_complexity"]]),
    ]


def load_classifier(path: Path | None = None):
    global _clf
    path = path or DEFAULT_MODEL
    if not path.exists():
        raise FileNotFoundError(
            f"Classifier not found at {path}. Run: python scripts/train_classifier.py"
        )
    bundle = joblib.load(path)
    _clf = bundle["model"] if isinstance(bundle, dict) else bundle
    return _clf


def predict_tier(prompt: str, *, path: Path | None = None) -> int:
    """Return complexity tier 1, 2, or 3."""
    global _clf
    if _clf is None or path is not None:
        load_classifier(path)
    assert _clf is not None
    vec = features_to_vector(extract_features(prompt))
    return int(_clf.predict([vec])[0])


if __name__ == "__main__":
    for p in (
        "What is 17 + 25? Answer with the number only.",
        "Summarize in one sentence: The team shipped v2 on Monday.",
        "Compare PostgreSQL vs SQLite for a small internal tool. Two short paragraphs.",
    ):
        print(f"tier {predict_tier(p)} ← {p[:60]}...")
