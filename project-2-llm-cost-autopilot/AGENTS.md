# Agent Guide — LLM Cost Autopilot

> **Project path:** `project-2-llm-cost-autopilot/` — run all commands from this directory.

## On Every Session

1. Read `STATUS.md` — current phase, next task, blockers.
2. Read only the **relevant phase section** in `docs/BUILD_GUIDE.md`.
3. Read `docs/SCHEMA.md` if touching models, routing config, or request logs.
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

- Python 3.12+ via **uv**: `uv venv` then `uv pip install -r requirements.txt` (never bare `pip` on macOS Homebrew)
- Model registry + pricing in code/config (real numbers)
- Routing map = versioned YAML in `/config`
- Classifier training data = hand-labeled JSON in `/data/prompts`
- Request audit trail in SQLite (`/data/requests.db`)
- Env vars: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` (Ollama optional / local)

## Target Layout (create as needed)

```
config/                 # routing YAML
data/prompts/           # labeled complexity dataset
data/requests.db        # audit trail (gitignored)
src/
  models/               # ModelConfig, Response, registry
  providers/            # OpenAI / Anthropic / Ollama adapters
  router/               # classifier + tier → model map
  verify/               # async quality check + escalation
  api/                  # FastAPI app
  dashboard/            # Streamlit (or Grafana later)
scripts/                # baseline smoke tests, train classifier
Dockerfile
docker-compose.yml
```
