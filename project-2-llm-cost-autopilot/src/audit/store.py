"""Insert / query helpers for the requests audit table."""

from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timezone

from src.audit.db import get_conn


def prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]


def log_request(
    conn: sqlite3.Connection,
    *,
    prompt: str,
    complexity_tier: int,
    routed_model: str,
    final_model: str,
    cost: float,
    latency_ms: float,
    quality_score: float | None,
    escalated: bool,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    timestamp: str | None = None,
) -> int:
    """Insert one audit row. Returns new row id."""
    ts = timestamp or datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        """
        INSERT INTO requests (
            timestamp, prompt_hash, complexity_tier, routed_model, final_model,
            cost, latency_ms, quality_score, escalated, input_tokens, output_tokens
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ts,
            prompt_hash(prompt),
            complexity_tier,
            routed_model,
            final_model,
            cost,
            latency_ms,
            quality_score,
            int(escalated),
            input_tokens,
            output_tokens,
        ),
    )
    conn.commit()
    return int(cur.lastrowid)


def fetch_recent(conn: sqlite3.Connection, limit: int = 20) -> list[sqlite3.Row]:
    cur = conn.execute(
        "SELECT * FROM requests ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    return list(cur.fetchall())


def fetch_all(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return list(conn.execute("SELECT * FROM requests ORDER BY id ASC"))


if __name__ == "__main__":
    with get_conn() as conn:
        version = int(conn.execute("PRAGMA user_version").fetchone()[0])
        row_id = log_request(
            conn,
            prompt="smoke test prompt",
            complexity_tier=1,
            routed_model="gpt-4o-mini",
            final_model="gpt-4o-mini",
            cost=0.00001,
            latency_ms=12.3,
            quality_score=1.0,
            escalated=False,
            input_tokens=10,
            output_tokens=5,
        )
        rows = fetch_recent(conn, limit=1)
        print(f"user_version={version}")
        print(f"inserted id={row_id}")
        print(dict(rows[0]))
