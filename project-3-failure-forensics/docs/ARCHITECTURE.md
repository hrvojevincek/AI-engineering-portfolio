# Architecture — Failure Forensics Tool

```
Document ──► Pipeline (4 steps) ──► Final output
                 │
                 ▼
            Trace + Spans (JSON + SQLite)
                 │
        flag bad output
                 ▼
         Backward analyzer ──► root cause + taxonomy
                 │
                 ▼
            Eval dataset ──► regression re-runs
```

## Core idea

Instrument a real multi-step LLM pipeline so failures are **localizable** (which span broke?) and **reusable** (confirmed failures become eval cases).

## Components (V1)

| Piece | Role |
|-------|------|
| `pipeline/` | Intake → Extract → Classify → Summarize |
| `tracing/` | Span decorator, Trace store |
| `analyze/` | Backward RCA + failure taxonomy |
| `api/` + `ui/` | Run pipeline, explore traces, flag |
| `data/eval/` | Growing golden set from human confirmations |
