# Schemas & Contracts

Reference for all data shapes. Implement as Pydantic models in `src/models/`.

---

## EmailCategory

```
billing | technical | account | general
```

---

## PromptConfig (from YAML)

| Field | Type | Required |
|-------|------|----------|
| version | string (semver) | yes |
| created_at | ISO datetime | yes |
| model | string | yes |
| system_prompt | string | yes |
| few_shot_examples | list[{input, output}] | no |

---

## ClassificationResult (LLM output)

| Field | Type | Required |
|-------|------|----------|
| category | EmailCategory | yes |
| summary | string (1 sentence) | yes |

---

## GoldenTestCase

| Field | Type | Required |
|-------|------|----------|
| id | string (stable, e.g. `billing-001`) | yes |
| input | string (email body) | yes |
| expected | ClassificationResult | yes |
| expected_difficulty | `easy \| medium \| hard` | yes |
| notes | string | no |

---

## GoldenDataset (JSON file)

| Field | Type | Required |
|-------|------|----------|
| version | string | yes |
| created_at | ISO datetime | yes |
| cases | list[GoldenTestCase] | yes |

---

## CaseResult (per eval run)

| Field | Type |
|-------|------|
| case_id | string |
| actual | ClassificationResult |
| category_match | bool |
| summary_score | int 1–5 |
| latency_ms | float |
| tokens_in | int |
| tokens_out | int |
| passed | bool |

`passed` = category_match AND summary_score >= 4

---

## EvalRun

| Field | Type |
|-------|------|
| run_id | UUID |
| prompt_version | string |
| model | string |
| timestamp | ISO datetime |
| case_results | list[CaseResult] |
| pass_rate | float |
| category_accuracy | dict[EmailCategory, float] |
| avg_latency_ms | float |
| total_tokens | int |

---

## RunComparison (diff)

| Field | Type |
|-------|------|
| baseline_run_id | UUID |
| current_run_id | UUID |
| pass_rate_delta | float |
| category_deltas | dict[EmailCategory, float] |
| regressions | list[{case_id, baseline, current}] |
| improvements | list[{case_id, baseline, current}] |
| severity | `pass \| warn \| critical` |

---

## ThresholdConfig

| Field | Default |
|-------|---------|
| warn_delta_pct | 0.03 |
| critical_delta_pct | 0.08 |
| drift_window_runs | 7 |
| drift_threshold_pct | 0.05 |
| summary_pass_score | 4 |

---

## SQLite Tables

```sql
-- runs
run_id, prompt_version, model, timestamp, pass_rate, metadata_json

-- case_results
run_id, case_id, actual_json, category_match, summary_score,
       latency_ms, tokens_in, tokens_out, passed

-- drift tracked via queries on runs.pass_rate
```

---

## Env Vars

| Var | Required | Purpose |
|-----|----------|---------|
| OPENAI_API_KEY | yes | LLM calls |
| SLACK_WEBHOOK_URL | CI only | Alerts |
| THRESHOLD_WARN | no | Override 3% |
| THRESHOLD_CRITICAL | no | Override 8% |
| EVAL_DB_PATH | no | Default `data/eval.db` |
