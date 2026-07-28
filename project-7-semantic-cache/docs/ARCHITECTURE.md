# Architecture — Semantic Caching Layer

```
Client (any OpenAI SDK)
        │
        ▼
┌───────────────────┐
│  FastAPI Proxy    │  POST /v1/chat/completions
│  (OpenAI shape)   │  X-Cache: HIT | MISS
└─────────┬─────────┘
          │
    embed prompt
          │
          ▼
┌───────────────────┐     HIT ──► return cached response
│  Redis + RedisVL  │
│  vector index     │     MISS ──► provider router
└─────────┬─────────┘                    │
          │                                ▼
          │                    ┌───────────────────────┐
          │                    │ OpenAI / Anthropic /  │
          │                    │ Ollama                │
          │                    └───────────┬───────────┘
          │                                │
          └◄──── store embedding + response (on complete miss)
```

## Core idea

LLM apps repeat semantically similar prompts constantly. A **semantic** cache (not string match) returns prior answers in milliseconds and skips billed tokens — without changing client code beyond the base URL.

## Components (V1)

| Piece           | Role                                          |
| --------------- | --------------------------------------------- |
| `cache/`        | Embed, similarity search, store, TTL eviction |
| `proxy/`        | OpenAI-compatible HTTP API                    |
| `providers/`    | Forward misses; stream + buffer               |
| `policies/`     | Cache key namespace, TTL tiers, invalidation  |
| `metrics/`      | Prometheus counters/histograms                |
| Redis + RedisVL | Vector index + metadata store                 |

## Cache key namespace

```
namespace = hash(system_prompt) + model + temperature + max_tokens
lookup_key = embed(user_messages) within namespace
```

Two prompts that look identical to a human but differ in system prompt or temperature must not share an entry.

## Data flow

1. **Request in** → parse messages → extract embeddable user content + cache namespace.
2. **Lookup** → nearest neighbor in RedisVL → similarity vs threshold.
3. **HIT** → increment hit count → return stored response + `X-Cache: HIT`.
4. **MISS** → route to provider → stream to client → on success, embed + store with TTL.
5. **Metrics** → record hit/miss, latency, tokens saved, similarity score.

## Non-goals (V1)

- Multi-tenant auth / API keys (add in V2 if needed)
- Cross-model cache sharing (entries are model-scoped)
- Caching failed or truncated streams
