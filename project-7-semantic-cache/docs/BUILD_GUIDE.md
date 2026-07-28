# Build Guide — Semantic Caching Layer

Condensed from the PDF (pages 32–37). Actionable phase checklist.

---

## Phase 1 — Cache Index & Similarity Engine (Day 1–3)

**Goal:** Embed prompts, find near-duplicates in RedisVL, store and retrieve full LLM responses.

### Steps

1. **Cache key strategy** — Embed every user prompt with `text-embedding-3-small`. Combine with hashes of system prompt + generation params (`model`, `temperature`, `max_tokens`) so different configs never collide.
2. **Similarity lookup** — On request: embed prompt → query vector store for nearest neighbor. Cosine similarity ≥ threshold (start **0.95**) = **HIT**; else **MISS** → forward to provider.
3. **Cache storage** — On miss: call LLM, store embedding + full response + metadata (timestamp, TTL expiry, hit count, token counts, model, finish reason, original prompt text for debug).
4. **Parameter isolation** — Same user text + different system prompt or temperature = different cache namespace.

**Interview point:** Exact string matching misses paraphrases; semantic cache is the ROI story engineering managers get instantly.

**Done when:** You can store a response, query with a paraphrased prompt, and get a cache hit with the stored answer.

---

## Phase 2 — Drop-In Proxy API (Day 3–5)

**Goal:** Any client switches base URL only — zero SDK changes.

1. **Mirror OpenAI contract** — `POST /v1/chat/completions` accepts the same JSON body; returns the same shape + `X-Cache: HIT|MISS` header.
2. **Provider routing** — Route by `model` field to OpenAI, Anthropic, or Ollama. Cache is provider-agnostic in logic but entries are scoped per provider/model.
3. **Streaming** — Hits return instantly (no stream). Misses stream from provider to client while buffering; only cache **complete, successful** responses.

**Interview point:** Streaming + caching is the hard part — partial responses must not be cached.

**Done when:** `curl` against your proxy with `OPENAI_BASE_URL` swapped returns identical JSON to direct OpenAI, with cache header on repeat/paraphrased calls.

---

## Phase 3 — Cache Policies & Eviction (Day 5–8)

**Goal:** Tunable freshness vs hit rate; safe invalidation.

1. **TTL tiers** — Long TTL (24h+) for stable/factual queries; short (1h) or no-cache for time-sensitive prompts. Optional classifier auto-assigns tier from prompt content.
2. **Invalidation** — On system-prompt hash change → purge matching entries. On model upgrade → purge by model. API endpoints for manual invalidation by prefix/tag.
3. **Threshold tuner** — Endpoint that replays historical queries at different thresholds: show hit rate vs "wrong answer" rate at 0.90 vs 0.98.
4. **Adaptive thresholds** — Classification tasks tolerate lower similarity (~0.90); creative generation needs ~0.98 or skip cache entirely.

**Interview point:** The threshold tradeoff visualization is the core design discussion — not "we used Redis."

**Done when:** You can invalidate by tag, tune threshold with data, and see different TTLs applied by prompt type.

---

## Phase 4 — Monitoring & Analytics (Day 8–10)

**Goal:** Prove savings with numbers.

1. **Prometheus metrics** — Hit rate (overall + per-model), latency hits vs misses, estimated cost savings, cache size/eviction rate, similarity score distribution, near-miss counts.
2. **Grafana dashboard** — Real-time hit rate, cumulative cost savings, P50/P95/P99 latency comparison, capacity utilization, threshold effect over 7 days.
3. **Near-miss analyzer** — Log queries just below threshold; surface candidates for lower threshold or query normalization (strip filler words before embed).

**Done when:** Dashboard shows live metrics during a demo run; near-miss report exports to CSV or API.

---

## Phase 5 — Containerize & Load Test (Day 10–12)

**Goal:** Portfolio-grade numbers.

1. **docker-compose** — FastAPI proxy, Redis+RedisVL, Prometheus, Grafana, optional Ollama. Pre-seed Grafana dashboards.
2. **Load test** — 2,000+ requests, mix of unique and repeated/paraphrased queries. Measure hit rate convergence, latency percentiles, total savings.
3. **README as proposal** — Frame as internal doc: "Deploy in front of our LLM calls → save $X/month." Include load test results + deployment guide.

**Done when:** `docker compose up` → run load test script → Grafana shows headline metrics.

---

## Phase 6 — Portfolio (Day 12–14)

1. **Demo (<4 min)** — Fresh query (slow miss) → exact repeat (hit) → paraphrase (semantic hit) → Grafana savings climbing.
2. **Case study** — Lead with: _"Drop-in caching layer reduced LLM API costs by X% and P95 latency by Y% on a 2,000-request load test."_
