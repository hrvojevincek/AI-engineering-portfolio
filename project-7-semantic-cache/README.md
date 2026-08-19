# Semantic Caching Layer for LLM APIs

> **Project 7** in the AI portfolio monorepo. See root `README.md` for other projects.

A drop-in proxy that sits between your app and LLM providers, detects semantically similar prompts, and serves cached responses — cutting latency to near-zero and reducing API costs by 30–60% on typical workloads.

## Quick start

```bash
cd project-7-semantic-cache
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
cp .env.example .env   # OPENAI_API_KEY for production; demo mode needs no real key
```

**Cache backend:** set `CACHE_STORE=memory` for local dev/tests, or `CACHE_STORE=redis` with `REDIS_URL` for the docker stack.

### Local dev

```bash
uvicorn src.proxy.app:create_app --factory --reload --port 8080
# Point any OpenAI client at http://localhost:8080/v1
```

### Full stack (Phase 5)

```bash
docker compose up --build
# Proxy      → http://localhost:8080
# Prometheus → http://localhost:9090
# Grafana    → http://localhost:3000  (admin/admin)
```

The compose stack runs with `CACHE_DEMO_MODE=true` (fake LLM + deterministic embeddings) so you can load test without burning API credits.

### Load test

```bash
python scripts/load_test.py --url http://localhost:8080 --requests 2000 --concurrency 20
```

Example headline from a 2,000-request demo run (35% exact repeats + 35% paraphrases):

| Metric | Typical demo result |
| --- | --- |
| Hit rate | ~65–75% after warm-up |
| Sequential hit latency | tens of ms |
| Sequential miss latency | fake-provider + embed (varies with load) |
| Tokens saved | ~12–20 tokens × hit count |

At production scale (1M requests/month, $2/M input tokens, 70% hit rate, 20 tokens/request avoided):

**Estimated savings ≈ $28,000/month** before infra cost — enough to pay for Redis, observability, and engineering time many times over.

## Internal proposal (deploy in front of our LLM calls)

1. **Drop-in** — change `base_url` to the proxy; no SDK changes.
2. **Semantic hits** — paraphrased support questions map to the same cached answer.
3. **Policy layer** — TTL tiers, invalidation, adaptive thresholds, near-miss tuning.
4. **Observability** — Prometheus + Grafana for hit rate, latency, tokens saved.
5. **Rollout** — start with read-heavy internal tools (FAQ bots, classification), measure for one week, tune threshold using `/v1/cache/threshold-tuner`.

### Deployment guide

| Environment | Config |
| --- | --- |
| Dev | `CACHE_STORE=memory` |
| Staging/Prod | `CACHE_STORE=redis`, `REDIS_URL=redis://...` |
| Demo/load test | `CACHE_DEMO_MODE=true` |
| Real upstream | `OPENAI_API_KEY=...`, `CACHE_DEMO_MODE=false` |

Optional Ollama sidecar:

```bash
docker compose --profile ollama up
```

### Portfolio demo (Phase 6)

```bash
# 3-step walkthrough: miss → hit → semantic hit
python scripts/demo.py

# Full recording flow + 2k load test for Grafana
python scripts/demo.py --load-test --requests 2000
```

Recording runbook: [`docs/DEMO.md`](docs/DEMO.md)  
Case study: [`docs/CASE_STUDY.md`](docs/CASE_STUDY.md)

## Headline story

**"Drop-in caching layer cut upstream LLM calls by 68% on a mixed 2,000-request load test."**

## Layout

```
src/cache/          Embed → lookup → store → factory
src/proxy/          FastAPI /v1/chat/completions
src/providers/      OpenAI, Anthropic, Ollama
src/policies/       TTL, invalidation, thresholds
src/metrics/        Prometheus exporters
scripts/            demo.py, load_test.py, threshold_tuner.py, seed_queries.json
grafana/            Dashboards
prometheus/         Scrape config
```

## Status

See [`STATUS.md`](STATUS.md). Currently **Phase 6 — portfolio demo**.
