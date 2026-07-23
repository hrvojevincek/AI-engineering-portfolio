# Model Regression Detection System

> **Project 1** in the AI portfolio monorepo. See root `README.md` for other projects.

Runs automated quality checks on our email classifier whenever prompts change.

## Quick start

```bash
cd project-1-model-regression   # from repo root
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add OPENAI_API_KEY

python -m src.eval.runner --prompt 1.0.0 --report-dir reports --write-pr-comment
```

## What gets tested

| Component      | Location                    | Purpose                               |
| -------------- | --------------------------- | ------------------------------------- |
| LLM feature    | `src/feature/classifier.py` | Email → category + summary            |
| Prompts        | `prompts/v*.yaml`           | Versioned system prompts (CI trigger) |
| Golden dataset | `data/golden/v*.json`       | Human-labeled ground truth (60 cases) |
| Eval engine    | `src/eval/`                 | Runner, scoring, diff, SQLite history |
| Reports        | `src/report/`               | HTML diff + PR comment markdown       |

## CI/CD

Workflow: `.github/workflows/eval.yml`

- **Triggers:** PR or push to `main` that modifies `project-1-model-regression/prompts/**`
- **Baseline:** Restores `data/eval.db` cache from `main` branch
- **On PR:** Runs eval → posts comment → fails check if severity is `critical`
- **On main:** Runs eval → updates baseline cache for future PRs

### Required secret

| Secret           | Where                                      |
| ---------------- | ------------------------------------------ |
| `OPENAI_API_KEY` | GitHub repo → Settings → Secrets → Actions |

### Severity thresholds

| Level      | Condition           | CI behavior                   |
| ---------- | ------------------- | ----------------------------- |
| `pass`     | Pass rate drop ≤ 3% | Green, comment posted         |
| `warn`     | Drop > 3%           | Green with warning in comment |
| `critical` | Drop > 8%           | **Red, merge blocked**        |

Override via env vars: `THRESHOLD_WARN`, `THRESHOLD_CRITICAL`, `SUMMARY_PASS_SCORE`.

## Adding golden test cases

1. Edit `data/golden/v1.0.0.json`
2. Add a case with stable `id`, realistic `input`, hand-written `expected`, and `expected_difficulty`
3. Do **not** LLM-generate labels — quality ceiling = label quality
4. Bump dataset version (`v1.1.0.json`) when the eval bar materially changes

```json
{
  "id": "billing-015",
  "input": "customer email text",
  "expected": { "category": "billing", "summary": "One sentence." },
  "expected_difficulty": "medium",
  "notes": "Why this case matters"
}
```

## Changing prompts

1. Create `prompts/v1.1.0.yaml` (copy from previous version, edit)
2. Open a PR — CI auto-detects the changed version and runs eval
3. Review the PR comment and download the `eval-report` artifact for the full HTML diff

## Docker

```bash
docker build -t model-eval .
docker run --rm \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/reports:/app/reports \
  model-eval --prompt 1.0.0
```

## Architecture decisions

**Prompts as YAML in git** — Diffs are reviewable in PRs; CI triggers only on prompt changes, not code refactors.

**Hand-labeled golden set** — Eval quality is bounded by label quality. We seed with 60 cases and expand from production failures over time.

**LLM-as-judge for summaries** — Category accuracy alone misses semantic regressions (right bucket, wrong summary).

**Previous-run diffing** — Each eval compares to the last run in SQLite. On PRs, that's typically the last `main` branch eval (via cache restore).

**SQLite over Postgres** — Zero infrastructure; portable; sufficient for eval history and trend charts.

**Async batching (10 concurrent)** — Balances speed and API rate limits for ~120 calls per full eval (60 classify + 60 judge).

## Project layout

```
prompts/              Versioned prompt configs
data/golden/          Hand-labeled test cases
data/eval.db          Run history (gitignored, cached in CI)
src/feature/          LLM classifier under test
src/eval/             Runner, scorer, diff, store
src/report/           HTML + PR comment formatters
reports/              Generated eval reports (gitignored)
.github/workflows/    CI pipeline
```

## Local commands

```bash
# Validate golden dataset
python -m src.eval.dataset

# Classify one email (smoke test)
python -m src.feature.classifier

# Full eval with report
python -m src.eval.runner --prompt 1.0.0 --report-dir reports --write-pr-comment

# Cheaper eval (category only, no summary judge)
python -m src.eval.runner --prompt 1.0.0 --skip-judge
```
