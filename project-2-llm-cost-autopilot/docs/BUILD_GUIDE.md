# Build Guide — LLM Cost Autopilot

Condensed from the PDF (pages 7–12). Actionable phase checklist.

---

## Phase 1 — Unified Model Interface (Day 1–3)

**Goal:** One way to call any provider; every call returns cost + latency + tokens.

### 1.1 Model registry

```python
@dataclass
class ModelConfig:
    provider: str          # openai | anthropic | ollama
    model_id: str
    cost_per_input_token: float
    cost_per_output_token: float
    avg_latency_ms: float
    quality_tier: str      # high | medium | low
```

Populate with real pricing for: GPT-4o, GPT-4o-mini, Claude Sonnet, Claude Haiku, local Llama (Ollama — cost ≈ 0).

**Done when:** You can import a registry dict/list and print each model’s $/1K tokens.

### 1.2 Abstraction layer

```python
async def send_request(prompt: str, model: ModelConfig) -> Response
```

`Response` fields: `text`, `input_tokens`, `output_tokens`, `latency_ms`, `cost`, `model_id`.

Provider-specific HTTP/SDK calls stay behind this function.

**Done when:** Same call signature works for at least OpenAI + one other provider.

### 1.3 Baseline smoke test

Same 10 prompts → every model in the registry. Log outputs, costs, latencies (CSV/JSON is fine).

**Interview point:** Routing needs baseline cost/quality data before a classifier exists.

**Done when:** Script runs end-to-end and produces a comparison table.

---

## Phase 2 — Complexity Classifier (Day 3–6)

**Goal:** Predict which tier a prompt needs so we can map tier → cheap-enough model.

### Tiers

| Tier | Examples |
|------|----------|
| 1 — simple | Reformat, extract fields, Q&A from provided context |
| 2 — moderate | Summarize, classify, structured analysis |
| 3 — complex | Multi-step reasoning, creative gen, nuanced judgment |

### Steps

1. Hand-label **200+** prompts across tiers (features: token count, “analyze/compare” verbs, # constraints, context present?, output-format complexity).
2. Train sklearn (logistic regression or random forest). Target ≥ **80%** held-out accuracy — V1, not perfection.
3. YAML routing map: Tier 1 → cheapest; Tier 2 → mid; Tier 3 → highest.

**Interview point:** Classifier is a routing skeleton; quality comes from the verification flywheel later.

**Done when:** Train script prints accuracy + confusion matrix; YAML maps tiers to models.

---

## Phase 3 — Async Quality Verification (Day 6–9)

**Goal:** Return cheap answer fast; check quality in background; escalate when wrong.

1. Define “good enough” per task type (extraction fields, judge ≥4/5, label agreement vs GPT-4o).
2. After response: async job → highest-tier model → score agreement → log routing failures.
3. Auto-escalate on big gaps (log original model, escalated model, cost delta, quality gap).
4. Failures become new classifier training rows (weekly retrain = flywheel).

**Interview point:** Cost savings without a quality backstop is just silently wrong cheaper.

**Done when:** A deliberate mis-route triggers escalation + a logged failure row.

---

## Phase 4 — Logging & Cost Dashboard (Day 9–11)

**Goal:** Audit trail + the portfolio headline number.

Per request: timestamp, prompt hash, tier, model, cost, latency, verifier score, escalated?

Dashboard: daily/weekly cost vs always-GPT-4o (“you saved $X”), model mix pie, quality + escalation over time. **Lead with cost-reduction %.**

---

## Phase 5 — FastAPI (Day 11–13)

- `POST /v1/completions` — client does **not** pick the model; router does. Response includes metadata (model + why).
- `GET /v1/models`, `GET /v1/stats`, `PUT /v1/routing-config`
- docker-compose: API + background verifier + SQLite

---

## Phase 6 — Portfolio (Day 13–14)

Load test 500–1,000 prompts → savings report + dashboard screenshots + ≤4 min Loom + design-decision writeup.
