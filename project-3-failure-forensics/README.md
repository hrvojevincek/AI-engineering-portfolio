# Failure Forensics Tool

> **Project 3** in the AI portfolio monorepo. See root `README.md` for other projects.

Observability for multi-step AI pipelines: trace every step → when output is bad, find the root-cause span → feed confirmed failures into a growing eval dataset.

## Quick start

```bash
cd project-3-failure-forensics
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
cp .env.example .env   # OPENAI_API_KEY
```

Phase 1+ commands will land here as we build.

## Headline story

**“Where did this go wrong?”** — mini LangSmith/Braintrust for a 4-step document pipeline, with a failure → eval flywheel.

## Layout (target)

```
data/documents/     Sample + failure-mode docs
data/traces/        JSON traces
data/eval/          Eval cases from human flags
src/pipeline/       Intake → Extract → Classify → Summarize
src/tracing/        Trace/Span + instrumentation
src/analyze/        Backward root-cause analysis
src/api/            Run / flag / eval API
src/ui/             Trace explorer
```

## Status

See [`STATUS.md`](STATUS.md). Currently **Phase 0 — scaffold**.
