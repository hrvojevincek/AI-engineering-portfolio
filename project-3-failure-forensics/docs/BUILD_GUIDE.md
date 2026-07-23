# Build Guide — Failure Forensics Tool

Condensed from the PDF (pages 12–17). Actionable phase checklist.

---

## Phase 1 — Multi-Step Pipeline (Day 1–3)

**Goal:** A clean 4-step document pipeline with typed I/O so tracing has something meaningful to attach to.

### Steps

1. **Intake** — accept raw document text (md / simulated PDF text).
2. **Extraction** — LLM extracts entities (names, dates, amounts, key terms).
3. **Classification** — document type: contract | invoice | report | correspondence.
4. **Summarization** — structured summary tailored to the classified type.

Each step = isolated function + Pydantic input/output. No spaghetti between steps.

Add fixture docs that *will* fail: contract with no dates, multi-currency invoice, ambiguous category.

**Interview point:** Tracing is useless if steps aren’t clean boundaries.

**Done when:** You can run a happy-path doc end-to-end and at least 3 known-bad fixtures produce visible bad outputs.

---

## Phase 2 — Tracing Layer (Day 3–6)

**Goal:** Every run is a `Trace` of `Span`s you can inspect later.

1. `Trace`: `trace_id`, list of spans, final output, status (`success` | `failure` | `degraded`).
2. Wrap each step in a decorator/context manager capturing: name, input, output, prompt, raw LLM response, tokens, latency, errors.
3. Ask the model for a confidence score 1–5 per step; store on the span.
4. Persist full JSON + SQLite index (`trace_id`, timestamp, status, final_score).

**Interview point:** Confidence on spans is the first filter when walking backward from a failure.

**Done when:** Running the pipeline writes a JSON trace you can open by hand, indexed in SQLite.

---

## Phase 3 — Backward Trace Analyzer (Day 6–9)

**Goal:** Flagged bad output → root cause span + failure category + evidence.

1. Walk spans **backward**. LLM-as-judge: is this output a reasonable transform of its input? First big quality drop = root cause.
2. Taxonomy: Extraction Hallucination | Misclassification | Propagation Error | Prompt Failure | Context Loss.
3. Evidence chain: prose diagnosis + the specific I/O pairs.

**Interview point:** Root cause ≠ last failing step; propagation errors are common.

**Done when:** Flagging a known failure returns the correct step + category most of the time.

---

## Phase 4 — Visual Trace Explorer (Day 9–11)

**Goal:** Humans can see and flag bad runs without reading JSON.

1. Pipeline as nodes: green / yellow (low confidence) / red (root cause). Click → span details.
2. Diff view for failures: received vs produced vs expected.
3. “Bad output” button → run analyzer → confirm or override diagnosis.

**Done when:** You can demo open-trace → flag → see diagnosis without leaving the UI.

---

## Phase 5 — Feedback-to-Eval Loop (Day 11–13)

**Goal:** Confirmed flags become regression tests.

1. On confirm: append eval case (input, failing step, bad output, corrected output, category).
2. Periodically re-run the eval set; track fixed vs still-failing.
3. Analytics: top failure types, hottest step, rate over time, time-to-root-cause.

**Interview point:** This is the observability → quality flywheel interviewers love.

**Done when:** Flagging grows `data/eval/`; a script re-runs and reports pass/fail trend.

---

## Phase 6 — Portfolio (Day 13–14)

1. 50 docs through the pipeline; ≥8–10 diverse failures. Loom: bad output → explorer → diagnose → flag → eval grows.
2. Case study: lead with “we can pinpoint which step failed in X% of flagged runs” (or similar measurable claim).
