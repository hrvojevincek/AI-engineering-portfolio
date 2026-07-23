# LLM Cost Autopilot

> **Project 2** in the AI portfolio monorepo. See root `README.md` for other projects.

Routing layer: classify prompt complexity → cheapest capable model → verify vs gpt-4o → escalate on failure → audit + savings %.

## Quick start

```bash
cd project-2-llm-cost-autopilot
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
cp .env.example .env   # OPENAI_API_KEY

# train classifier (once)
python scripts/train_classifier.py

# API
uvicorn src.api.app:app --reload --port 8000
```

```bash
curl -s localhost:8000/v1/completions \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"What is 17 + 25? Answer with the number only.","kind":"exact"}'
```

```bash
python scripts/cost_report.py   # leads with COST REDUCTION %
```

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/v1/completions` | Router picks model; returns text + metadata |
| GET | `/v1/models` | Registry + prices |
| GET | `/v1/stats` | Savings vs always-gpt-4o |
| GET/PUT | `/v1/routing-config` | Tier → model map |

## Headline metric

**Cost reduction %** vs sending every request to gpt-4o — see `GET /v1/stats` and `scripts/cost_report.py`.

## Layout

```
config/routing.yaml     Tier → model
migrations/             SQLite schema versions
data/requests.db        Audit trail
data/models/            Trained classifier
src/router/             classify, routing, pipeline
src/verify/             score, verify, escalate, feedback
src/audit/              db, store, stats
src/api/app.py          FastAPI
```

## Docker

```bash
docker compose up --build
```
