# Project Status — Project 1: Model Regression Detection

> **Location:** `project-1-model-regression/`  
> **Agent:** Read this file first for "where are we?" questions. Update after every completed task.

## Snapshot

| Field            | Value                                                |
| ---------------- | ---------------------------------------------------- |
| **Phase**        | 5 — Complete ✓                                       |
| **Next task**    | Phase 4.2–4.3 (Slack + drift) or Phase 6 (portfolio) |
| **Blockers**     | Add `OPENAI_API_KEY` to GitHub repo secrets for CI   |
| **Last updated** | 2026-07-07                                           |

## Phase Checklist

### Phase 1 — LLM Feature (Day 1–2)

- [x] 1.1 `classify_email()` with configurable prompt
- [x] 1.2 Versioned prompts in `/prompts/*.yaml`
- [x] 1.3 `PromptConfig` + Pydantic output models

### Phase 2 — Golden Dataset (Day 2–4)

- [x] 2.1 50–100 hand-labeled test cases (60 cases)
- [x] 2.2 Edge cases + `expected_difficulty` field
- [x] 2.3 Versioned JSON in `/data/golden/`

### Phase 3 — Eval Engine (Day 4–7)

- [x] 3.1 Async test runner
- [x] 3.2 Multi-dim scoring (category, summary, latency, tokens)
- [x] 3.3 Run-to-run diff (regressions + improvements)
- [x] 3.4 Threshold alerts (warn 3%, critical 8%)
- [x] 3.5 SQLite run history

### Phase 4 — Alerts & Reports (Day 7–9)

- [x] 4.1 HTML diff report (built for Phase 5 CI)
- [ ] 4.2 Slack webhook alerts
- [ ] 4.3 7-run moving-average drift detection

### Phase 5 — CI/CD (Day 9–11)

- [x] 5.1 GitHub Action on `/prompts` changes
- [x] 5.2 Dockerfile
- [x] 5.3 Internal-style README

### Phase 6 — Portfolio (Day 11–12)

- [ ] 6.1 Loom walkthrough
- [ ] 6.2 Blog / design-decisions section

## Files Present

```
.github/workflows/eval.yml
Dockerfile
README.md
scripts/detect_prompt_version.py
src/report/html.py
src/report/pr_comment.py
```

## Decisions Log

| Date       | Decision                              | Rationale                                                 |
| ---------- | ------------------------------------- | --------------------------------------------------------- |
| 2026-07-07 | Baseline via GHA cache `eval-db-main` | PR diffs against last main eval without committing SQLite |
| 2026-07-07 | HTML report in Phase 5                | CI requires report artifact + PR comment                  |

## Session Notes

Phase 5 complete. Set `OPENAI_API_KEY` secret, push to GitHub, edit a prompt in a PR to trigger CI.
