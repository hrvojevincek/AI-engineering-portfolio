# Demo Recording Runbook (< 4 min)

Use this script when recording the Phase 6 portfolio demo.

## Prep (before hitting record)

```bash
cd project-7-semantic-cache
docker compose up --build -d
# wait ~30s for proxy + Grafana
open http://localhost:3000/d/semantic-cache-overview  # login: admin/admin
```

Split screen: terminal (left) + Grafana dashboard (right).

## Recording script (~3 min)

| Time | Action                                   | What to say                                                               |
| ---- | ---------------------------------------- | ------------------------------------------------------------------------- |
| 0:00 | Show architecture / README headline      | "Drop-in proxy — change base URL, save on LLM spend."                     |
| 0:30 | Run 3-step demo                          | `python scripts/demo.py --url http://localhost:8080`                      |
| 1:00 | Point at MISS → HIT → semantic HIT       | "First call hits OpenAI. Repeat is instant. Paraphrase still hits cache." |
| 1:30 | Point at Grafana Hit Rate + Tokens Saved | "Metrics update live — no custom instrumentation in the app."             |
| 2:00 | Run load test                            | `python scripts/demo.py --load-test --requests 2000`                      |
| 2:45 | Grafana panels climbing                  | "After 2k requests: ~68% hit rate, tokens saved counter rising."          |
| 3:00 | Case study headline                      | See `docs/CASE_STUDY.md`                                                  |

## Commands

```bash
# Step 1–3 only (miss → hit → semantic hit)
python scripts/demo.py

# Full demo + load test for Grafana
python scripts/demo.py --load-test --requests 2000 --concurrency 20
```

## Troubleshooting

| Issue              | Fix                                                               |
| ------------------ | ----------------------------------------------------------------- |
| Connection refused | `docker compose ps` — ensure proxy is up on :8080                 |
| All MISS           | Stack must run with `CACHE_DEMO_MODE=true` (default in compose)   |
| Empty Grafana      | Wait 10s after requests; check Prometheus target at :9090/targets |
