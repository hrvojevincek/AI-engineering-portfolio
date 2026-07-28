# AI Portfolio Projects

Monorepo for interview/portfolio AI engineering projects. Each project lives in its own folder with independent code, docs, and dependencies.

## Projects

| # | Folder | Status | Description |
|---|--------|--------|-------------|
| 1 | [`project-1-model-regression/`](project-1-model-regression/) | **Complete** (Phases 1–5) | CI/CD pipeline that tests LLM prompt changes against a golden dataset and blocks regressions |
| 2 | [`project-2-llm-cost-autopilot/`](project-2-llm-cost-autopilot/) | Complete (Phases 1–5) | Routes each request to the cheapest capable model; async quality verify + escalation |
| 3 | [`project-3-failure-forensics/`](project-3-failure-forensics/) | Scaffolded (Phase 0) | Trace multi-step AI pipelines, root-cause bad outputs, feed failures into evals |
| 7 | [`project-7-semantic-cache/`](project-7-semantic-cache/) | Scaffolded (Phase 0) | Drop-in LLM API proxy with semantic cache — cut cost and latency |

## Working on a project

```bash
cd project-1-model-regression
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

See each project's `README.md` for full setup and `STATUS.md` for build progress.

## Repo layout

```
.github/workflows/          CI (paths scoped per project)
project-1-model-regression/
project-2-llm-cost-autopilot/
project-3-failure-forensics/
project-7-semantic-cache/
```

## Adding a new project

1. Create `project-N-short-name/` at repo root
2. Add `README.md`, `STATUS.md`, and project code
3. Add a workflow under `.github/workflows/` with path filters scoped to that folder
4. Update the table above
