# Agent Guide — Model Regression Detection System

> **Project path:** `project-1-model-regression/` — run all commands from this directory.

## On Every Session

1. Read `STATUS.md` — current phase, next task, blockers.
2. Read only the **relevant phase section** in `docs/BUILD_GUIDE.md`.
3. Read `docs/SCHEMA.md` if touching data models, prompts, or eval output.
4. **Update `STATUS.md`** after completing any checklist item.

## Token-Saving Rules

| User asks…                 | Read only…                                           |
| -------------------------- | ---------------------------------------------------- |
| "Where are we?" / progress | `STATUS.md`                                          |
| "Build phase N"            | `STATUS.md` + `BUILD_GUIDE.md` Phase N + `SCHEMA.md` |
| "How does X work?"         | Grep codebase + `SCHEMA.md`; skip full build guide   |
| Architecture overview      | `docs/ARCHITECTURE.md`                               |

Do **not** re-read the full project spec from the user message. Everything is in `docs/`.

## Teaching Mode

User is **learning**, not just shipping. For each task:

1. Explain **what** we're building and **why** (1–2 sentences).
2. Implement the smallest working slice.
3. Point to the interview talking point in `BUILD_GUIDE.md` when relevant.
4. Mark `STATUS.md` checklist when done.

## Conventions

- Python 3.12+
- Prompts = versioned YAML in `/prompts`
- Golden data = hand-labeled JSON in `/data/golden` (never LLM-generated ground truth)
- Eval runs stored in SQLite (`/data/eval.db`)
- Reports in `/reports/`
- Env vars: `OPENAI_API_KEY`, `SLACK_WEBHOOK_URL`

## Target Layout (create as needed)

```
prompts/
data/golden/
data/eval.db
src/
  feature/       # classifier
  eval/          # runner, scoring, diff
  report/        # HTML, Slack
  models/        # Pydantic types
reports/
.github/workflows/
Dockerfile
```
