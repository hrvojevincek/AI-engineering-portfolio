# Portfolio Agent Guide

Monorepo containing multiple AI portfolio projects. Each project is self-contained in its own folder.

Projects are built from `AI Engineering Projects Guide.pdf` (15 project blueprints). A distilled summary lives at `docs/projects-guide.md` — read that instead of the PDF. Only read the PDF (in chunks, using the page ranges listed in the summary) when full phase-by-phase detail for a specific project is needed.

## On Every Session

1. Identify which **project-N-** folder the user is working on
2. Read that project's `STATUS.md` first for progress
3. Read that project's `AGENTS.md` and `docs/` as needed
4. **Do not** assume cwd is repo root — cd into the project folder for commands

## Project Index

| Folder                           | Read first                                |
| -------------------------------- | ----------------------------------------- |
| `project-1-model-regression/`    | `project-1-model-regression/STATUS.md`    |
| `project-2-llm-cost-autopilot/`  | `project-2-llm-cost-autopilot/STATUS.md`  |
| `project-3-failure-forensics/`   | `project-3-failure-forensics/STATUS.md`   |

## Token-Saving Rules

| User asks…      | Read only…             |
| --------------- | ---------------------- |
| "Where are we?" | `{project}/STATUS.md`  |
| Which project?  | Root `README.md` table |

## Agent mode

Default is **learning coach** (see `.cursor/rules/learning-coach.mdc`): step-by-step guidance, no full solutions. Say `just implement` / `write the code` to temporarily opt out.

## Conventions

- Each project has its own `requirements.txt`, venv, README, STATUS
- CI workflows live at `.github/workflows/` with path filters per project
- New projects: `project-N-short-name/` following the same doc pattern
