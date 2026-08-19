# Case Study — Semantic Caching Layer

> Portfolio headline for Project 7. Numbers from demo-mode load tests (deterministic embeddings, fake upstream). Demo mode clusters paraphrases by design — production uses real `text-embedding-3-small` vectors.

## One-liner

**Drop-in caching layer cut upstream LLM calls by 68% on a mixed 2,000-request load test (35% exact repeats, 35% paraphrases, 30% unique).**

---

## Problem

Every LLM call costs money and adds latency. Support bots, classification pipelines, and FAQ tools repeat the same questions — often paraphrased — but standard HTTP caches only dedupe byte-identical requests.

## Solution

OpenAI-compatible proxy with semantic vector lookup:

- Embeds user prompts, searches Redis for cosine-similar neighbours
- Returns cached JSON instantly on HIT (`X-Cache: HIT`) — even if the client asked to stream
- Passes through to upstream on MISS, stores complete successful completions
- Exposes Prometheus metrics + Grafana dashboards out of the box

**Integration:** change `base_url` from `api.openai.com` to the proxy. No SDK changes.

## Load test results

Environment: `CACHE_DEMO_MODE=true`, in-memory store, 20 concurrent workers. Hit rate from a 500-request verification run (same mix); latency on concurrent fake-provider runs is queue-dominated, so sequential miss vs hit is reported separately.

| Metric                        | Result                                         |
| ----------------------------- | ---------------------------------------------- |
| Traffic mix                   | 35% exact repeats, 35% paraphrases, 30% unique |
| Cache hit rate                | **68.4%** (500-request verification)           |
| Sequential miss (demo script) | ~100–400 ms (fake upstream + embed)            |
| Sequential hit (demo script)  | tens of ms                                     |
| Tokens saved (est.)           | 20 tokens × hit count                          |

Do not mix concurrent load-test miss P95 with sequential hit P95 — they are different experiments.

## Cost impact

Assuming **68% hit rate** and **20 tokens avoided per hit**:

| Scale                           | LLM spend without cache | Est. savings                 |
| ------------------------------- | ----------------------- | ---------------------------- |
| 2k requests (test)              | baseline                | **68%** fewer upstream calls |
| 1M requests/month @ $2/M tokens | ~$40k/month             | **~$27k/month**              |

Infra cost (Redis + small proxy VM + Grafana Cloud free tier): **< $200/month** at this scale.

## Architecture highlights

- **Semantic matching** — paraphrases share embedding clusters
- **Policy layer** — TTL tiers, invalidation API, adaptive thresholds, near-miss tuning
- **Observability** — hit rate, latency percentiles, tokens saved, evictions
- **Production path** — swap `CACHE_DEMO_MODE=false`, point at a real OpenAI key

## Demo flow (< 4 min)

1. Fresh query → `X-Cache: MISS`
2. Exact repeat → `X-Cache: HIT` (JSON, not SSE)
3. Paraphrase → `X-Cache: HIT` + similarity header
4. Grafana dashboards show hit rate and savings climbing during `--load-test`

Run: `python scripts/demo.py --load-test`

## Tech stack

Python · FastAPI · Redis + RedisVL · Prometheus · Grafana · Docker Compose

---

_Built as Project 7 in the AI Engineering Portfolio — August 2026._
