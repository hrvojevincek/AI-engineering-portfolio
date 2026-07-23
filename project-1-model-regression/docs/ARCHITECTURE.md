# Architecture

## System Flow

```
prompts/*.yaml ──┐
                 ├──► Eval Runner ──► SQLite (history)
golden/*.json ───┘         │
                           ├──► Diff Engine ──► severity (pass/warn/critical)
                           │         │
                           │         ├──► HTML Report
                           │         └──► Slack Webhook
                           │
                     GitHub Action (PR gate)
```

## Components

| Module | Responsibility |
|--------|----------------|
| `src/feature/classifier.py` | LLM call + parse structured output |
| `src/feature/prompts.py` | Load/version YAML prompts |
| `src/eval/runner.py` | Orchestrate batch eval |
| `src/eval/scorer.py` | Category match + LLM judge |
| `src/eval/diff.py` | Compare runs, compute severity |
| `src/eval/drift.py` | Moving-average degradation |
| `src/eval/store.py` | SQLite read/write |
| `src/report/html.py` | Generate diff report |
| `src/report/slack.py` | Format + send webhook |
| `src/models/` | All Pydantic types |

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Prompts as YAML in git | Diffs are reviewable; CI triggers on prompt changes |
| Hand-labeled golden set | Eval quality ceiling = label quality |
| LLM-as-judge for summary | Category alone misses semantic regressions |
| Per-run diff + drift | Catches sudden breaks AND slow degradation |
| SQLite not Postgres | Zero infra; portable; good enough for eval history |
| Async batching | Cost + speed for 50–100 cases per PR |

## CI Behavior

```
PR modifies prompts/** → Action runs eval →
  critical? → fail check, block merge
  warn?     → pass check, warn in PR comment
  pass      → green, post scorecard comment
```

## Dependencies (planned)

```
openai, pydantic, pyyaml, aiohttp, jinja2, sqlite3 (stdlib)
# optional: ragas or deepeval for summary scoring
```
