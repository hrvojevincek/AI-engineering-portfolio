# Schema — LLM Cost Autopilot

Contracts we will implement. Refine when code lands.

## ModelConfig

| Field                   | Type    | Notes                               |
| ----------------------- | ------- | ----------------------------------- |
| `provider`              | `str`   | `openai` \| `anthropic` \| `ollama` |
| `model_id`              | `str`   | e.g. `gpt-4o-mini`                  |
| `cost_per_input_token`  | `float` | USD per token                       |
| `cost_per_output_token` | `float` | USD per token                       |
| `avg_latency_ms`        | `float` | Baseline from smoke tests           |
| `quality_tier`          | `str`   | `high` \| `medium` \| `low`         |

## Response

| Field           | Type    | Notes             |
| --------------- | ------- | ----------------- |
| `text`          | `str`   | Model output      |
| `input_tokens`  | `int`   |                   |
| `output_tokens` | `int`   |                   |
| `latency_ms`    | `float` |                   |
| `cost`          | `float` | USD for this call |
| `model_id`      | `str`   |                   |

## Complexity dataset (Phase 2)

File: `data/prompts/v1.0.0.json` (JSON array). Seed = 10 baseline prompts; grow to 200+.

```json
{
  "id": "t1-001",
  "prompt": "...",
  "tier": 1,
  "features": {
    "token_count": 40,
    "has_analyze_verb": false,
    "num_constraints": 1,
    "has_context": true,
    "output_format_complexity": "low"
  },
  "notes": "optional"
}
```

## Routing config (YAML, Phase 2)

```yaml
tiers:
  1: claude-haiku # or ollama local
  2: gpt-4o-mini
  3: gpt-4o
```

## Request log row (Phase 4)

| Field                            | Notes                                       |
| -------------------------------- | ------------------------------------------- |
| `timestamp`                      | ISO UTC                                     |
| `prompt_hash`                    | SHA256 prefix — don’t store raw prompts     |
| `complexity_tier`                | 1\|2\|3                                     |
| `routed_model` / `final_model`   | After escalate may differ                   |
| `cost`                           | USD for this request                        |
| `latency_ms`                     |                                             |
| `quality_score`                  | From verifier                               |
| `escalated`                      | 0/1                                         |
| `input_tokens` / `output_tokens` | For baseline vs gpt-4o math (migration 002) |

Migrations: `migrations/NNN_*.sql` applied via `PRAGMA user_version` in `src/audit/db.py`.
