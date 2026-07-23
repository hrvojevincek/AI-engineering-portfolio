# Project Status — Project 2: LLM Cost Autopilot

> **Location:** `project-2-llm-cost-autopilot/`  
> **Agent:** Read this file first for "where are we?" questions. Update after every completed task.

## Snapshot

| Field            | Value                                  |
| ---------------- | -------------------------------------- |
| **Phase**        | 5 — Complete ✓ (local API)             |
| **Next task**    | Phase 6 — Portfolio polish / load test |
| **Blockers**     | None                                   |
| **Last updated** | 2026-07-23                             |

## Phase Checklist

### Phase 1 — Unified Model Interface (Day 1–3)

- [x] 1.1 `ModelConfig` registry with real pricing (OpenAI, Anthropic, Google, xAI, Ollama)
- [x] 1.2 `send_request(prompt, model_config) → Response` abstraction (OpenAI only for V1)
- [x] 1.3 Smoke-test OpenAI models on the same 10 prompts; log cost/latency

### Phase 2 — Complexity Classifier (Day 3–6)

- [x] 2.1 Define Tier 1 / 2 / 3 complexity (`docs/TIER.MD`)
- [x] 2.2 Hand-labeled 200+ prompts + extracted features (200 rows: 70/70/60)
- [x] 2.3 Train sklearn classifier (target ≥80% held-out accuracy) — 95% RF
- [x] 2.4 YAML routing map: tier → model (`config/routing.yaml`)

### Phase 3 — Async Quality Verification (Day 6–9)

- [x] 3.1 Quality thresholds per request type (`docs/quality.md`)
- [x] 3.2 Async verifier (compare cheap vs highest-tier) — exact + open judge
- [x] 3.3 Auto-escalation on quality gap (`src/verify/escalate.py`)
- [x] 3.4 Failure → classifier feedback loop (`failures.jsonl` + train merge)

### Phase 4 — Logging & Cost Dashboard (Day 9–11)

- [x] 4.1 SQLite audit trail per request (`src/audit/`)
- [x] 4.2 Cost dashboard (saved $ vs always-GPT-4o) — `scripts/cost_report.py` + `stats.py`
- [x] 4.3 Headline cost-reduction % metric (`cost_report.py` leads with it)

### Phase 5 — FastAPI Surface (Day 11–13)

- [x] 5.1 `POST /v1/completions` (router picks model) — `pipeline` + `src/api/app.py`
- [x] 5.2 `GET /v1/models`, `GET /v1/stats`, `PUT /v1/routing-config`
- [x] 5.3 docker-compose + internal-style README

### Phase 6 — Portfolio (Day 13–14)

- [ ] 6.1 Load test 500–1,000 prompts + savings report
- [ ] 6.2 Loom + case-study writeup

## Files Present

```
STATUS.md
AGENTS.md
README.md
docs/BUILD_GUIDE.md
docs/ARCHITECTURE.md
docs/SCHEMA.md
requirements.txt
.env.example
```

## Decisions Log

| Date       | Decision                                  | Rationale                                                     |
| ---------- | ----------------------------------------- | ------------------------------------------------------------- |
| 2026-07-22 | Folder = `project-2-llm-cost-autopilot`   | Matches monorepo naming + guide #2                            |
| 2026-07-22 | V1 providers = OpenAI only                | Ship abstraction + baseline first; add Anthropic/others later |
| 2026-07-23 | SQLite migrations + `PRAGMA user_version` | Version schema without Alembic for one-table V1               |

## Session Notes

Scaffold only. Start Phase 1.1 next.
