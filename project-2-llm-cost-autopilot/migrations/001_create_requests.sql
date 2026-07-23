-- migration 001: initial requests audit table
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    prompt_hash TEXT NOT NULL,
    complexity_tier INTEGER NOT NULL,
    routed_model TEXT NOT NULL,
    final_model TEXT NOT NULL,
    cost REAL NOT NULL,
    latency_ms REAL NOT NULL,
    quality_score REAL,
    escalated INTEGER NOT NULL DEFAULT 0
);
