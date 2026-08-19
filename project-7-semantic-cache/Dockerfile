FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY scripts ./scripts

EXPOSE 8080

CMD ["uvicorn", "src.proxy.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8080"]
