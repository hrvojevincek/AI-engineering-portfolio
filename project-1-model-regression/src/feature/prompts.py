from pathlib import Path

import yaml

from src.models import PromptConfig

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


def load_prompt(version: str) -> PromptConfig:
    """Load a versioned prompt from prompts/v{version}.yaml."""
    path = PROMPTS_DIR / f"v{version}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")

    with path.open() as f:
        data = yaml.safe_load(f)

    return PromptConfig.model_validate(data)
