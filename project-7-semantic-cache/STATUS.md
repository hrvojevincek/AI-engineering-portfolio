# Project Status — Project 7: Semantic Caching Layer

> **Location:** `project-7-semantic-cache/`  
> **Agent:** Read this file first for "where are we?" questions. Update after every completed task.

## Snapshot

| Field            | Value                                     |
| ---------------- | ----------------------------------------- |
| **Phase**        | 1 — Cache Index                           |
| **Next task**    | Phase 1.4 — Param isolation integration tests |
| **Blockers**     | None                                      |
| **Last updated** | 2026-08-19                                |

## Phase Checklist

### Phase 1 — Cache Index & Similarity Engine (Day 1–3)

- [x] 1.1 Cache key: embed prompt + hash system prompt + generation params
- [x] 1.2 Similarity lookup: cosine threshold (start 0.95) → hit or miss
- [x] 1.3 Cache storage: response + metadata (TTL, hit count, tokens, model)
- [x] 1.4 Param isolation: different system prompt / temp / model → separate entries

### Phase 2 — Drop-In Proxy API (Day 3–5)

- [ ] 2.1 Mirror OpenAI `/v1/chat/completions` contract (change base URL only)
- [ ] 2.2 `X-Cache: HIT|MISS` header on responses
- [ ] 2.3 Provider routing: OpenAI, Anthropic, Ollama by `model` field
- [ ] 2.4 Streaming: pass-through on miss, buffer complete response before caching

### Phase 3 — Cache Policies & Eviction (Day 5–8)

- [ ] 3.1 TTL tiers (stable vs time-sensitive prompts; auto-classifier)
- [ ] 3.2 Invalidation: system-prompt hash change, model upgrade, manual by prefix/tag
- [ ] 3.3 Threshold tuner endpoint (hit rate vs accuracy tradeoff visualization)
- [ ] 3.4 Adaptive thresholds by request type (classification vs creative)

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
```

## Decisions Log

| Date       | Decision                            | Rationale                                      |
| ---------- | ----------------------------------- | ---------------------------------------------- |
| 2026-07-28 | Folder = `project-7-semantic-cache` | Matches monorepo naming + guide #7             |
| 2026-07-28 | Vector store = Redis + RedisVL      | Guide default; sub-ms lookups, docker-friendly |

## Session Notes

Phase 1 complete (namespace, lookup, in-memory store + Redis store). Next: Phase 2 proxy API.
