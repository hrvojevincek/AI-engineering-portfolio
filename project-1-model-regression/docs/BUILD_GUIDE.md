# Build Guide

Condensed phase guide. Full spec lives in project brief; this is the actionable version.

---

## Phase 1 — LLM Feature (Day 1–2)

**Goal:** One testable function + versioned prompts + typed contract.

### 1.1 Email classifier

```python
async def classify_email(email: str, config: PromptConfig) -> ClassificationResult
```

- Input: raw email text
- Output: `{ category, summary }` — categories: `billing | technical | account | general`
- Prompt is **not** hardcoded; comes from `PromptConfig`

### 1.2 Versioned prompts

File: `prompts/v{semver}.yaml`

```yaml
version: "1.0.0"
created_at: "2026-07-07T00:00:00Z"
model: "gpt-4o-mini"
system_prompt: "..."
few_shot_examples:
  - input: "..."
    output: { category: "...", summary: "..." }
```

### 1.3 Interface contract

- `PromptConfig` — dataclass loaded from YAML
- `ClassificationResult` — Pydantic model
- `EmailCategory` — enum

**Interview point:** Prompts are versioned like code; CI runs against prompt diffs.

**Done when:** `python -m src.feature.classifier` classifies one email using `prompts/v1.0.0.yaml`.

---

## Phase 2 — Golden Dataset (Day 2–4)

**Goal:** Human-verified ground truth. Quality of eval = quality of this data.

### Requirements

- 50–100 cases, **hand-written** (not LLM-generated labels)
- Fields per case: `id`, `input`, `expected` (category + summary), `expected_difficulty`, `notes`
- Dataset file versioned: `data/golden/v1.0.0.json`

### Edge cases to include

| Type | Why |
|------|-----|
| Ambiguous (2 valid categories) | Tests classifier confidence |
| Very short ("refund?") | Tests minimal context |
| Typos / slang | Tests robustness |
| Mixed language | Tests locale handling |
| Sarcasm | Tests tone misread |

**Interview point:** Lead with how you built + expanded the golden set from production failures.

**Done when:** JSON validates against schema; ≥50 cases across all 4 categories.

---

## Phase 3 — Eval Engine (Day 4–7)

**Goal:** Run all cases, score multi-dimensionally, diff vs previous run.

### 3.1 Test runner

```python
async def run_eval(config: PromptConfig, dataset: GoldenDataset) -> EvalRun
```

- Async batching (semaphore ~10 concurrent)
- Persist raw outputs per case

### 3.2 Scoring dimensions

| Dimension | Method | Pass threshold |
|-----------|--------|----------------|
| Category | Exact match | binary |
| Summary | LLM-as-judge 1–5 | ≥4 |
| Latency | Wall clock ms | informational |
| Tokens | `usage` from API | informational |

### 3.3 Comparison

vs previous run (baseline = last passing run or explicit tag):

- Overall pass rate delta
- Per-category accuracy delta
- `regressions[]` — pass→fail
- `improvements[]` — fail→pass

### 3.4 Thresholds (configurable)

- **warn:** pass rate drops >3%
- **critical:** pass rate drops >8% → block CI

### 3.5 Storage

SQLite tables: `runs`, `case_results`, `scores`

**Done when:** `python -m src.eval.runner --prompt v1.0.0` produces run + diff vs baseline.

---

## Phase 4 — Alerts & Reports (Day 7–9)

### 4.1 HTML report

Sections: metadata, scorecard (this vs baseline), regression table (old vs new side-by-side), trend chart (last N runs).

Output: `reports/{run_id}.html`

### 4.2 Slack

Webhook payload: status emoji, headline ("3 regressions, 94%→89%"), link to report.

### 4.3 Drift detection

7-run moving average of pass rate. Alert if MA drops below threshold even when single-run delta is small.

**Done when:** Eval run → HTML file + Slack message (mock webhook OK locally).

---

## Phase 5 — CI/CD (Day 9–11)

### GitHub Action

- Trigger: PR changing `prompts/**`
- Steps: run eval → generate report → PR comment → fail job on critical
- Secrets: `OPENAI_API_KEY`, `SLACK_WEBHOOK_URL`

### Docker

```dockerfile
# Env: OPENAI_API_KEY, SLACK_WEBHOOK_URL, THRESHOLD_WARN, THRESHOLD_CRITICAL
CMD ["python", "-m", "src.eval.runner"]
```

### README

Internal-docs tone: what it does, setup, add test cases, adjust thresholds, architecture rationale.

**Done when:** PR that edits a prompt triggers CI and posts comment.

---

## Phase 6 — Portfolio (Day 11–12)

- 3-min Loom: change prompt → eval → Slack → diff report
- Blog section: problem (blind prompt shipping) → solution (CI for model behavior) → proud decision (e.g. slow drift vs per-run)

---

## Suggested Build Order (first session)

1. `src/models/` — Pydantic types
2. `prompts/v1.0.0.yaml` — first prompt
3. `src/feature/classifier.py` — core function
4. `data/golden/v1.0.0.json` — start with 10 cases, expand to 50+
5. `src/eval/runner.py` — category-only scoring first, then add judge + diff
