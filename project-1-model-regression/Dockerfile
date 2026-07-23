FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY prompts/ prompts/
COPY data/golden/ data/golden/
COPY src/ src/
COPY scripts/ scripts/

ENV PYTHONUNBUFFERED=1
ENV EVAL_DB_PATH=/app/data/eval.db

# OPENAI_API_KEY          — required
# SLACK_WEBHOOK_URL       — optional (Phase 4)
# THRESHOLD_WARN          — default 0.03
# THRESHOLD_CRITICAL      — default 0.08

ENTRYPOINT ["python", "-m", "src.eval.runner"]
CMD ["--prompt", "1.0.0", "--report-dir", "reports", "--write-pr-comment"]
