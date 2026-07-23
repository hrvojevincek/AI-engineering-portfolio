"""Load and validate the hand-labeled golden dataset."""

from pathlib import Path

from src.models import GoldenDataset

GOLDEN_DIR = Path(__file__).resolve().parents[2] / "data" / "golden"


def load_golden_dataset(version: str) -> GoldenDataset:
    path = GOLDEN_DIR / f"v{version}.json"
    if not path.exists():
        raise FileNotFoundError(f"Golden dataset not found: {path}")

    return GoldenDataset.model_validate_json(path.read_text())


def _summary() -> None:
    dataset = load_golden_dataset("1.0.0")
    by_category: dict[str, int] = {}
    by_difficulty: dict[str, int] = {}

    for case in dataset.cases:
        cat = case.expected.category.value
        by_category[cat] = by_category.get(cat, 0) + 1
        diff = case.expected_difficulty.value
        by_difficulty[diff] = by_difficulty.get(diff, 0) + 1

    print(f"Dataset v{dataset.version} — {len(dataset.cases)} cases")
    print("By category:", dict(sorted(by_category.items())))
    print("By difficulty:", dict(sorted(by_difficulty.items())))


if __name__ == "__main__":
    _summary()
