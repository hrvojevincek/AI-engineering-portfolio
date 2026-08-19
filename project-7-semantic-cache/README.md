# Semantic Caching Layer for LLM APIs

> **Project 7** in the AI portfolio monorepo. See root `README.md` for other projects.

A drop-in proxy that sits between your app and LLM providers, detects semantically similar prompts, and serves cached responses — cutting latency to near-zero and reducing API costs by 30–60% on typical workloads.

## Quick start

```bash
cd project-7-semantic-cache
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
cp .env.example .env   # OPENAI_API_KEY (required); REDIS_URL (Phase 5)
```

**Cache backend:** local dev uses an **in-memory** store (`MemoryCacheStore`) — fast for tests, resets on restart. Production target is **Redis + RedisVL** (`src/cache/redis_store.py`); wired via docker-compose in Phase 5.

Phase 1+ commands:

```bash
# Run the cache proxy locally
uvicorn src.proxy.app:create_app --factory --reload --port 8080
# Point any OpenAI client at http://localhost:8080/v1
```

## Headline story

**"Change the base URL, save 40% on LLM spend."** — OpenAI-compatible proxy with semantic cache hits, streaming pass-through, and Grafana dashboards showing real cost savings.

## Layout (target)

```
src/cache/          Embed → lookup → store
src/proxy/          FastAPI /v1/chat/completions
src/providers/      OpenAI, Anthropic, Ollama
src/policies/       TTL, invalidation, thresholds
src/metrics/        Prometheus exporters
scripts/            Load test + seed queries
grafana/            Dashboards
```

## Status

See [`STATUS.md`](STATUS.md). Currently **Phase 3 — cache policies**.
