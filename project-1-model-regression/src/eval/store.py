import json
import os
import sqlite3
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from src.models import CaseResult, EvalRun

DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "eval.db"


def get_db_path() -> Path:
    return Path(os.getenv("EVAL_DB_PATH", str(DEFAULT_DB_PATH)))


def _connect(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = db_path or get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[Path] = None) -> None:
    conn = _connect(db_path)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            prompt_version TEXT NOT NULL,
            model TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            pass_rate REAL NOT NULL,
            avg_latency_ms REAL NOT NULL,
            total_tokens INTEGER NOT NULL,
            category_accuracy_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS case_results (
            run_id TEXT NOT NULL,
            case_id TEXT NOT NULL,
            actual_json TEXT NOT NULL,
            category_match INTEGER NOT NULL,
            summary_score INTEGER NOT NULL,
            latency_ms REAL NOT NULL,
            tokens_in INTEGER NOT NULL,
            tokens_out INTEGER NOT NULL,
            passed INTEGER NOT NULL,
            PRIMARY KEY (run_id, case_id),
            FOREIGN KEY (run_id) REFERENCES runs(run_id)
        );
        """
    )
    conn.commit()
    conn.close()


def save_run(run: EvalRun, db_path: Optional[Path] = None) -> None:
    init_db(db_path)
    conn = _connect(db_path)

    conn.execute(
        """
        INSERT INTO runs (
            run_id, prompt_version, model, timestamp,
            pass_rate, avg_latency_ms, total_tokens, category_accuracy_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(run.run_id),
            run.prompt_version,
            run.model,
            run.timestamp.isoformat(),
            run.pass_rate,
            run.avg_latency_ms,
            run.total_tokens,
            json.dumps(run.category_accuracy),
        ),
    )

    for case in run.case_results:
        conn.execute(
            """
            INSERT INTO case_results (
                run_id, case_id, actual_json, category_match, summary_score,
                latency_ms, tokens_in, tokens_out, passed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(run.run_id),
                case.case_id,
                case.actual.model_dump_json(),
                int(case.category_match),
                case.summary_score,
                case.latency_ms,
                case.tokens_in,
                case.tokens_out,
                int(case.passed),
            ),
        )

    conn.commit()
    conn.close()


def _row_to_case_result(row: sqlite3.Row) -> CaseResult:
    from src.models import ClassificationResult

    return CaseResult(
        case_id=row["case_id"],
        actual=ClassificationResult.model_validate_json(row["actual_json"]),
        category_match=bool(row["category_match"]),
        summary_score=row["summary_score"],
        latency_ms=row["latency_ms"],
        tokens_in=row["tokens_in"],
        tokens_out=row["tokens_out"],
        passed=bool(row["passed"]),
    )


def load_run(run_id: UUID, db_path: Optional[Path] = None) -> EvalRun:
    from datetime import datetime

    conn = _connect(db_path)
    row = conn.execute(
        "SELECT * FROM runs WHERE run_id = ?", (str(run_id),)
    ).fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Run not found: {run_id}")

    case_rows = conn.execute(
        "SELECT * FROM case_results WHERE run_id = ? ORDER BY case_id",
        (str(run_id),),
    ).fetchall()
    conn.close()

    return EvalRun(
        run_id=UUID(row["run_id"]),
        prompt_version=row["prompt_version"],
        model=row["model"],
        timestamp=datetime.fromisoformat(row["timestamp"]),
        case_results=[_row_to_case_result(r) for r in case_rows],
        pass_rate=row["pass_rate"],
        category_accuracy=json.loads(row["category_accuracy_json"]),
        avg_latency_ms=row["avg_latency_ms"],
        total_tokens=row["total_tokens"],
    )


def get_previous_run(
    before_run_id: UUID, db_path: Optional[Path] = None
) -> Optional[EvalRun]:
    conn = _connect(db_path)
    row = conn.execute(
        """
        SELECT run_id FROM runs
        WHERE timestamp < (SELECT timestamp FROM runs WHERE run_id = ?)
        ORDER BY timestamp DESC
        LIMIT 1
        """,
        (str(before_run_id),),
    ).fetchone()
    conn.close()

    if not row:
        return None
    return load_run(UUID(row["run_id"]), db_path)


def get_latest_run(db_path: Optional[Path] = None) -> Optional[EvalRun]:
    conn = _connect(db_path)
    row = conn.execute(
        "SELECT run_id FROM runs ORDER BY timestamp DESC LIMIT 1"
    ).fetchone()
    conn.close()

    if not row:
        return None
    return load_run(UUID(row["run_id"]), db_path)


def get_recent_run_summaries(
    n: int = 10, db_path: Optional[Path] = None
) -> List[dict]:
    """Lightweight history for trend charts (no case results loaded)."""
    from datetime import datetime

    conn = _connect(db_path)
    rows = conn.execute(
        """
        SELECT run_id, prompt_version, model, timestamp, pass_rate
        FROM runs ORDER BY timestamp DESC LIMIT ?
        """,
        (n,),
    ).fetchall()
    conn.close()

    summaries = []
    for row in reversed(rows):
        summaries.append(
            {
                "run_id": row["run_id"],
                "prompt_version": row["prompt_version"],
                "model": row["model"],
                "timestamp": datetime.fromisoformat(row["timestamp"]),
                "pass_rate": row["pass_rate"],
            }
        )
    return summaries
