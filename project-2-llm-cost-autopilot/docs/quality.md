# Quality thresholds (Phase 3)

Rules for “is the cheap model’s answer good enough?”  
Reference model for verification: **`gpt-4o`** (registry key).  
Escalate when a check fails (see Phase 3.3).

## Global

| Setting           | Value                          | Notes                                 |
| ----------------- | ------------------------------ | ------------------------------------- |
| `ESCALATE_BELOW`  | `4`                            | Judge score 1–5; fail if score &lt; 4 |
| `REFERENCE_MODEL` | `gpt-4o`                       | Always compare against this           |
| Skip verify       | tier **3** already on `gpt-4o` | Optional: sample 10% later            |

## By request kind

| Kind           | Examples                                         | How we score                                                                           | Fail / escalate when |
| -------------- | ------------------------------------------------ | -------------------------------------------------------------------------------------- | -------------------- |
| **Exact-ish**  | extract email/date, yes/no, arithmetic, reformat | Normalize both answers (trim, lower, collapse spaces) then **exact match** vs `gpt-4o` | Strings not equal    |
| **Label**      | sentiment, category, P1/P2/P3                    | Same as exact-ish on the **label token** only                                          | Labels disagree      |
| **Open-ended** | summarize, compare, write email, explain         | LLM-as-judge: “Does candidate convey the same key facts as reference?” score **1–5**   | Score **&lt; 4**     |

## Judge prompt (V1)

Ask `gpt-4o` (or mini for cost) with:

- `prompt` (user task)
- `reference` (gpt-4o answer)
- `candidate` (routed/cheap answer)

Return JSON: `{ "score": <1-5>, "reason": "<one sentence>" }`.

Rubric:

- 5 — same facts / decision, minor wording diff OK
- 4 — small omission, still usable
- 3 — missing important point or mild error
- 1–2 — wrong, invented, or unusable

## Logging (for failures)

When a check fails, record at least:

- `prompt_hash`, `tier`, `routed_model`, `reference_model`
- `quality_score` (1 for match / 0 for mismatch; or judge 1–5)
- `escalated` (bool), `cost_delta` (after 3.3)

## Out of scope for V1

- Per-use-case custom extractors (regex field-by-field)
- Human review queue
- Retrain-from-failures automation (3.4) — log only first
