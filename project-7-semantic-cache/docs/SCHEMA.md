# Schema — Semantic Caching Layer

Draft contracts. Refine in Phase 1–2 as we implement.

## Cache namespace (Phase 1)

Derived from request — never embed alone; always scope lookup:

```text
CacheNamespace
  system_prompt_hash: str    # SHA-256 of system message content
  model: str
  temperature: float | null
  max_tokens: int | null
  provider: openai | anthropic | ollama
```

## Cache entry (Phase 1)

```text
CacheEntry
  id: str                    # UUID
  namespace: CacheNamespace
  prompt_text: str            # concatenated user content (debug)
  embedding: list[float]      # text-embedding-3-small
  response: ChatCompletion    # full provider response JSON
  created_at: datetime
  expires_at: datetime
  hit_count: int
  tokens_saved: int           # cumulative on hits
  metadata:
    finish_reason: str
    prompt_tokens: int
    completion_tokens: int
```

## Lookup result (Phase 1)

```text
LookupResult
  status: HIT | MISS | NEAR_MISS
  similarity: float | null
  entry: CacheEntry | null
  threshold: float
```

## Proxy request/response (Phase 2)

Mirror OpenAI `ChatCompletionCreateParams` / `ChatCompletion` shapes. Add response header:

```text
X-Cache: HIT | MISS
X-Cache-Similarity: 0.97      # only on HIT
```

## TTL policy (Phase 3)

```text
TTLTier
  name: stable | default | time_sensitive | no_cache
  ttl_seconds: int
  classifier_hint: str | null   # optional rule/label from prompt classifier
```

## Invalidation (Phase 3)

```text
InvalidateRequest
  by: system_prompt_hash | model | tag | prefix
  value: str
```

## Prometheus metrics (Phase 4)

| Metric                         | Type      | Labels                      |
| ------------------------------ | --------- | --------------------------- |
| `cache_requests_total`         | counter   | `result=hit\|miss`, `model` |
| `cache_lookup_latency_seconds` | histogram | —                           |
| `cache_similarity_score`       | histogram | `result`                    |
| `cache_tokens_saved_total`     | counter   | `model`                     |
| `cache_entries_active`         | gauge     | —                           |
| `cache_near_miss_total`        | counter   | `model`                     |

## Near-miss log (Phase 4)

```text
NearMiss
  query_text: str
  best_similarity: float
  threshold: float
  gap: float                   # threshold - best_similarity
  timestamp: datetime
```
