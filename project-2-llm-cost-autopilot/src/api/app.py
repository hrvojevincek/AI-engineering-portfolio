"""FastAPI surface for the LLM Cost Autopilot."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.audit.db import get_conn
from src.audit.stats import compute_savings
from src.audit.store import fetch_all
from src.models.registry import REGISTRY
from src.router.pipeline import complete
from src.router.routing import DEFAULT_ROUTING, load_routing, reload_routing

load_dotenv()

app = FastAPI(
    title="LLM Cost Autopilot",
    description="Routes each prompt to the cheapest capable model; verifies and escalates.",
    version="0.1.0",
)


class CompletionRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    kind: Literal["exact", "label", "open"] = "open"


class RoutingConfigUpdate(BaseModel):
    tiers: dict[int, str] = Field(
        ...,
        description="Map tier → registry key, e.g. {1: 'gpt-4o-mini', 3: 'gpt-4o'}",
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/completions")
async def completions(body: CompletionRequest) -> dict[str, Any]:
    result = await complete(body.prompt, kind=body.kind)
    return {
        "text": result.text,
        "metadata": {
            "tier": result.tier,
            "routed_model": result.routed_model,
            "final_model": result.final_model,
            "escalated": result.escalated,
            "cost": result.cost,
            "latency_ms": result.latency_ms,
            "quality_score": result.quality_score,
            "verify_reason": result.verify_reason,
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "kind": result.kind,
        },
    }


@app.get("/v1/models")
def list_models() -> dict[str, Any]:
    return {
        "models": [
            {
                "key": key,
                "provider": m.provider,
                "model_id": m.model_id,
                "cost_per_input_token": m.cost_per_input_token,
                "cost_per_output_token": m.cost_per_output_token,
                "quality_tier": m.quality_tier,
            }
            for key, m in REGISTRY.items()
        ]
    }


@app.get("/v1/stats")
def stats() -> dict[str, Any]:
    with get_conn() as conn:
        s = compute_savings(fetch_all(conn))
    return {
        "headline_cost_reduction_pct": round(s.saved_pct, 1),
        "saved_usd": s.saved,
        "actual_cost_usd": s.actual_cost,
        "baseline_cost_usd": s.baseline_cost,
        "n_requests": s.n_requests,
        "n_with_tokens": s.n_with_tokens,
        "escalation_rate": s.escalation_rate,
    }


@app.get("/v1/routing-config")
def get_routing_config() -> dict[str, Any]:
    table = load_routing()
    return {"tiers": {str(t): m.model_id for t, m in sorted(table.items())}}


@app.put("/v1/routing-config")
def put_routing_config(body: RoutingConfigUpdate) -> dict[str, Any]:
    for name in body.tiers.values():
        if name not in REGISTRY:
            raise HTTPException(400, detail=f"Unknown model {name!r}")
    path = Path(DEFAULT_ROUTING)
    payload = {"tiers": {int(k): v for k, v in body.tiers.items()}}
    path.write_text(
        yaml.safe_dump(payload, sort_keys=True),
        encoding="utf-8",
    )
    reload_routing(path)
    return get_routing_config()
