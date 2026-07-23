"""Model registry with list prices (USD per token).

Pricing as_of: 2026-07-22 — refresh when providers change list prices.
Source quotes are usually $/1M tokens; we store $/token (= $/1M / 1e6).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelConfig:
    provider: str
    model_id: str
    cost_per_input_token: float
    cost_per_output_token: float
    avg_latency_ms: float
    quality_tier: str  # "high" | "medium" | "low"


REGISTRY: dict[str, ModelConfig] = {
    # --- OpenAI ---
    "gpt-4o": ModelConfig(
        provider="openai",
        model_id="gpt-4o",
        cost_per_input_token=2.5e-6,  # $2.50 / 1M
        cost_per_output_token=1e-5,  # $10 / 1M
        avg_latency_ms=0.0,
        quality_tier="high",
    ),
    "gpt-4o-mini": ModelConfig(
        provider="openai",
        model_id="gpt-4o-mini",
        cost_per_input_token=1.5e-7,  # $0.15 / 1M
        cost_per_output_token=6e-7,  # $0.60 / 1M
        avg_latency_ms=0.0,
        quality_tier="medium",
    ),
    # --- Anthropic ---
    "claude-sonnet-4-6": ModelConfig(
        provider="anthropic",
        model_id="claude-sonnet-4-6",
        cost_per_input_token=3e-6,  # $3 / 1M
        cost_per_output_token=1.5e-5,  # $15 / 1M
        avg_latency_ms=0.0,
        quality_tier="high",
    ),
    "claude-haiku-4-5": ModelConfig(
        provider="anthropic",
        model_id="claude-haiku-4-5",
        cost_per_input_token=1e-6,  # $1 / 1M
        cost_per_output_token=5e-6,  # $5 / 1M
        avg_latency_ms=0.0,
        quality_tier="low",
    ),
    # --- Google ---
    "gemini-2.5-pro": ModelConfig(
        provider="google",
        model_id="gemini-2.5-pro",
        cost_per_input_token=1.25e-6,  # $1.25 / 1M
        cost_per_output_token=1e-5,  # $10 / 1M
        avg_latency_ms=0.0,
        quality_tier="high",
    ),
    "gemini-2.5-flash": ModelConfig(
        provider="google",
        model_id="gemini-2.5-flash",
        cost_per_input_token=3e-7,  # $0.30 / 1M
        cost_per_output_token=2.5e-6,  # $2.50 / 1M
        avg_latency_ms=0.0,
        quality_tier="medium",
    ),
    # --- xAI ---
    "grok-4.3": ModelConfig(
        provider="xai",
        model_id="grok-4.3",
        cost_per_input_token=1.25e-6,  # $1.25 / 1M
        cost_per_output_token=2.5e-6,  # $2.50 / 1M
        avg_latency_ms=0.0,
        quality_tier="high",
    ),
    # --- Local ---
    "llama3.2": ModelConfig(
        provider="ollama",
        model_id="llama3.2",
        cost_per_input_token=0.0,
        cost_per_output_token=0.0,
        avg_latency_ms=0.0,
        quality_tier="low",
    ),
}


if __name__ == "__main__":
    print(
        f"{'key':<22} {'provider':<10} {'tier':<8} {'$/1K in':>10} {'$/1K out':>10}"
    )
    print("-" * 64)
    for key, m in REGISTRY.items():
        print(
            f"{key:<22} {m.provider:<10} {m.quality_tier:<8} "
            f"{m.cost_per_input_token * 1000:>10.6f} "
            f"{m.cost_per_output_token * 1000:>10.6f}"
        )
