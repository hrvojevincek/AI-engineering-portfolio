"""Train a complexity-tier classifier from data/prompts/v1.0.0.json."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "prompts" / "v1.0.0.json"
FAILURES = ROOT / "data" / "prompts" / "failures.jsonl"
OUT = ROOT / "data" / "models" / "complexity_clf.joblib"

FMT = {"low": 0, "medium": 1, "high": 2}


def row_to_features(row: dict) -> list[float]:
    f = row["features"]
    return [
        float(f["token_count"]),
        float(f["has_analyze_verb"]),
        float(f["num_constraints"]),
        float(f["has_context"]),
        float(FMT[f["output_format_complexity"]]),
    ]


def load_xy(path: Path) -> tuple[list[list[float]], list[int]]:
    rows = json.loads(path.read_text())
    if FAILURES.exists():
        for line in FAILURES.read_text().splitlines():
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    X = [row_to_features(r) for r in rows]
    y = [int(r["tier"]) for r in rows]
    return X, y


def train_classifier() -> None:
    X, y = load_xy(DATA)

    # Hold out 20% to measure generalization (not memorization)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Ensemble of decision trees — good default for small tabular features
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Held-out accuracy: {acc:.1%}")
    print("Confusion matrix (rows=true, cols=pred) for tiers 1,2,3:")
    print(confusion_matrix(y_test, y_pred, labels=[1, 2, 3]))
    print(classification_report(y_test, y_pred, labels=[1, 2, 3]))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": clf, "feature_order": list(FMT.keys())}, OUT)
    print(f"Saved → {OUT}")


if __name__ == "__main__":
    train_classifier()
