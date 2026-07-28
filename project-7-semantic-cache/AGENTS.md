# Agent Guide — Semantic Caching Layer

> **Project path:** `project-7-semantic-cache/` — run all commands from this directory.

## On Every Session

1. Read `STATUS.md` — current phase, next task, blockers.
2. Read only the **relevant phase section** in `docs/BUILD_GUIDE.md`.
3. Read `docs/SCHEMA.md` if touching cache entries, keys, or metrics.
4. **Update `STATUS.md`** after completing any checklist item.

## Token-Saving Rules

| User asks…                 | Read only…                                           |
| -------------------------- | ---------------------------------------------------- |
| "Where are we?" / progress | `STATUS.md`                                          |
| "Build phase N"            | `STATUS.md` + `BUILD_GUIDE.md` Phase N + `SCHEMA.md` |
| "How does X work?"         | Grep codebase + `SCHEMA.md`; skip full build guide   |
| Architecture overview      | `docs/ARCHITECTURE.md`                               |

Do **not** re-read the full PDF. Everything actionable is in `docs/`.

## Teaching Mode

User is **learning**, not just shipping. For each task:

1. Explain **what** we're building and **why** (1–2 sentences).
2. Give approach + stub/pseudocode; they fill in the meat (unless they say `just implement`).
3. Point to the interview talking point in `BUILD_GUIDE.md` when relevant.
4. Mark `STATUS.md` checklist when done.

## Conventions

- Python 3.12+ via **uv**: `uv venv` then `uv pip install -r requirements.txt`
- Cache entries in **Redis + RedisVL** (vector index)
- Proxy mirrors **OpenAI chat completions** API shape
- Env vars: `OPENAI_API_KEY`, `REDIS_URL`, optional `ANTHROPIC_API_KEY`

## Target Layout (create as needed)

```
src/
  cache/              # embed, lookup, store, eviction
  proxy/              # FastAPI OpenAI-compatible routes
  providers/          # OpenAI, Anthropic, Ollama adapters
  policies/           # TTL tiers, invalidation, adaptive thresholds
  metrics/            # Prometheus instrumentation
scripts/              # load test, threshold tuner, seed queries
grafana/              # pre-built dashboards
docker-compose.yml
Dockerfile
```
