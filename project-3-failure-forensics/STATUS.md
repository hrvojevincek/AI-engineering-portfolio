# Project Status — Project 3: Failure Forensics Tool

> **Location:** `project-3-failure-forensics/`  
> **Agent:** Read this file first for "where are we?" questions. Update after every completed task.

## Snapshot

| Field            | Value                |
| ---------------- | -------------------- |
| **Phase**        | 0 — Scaffold         |
| **Next task**    | Phase 1.1 — Design 4-step document pipeline |
| **Blockers**     | None                 |
| **Last updated** | 2026-07-23           |

## Phase Checklist

### Phase 1 — Multi-Step Pipeline (Day 1–3)

- [ ] 1.1 Four steps: Intake → Extraction → Classification → Summarization
- [ ] 1.2 Typed Pydantic I/O per step (isolated functions)
- [ ] 1.3 Fixture docs that trigger realistic failures

### Phase 2 — Tracing Layer (Day 3–6)

- [ ] 2.1 `Trace` + `Span` models (`trace_id`, status, final output)
- [ ] 2.2 Span decorator/context manager (I/O, prompt, tokens, latency, errors)
- [ ] 2.3 Per-step confidence score (1–5)
- [ ] 2.4 JSON traces + SQLite index

### Phase 3 — Backward Trace Analyzer (Day 6–9)

- [ ] 3.1 Walk spans backward; LLM-as-judge quality drop = root cause
- [ ] 3.2 Failure taxonomy (hallucination, misclass, propagation, prompt, context loss)
- [ ] 3.3 Evidence chain (structured diagnosis + I/O pairs)

### Phase 4 — Visual Trace Explorer (Day 9–11)

- [ ] 4.1 Trace view (nodes color-coded by health / confidence / root cause)
- [ ] 4.2 Diff view (received vs produced vs expected)
- [ ] 4.3 Flag “bad output” → run analyzer → confirm/override

### Phase 5 — Feedback-to-Eval Loop (Day 11–13)

- [ ] 5.1 Flag + confirm → append eval case
- [ ] 5.2 Regression re-runs of accumulated eval set
- [ ] 5.3 Failure analytics dashboard

### Phase 6 — Portfolio (Day 13–14)

- [ ] 6.1 Demo: 50 docs, 8–10 diverse failures, Loom walkthrough
- [ ] 6.2 Case-study writeup

## Files Present

```
STATUS.md
AGENTS.md
README.md
docs/BUILD_GUIDE.md
docs/ARCHITECTURE.md
docs/SCHEMA.md
requirements.txt
.env.example
```

## Decisions Log

| Date       | Decision                               | Rationale                                      |
| ---------- | -------------------------------------- | ---------------------------------------------- |
| 2026-07-23 | Folder = `project-3-failure-forensics` | Matches monorepo naming + guide #3             |

## Session Notes

Scaffold only. Start Phase 1.1 next.
