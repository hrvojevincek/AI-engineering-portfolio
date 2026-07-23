# Architecture — LLM Cost Autopilot

High-level shape. Update as phases land.

```
Client
  │
  ▼
FastAPI  POST /v1/completions
  │
  ├─► Complexity classifier  →  tier (1|2|3)
  │
  ├─► Routing map (YAML)     →  ModelConfig
  │
  ├─► send_request(...)      →  Response (text, cost, latency, tokens)
  │         │
  │         ▼
  │    Provider adapters (OpenAI / Anthropic / Ollama)
  │
  ├─► Return to client (+ routing metadata)
  │
  └─► Async verifier (highest-tier compare)
            │
            ├─ ok → log
            └─ fail → escalate (+ retrain signal)
```

## Design principles

1. **Unified interface first** — providers are swappable; cost/latency always measured.
2. **Route cheap, verify async** — don’t block the user on the expensive check unless escalating.
3. **Flywheel** — routing failures become classifier training data.
4. **Money shot** — every dashboard and README leads with cost reduction vs always-expensive.
