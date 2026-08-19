# Project Status — Project 7: Semantic Caching Layer

> **Location:** `project-7-semantic-cache/`  
> **Agent:** Read this file first for "where are we?" questions. Update after every completed task.

## Snapshot

| Field            | Value                         |
| ---------------- | ----------------------------- |
| **Phase**        | 4 — Monitoring & Analytics    |
| **Next task**    | Phase 4.1 — Prometheus metrics |
| **Last updated** | 2026-08-19                    |

## Phase Checklist

### Phase 1 — Cache Index & Similarity Engine (Day 1–3)

- [x] 1.1 Cache key: embed prompt + hash system prompt + generation params
- [x] 1.2 Similarity lookup: cosine threshold (start 0.95) → hit or miss
- [x] 1.3 Cache storage: response + metadata (TTL, hit count, tokens, model)
- [x] 1.4 Param isolation: different system prompt / temp / model → separate entries

### Phase 2 — Drop-In Proxy API (Day 3–5)

- [x] 2.1 Mirror OpenAI `/v1/chat/completions` contract (change base URL only)
- [x] 2.2 `X-Cache: HIT|MISS` header on responses
- [x] 2.3 OpenAI provider routing by `model` field
- [ ] 2.3b Anthropic + Ollama adapters (currently 501 stubs)
- [x] 2.4 Streaming: pass-through on miss, buffer complete response before caching

### Phase 3 — Cache Policies & Eviction (Day 5–8)

- [x] 3.1 TTL tiers (stable vs time-sensitive prompts; auto-classifier)
- [x] 3.2 Invalidation: system-prompt hash change, model upgrade, manual by prefix/tag
- [x] 3.3 Threshold tuner endpoint (hit rate vs accuracy tradeoff visualization)
- [x] 3.4 Adaptive thresholds by request type (classification vs creative)

### Phase 4 — Monitoring & Analytics (Day 8–10)

- [ ] 4.1 Prometheus metrics: hit rate, latency, cost savings, similarity distribution
- [ ] 4.2 Grafana dashboard (hit rate, savings, P50/P95 latency, capacity)
- [ ] 4.3 Near-miss analyzer (queries just below threshold)

### Phase 5 — Containerize & Load Test (Day 10–12)

- [ ] 5.1 docker-compose: proxy, Redis+RedisVL, Prometheus, Grafana, optional Ollama
- [ ] 5.2 Load test: 2,000+ requests, mixed unique/repeated queries
- [ ] 5.3 README as internal proposal (savings projection + deployment guide)

### Phase 6 — Portfolio (Day 12–14)

- [ ] 6.1 Demo: miss → hit → semantic hit → Grafana savings
- [ ] 6.2 Case study headline: "X% cost cut, Y% P95 latency reduction"

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
src/cache/          embed, lookup, store, redis_store
src/proxy/          app, schemas, streaming
src/providers/      OpenAI adapter, router, fakes
src/policies/       TTL, invalidation, threshold tuner, adaptive thresholds
tests/              unit + proxy integration tests
```

## Decisions Log

| Date       | Decision                            | Rationale                                      |
| ---------- | ----------------------------------- | ---------------------------------------------- |
| 2026-07-28 | Folder = `project-7-semantic-cache` | Matches monorepo naming + guide #7             |
| 2026-07-28 | Vector store = Redis + RedisVL      | Guide default; sub-ms lookups, docker-friendly |
| 2026-08-19 | Dev default = in-memory cache store | Fast local/tests; Redis wired in Phase 5       |

## Session Notes

Phase 3 complete (TTL tiers, invalidation, threshold tuner, adaptive thresholds). Next: Phase 4 Prometheus metrics.
