# AI Engineering Projects Guide — Reference

Distilled from `AI Engineering Projects Guide.pdf` (BASWE, "15 AI Engineering Projects That Actually Land Jobs"). This monorepo builds a selection of these projects as portfolio pieces. Each project is scoped for ~12–14 days (2–3 hrs/day). The guide's advice: build 2–3 deeply rather than all 15 shallowly.

For full phase-by-phase detail on any project, read the PDF in chunks (it's ~82 pages; page ranges below).

## The 15 Projects

| # | Project | What it is | Core stack | PDF pages |
|---|---------|-----------|------------|-----------|
| 1 | **Model Regression Detection System** | CI/CD pipeline that tests LLM prompt changes against a golden dataset, detects regressions, alerts via Slack, blocks bad merges | Python, OpenAI, custom evals + LLM-as-judge, SQLite/JSON, GitHub Actions, Slack webhooks, Docker | 2–7 |
| 2 | **LLM Cost Autopilot** | Routing layer that classifies request complexity and routes to the cheapest capable model, with async quality verification and auto-escalation | FastAPI, scikit-learn classifier, OpenAI/Anthropic/Ollama, SQLite, Streamlit/Grafana | 7–12 |
| 3 | **Failure Forensics Tool** | Observability layer for multi-step AI pipelines: traces every step, backward root-cause analysis, failures feed a growing eval dataset | Custom pipeline/LangChain, OpenTelemetry spans, SQLite + JSON traces, Streamlit/React | 12–17 |
| 4 | **Self-Healing Technical Documentation** | GitHub Action that detects when code changes make docs stale and auto-generates correction PRs | Embeddings + ChromaDB, code-to-docs link graph, git diff parsing, PyGithub, GitHub Actions | 17–22 |
| 5 | **LLM Output Arbitration System** | Multi-agent pipeline: three specialized critic models (accuracy, logic, completeness) on different providers + an adjudicator that resolves disagreements into a verdict | LangGraph, OpenAI + Anthropic + Ollama, instructor/Pydantic, FastAPI | 22–27 |
| 6 | **RAG with Hybrid Search** | Production RAG: dense + BM25 sparse retrieval, RRF fusion, reranking, grounded answers with verified citations, chunking-strategy comparison | ChromaDB/Qdrant, rank_bm25, LangChain splitters, FastAPI, golden Q&A eval suite | 27–32 |
| 7 | **Semantic Caching Layer** | Drop-in proxy that detects semantically similar prompts and serves cached responses (30–60% cost cut); mirrors the OpenAI API contract | Redis + RedisVL, embeddings, FastAPI, Prometheus + Grafana | 32–37 |
| 8 | **Text-to-SQL with Guardrails** | NL-to-SQL with schema-aware prompting, DDL/DML blocking, read-only sandboxing, hallucination detection via back-translation and multi-query agreement | PostgreSQL/DuckDB, SQLAlchemy introspection, instructor, FastAPI | 37–43 |
| 9 | **Prompt Versioning & A/B Testing Platform** | Prompts as versioned artifacts; traffic splitting between variants, statistical significance testing, automated winner declaration, audit log | PostgreSQL, scipy.stats, FastAPI, React/Streamlit | 43–48 |
| 10 | **LoRA Fine-Tuning Pipeline** | End-to-end LoRA fine-tune of an open model on domain data: hyperparameter sweeps, base-vs-tuned benchmark, catastrophic-forgetting check, vLLM serving | Llama 3 8B / Mistral 7B, HF PEFT + TRL, QLoRA/Unsloth, W&B/MLflow, vLLM/Ollama | 48–53 |
| 11 | **LLM Gateway** | API gateway for all org LLM calls: per-team rate limits + budgets, provider health checks, automatic fallback routing, circuit breakers, full observability | FastAPI/Go, Redis token buckets, OpenTelemetry, Prometheus + Grafana | 53–59 |
| 12 | **AI Feature Flag System** | Feature flags for AI features: gradual staged rollout with continuous quality monitoring and automatic rollback on quality degradation | PostgreSQL + Redis, LLM-as-judge scoring, Python SDK, Slack alerts | 59–65 |
| 13 | **Eval Dataset Generator from Production Logs** | Mines production LLM logs, clusters interactions, flags edge cases, auto-labels them into a growing eval dataset with human review queue | HDBSCAN clustering, LLM auto-labeling, PostgreSQL/ClickHouse, Streamlit curation UI, nightly cron | 65–70 |
| 14 | **Multi-Modal Document Processor** | OCR + LLM extraction + validation pipeline for PDFs/scans, with confidence-based routing to a human review UI and correction feedback loops | Tesseract + EasyOCR, GPT-4o vision fallback, instructor/Pydantic, Celery + Redis | 70–76 |
| 15 | **Agent Orchestration System** | Supervisor agent decomposes tasks, delegates to tool-using specialist agents, persistent memory (short-term Redis + long-term ChromaDB), human-in-the-loop escalation, full tracing | LangGraph, MCP tools, PostgreSQL + ChromaDB, Celery, trace explorer UI | 76–82 |

## Recurring Themes (what the guide emphasizes across all projects)

- **Evaluation first**: golden datasets are hand-curated, versioned, and grow from real failure cases; LLM-as-judge complements exact-match metrics.
- **Production framing**: everything is Dockerized, exposed as an API, wired into CI/CD, and documented like internal onboarding docs — not tutorials.
- **Lead with numbers**: every portfolio narrative starts with a measurable headline ("reduced cost by X%", "Y% faithfulness").
- **Feedback loops**: failures become training/eval data (the "flywheel") in nearly every project.
- **Final phase is always polish**: a <4 min demo recording + a case-study writeup.

## Status in this repo

| Guide # | Folder | Status |
|---------|--------|--------|
| 1 | `project-1-model-regression/` | Complete (Phases 1–5) |
| 2 | `project-2-llm-cost-autopilot/` | Complete (Phases 1–5 local) |
| 3 | `project-3-failure-forensics/` | Scaffolded (Phase 0) |
| 7 | `project-7-semantic-cache/` | Scaffolded (Phase 0) |
