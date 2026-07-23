"""Tier → ModelConfig from config/routing.yaml."""

from __future__ import annotations

from pathlib import Path

import yaml

from src.models.registry import REGISTRY, ModelConfig

DEFAULT_ROUTING = (
    Path(__file__).resolve().parents[2] / "config" / "routing.yaml"
)

_cache: dict[int, ModelConfig] | None = None


def load_routing(path: Path | None = None) -> dict[int, ModelConfig]:
    """Map complexity tier → ModelConfig from YAML registry keys."""
    path = path or DEFAULT_ROUTING
    raw = yaml.safe_load(path.read_text())
    out: dict[int, ModelConfig] = {}
    for tier, name in raw["tiers"].items():
        if name not in REGISTRY:
            raise KeyError(f"Unknown model {name!r} in {path}")
        out[int(tier)] = REGISTRY[name]
    return out


def model_for_tier(tier: int, *, path: Path | None = None) -> ModelConfig:
    """Resolve one tier to a ModelConfig (cached unless custom path)."""
    global _cache
    if path is not None:
        table = load_routing(path)
        if tier not in table:
            raise KeyError(f"No routing for tier {tier}")
        return table[tier]
    if _cache is None:
        _cache = load_routing()
    if tier not in _cache:
        raise KeyError(f"No routing for tier {tier}")
    return _cache[tier]


def reload_routing(path: Path | None = None) -> dict[int, ModelConfig]:
    """Clear cache and reload YAML (for PUT /v1/routing-config later)."""
    global _cache
    _cache = load_routing(path)
    return _cache


if __name__ == "__main__":
    for tier in (1, 2, 3):
        m = model_for_tier(tier)
        print(f"tier {tier} → {m.model_id} ({m.provider})")
