# Schema — Failure Forensics Tool

Draft contracts. Refine in Phase 1–2 as we implement.

## Pipeline I/O (Pydantic — Phase 1)

| Step           | Input                   | Output (sketch)                           |
| -------------- | ----------------------- | ----------------------------------------- |
| Intake         | raw text / path         | `Document` (id, text, metadata)           |
| Extraction     | `Document`              | `Entities` (names, dates, amounts, terms) |
| Classification | `Document` + `Entities` | `DocType` + confidence                    |
| Summarization  | all prior               | `Summary` (structured by type)            |

## Trace / Span (Phase 2)

```text
Trace
  trace_id: str
  status: success | failure | degraded
  spans: list[Span]
  final_output: ...
  created_at: datetime

Span
  name: str                 # intake | extraction | classification | summarization
  input: JSON
  output: JSON
  prompt: str | null
  raw_response: str | null
  confidence: int | null    # 1–5
  tokens_in / tokens_out
  latency_ms
  error: str | null
```

## SQLite index (Phase 2)

`traces(trace_id PK, timestamp, status, final_score, path_to_json)`

## Failure diagnosis (Phase 3)

```text
Diagnosis
  root_span: str
  category: hallucination | misclassification | propagation | prompt_failure | context_loss
  evidence: list[{step, input, output, note}]
  explanation: str
```

## Eval case (Phase 5)

```text
EvalCase
  id, source_trace_id
  input_document
  failing_step
  bad_output
  corrected_output
  category
  created_at
```
