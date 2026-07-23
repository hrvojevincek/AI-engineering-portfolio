# Agent Guide — Failure Forensics Tool

> **Project path:** `project-3-failure-forensics/` — run all commands from this directory.

## On Every Session

1. Read `STATUS.md` — current phase, next task, blockers.
2. Read only the **relevant phase section** in `docs/BUILD_GUIDE.md`.
3. Read `docs/SCHEMA.md` if touching Trace/Span models, storage, or eval cases.
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
- Pipeline steps = isolated functions + Pydantic I/O
- Traces = JSON files under `/data/traces/` + SQLite index
- Eval cases grown from human flags under `/data/eval/`
- Env vars: `OPENAI_API_KEY`

## Target Layout (create as needed)

```
data/
  documents/            # fixture / sample docs (incl. failure cases)
  traces/               # JSON trace files
  eval/                 # growing eval dataset from flags
  traces.db             # SQLite index (gitignored)
src/
  pipeline/             # intake, extract, classify, summarize
  models/               # Pydantic I/O + Trace/Span
  tracing/              # decorator, store
  analyze/              # backward RCA + taxonomy
  api/                  # FastAPI (run + flag + eval)
  ui/                   # Streamlit/React trace explorer
scripts/                # batch run, regression eval
Dockerfile
docker-compose.yml
```
