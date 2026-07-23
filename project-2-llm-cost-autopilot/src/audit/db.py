"""DB connection + SQL migrations (PRAGMA user_version)."""

from __future__ import annotations

import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from src.audit.paths import DEFAULT_DB, MIGRATIONS_DIR

_MIGRATION_RE = re.compile(r"^(\d+)_.*\.sql$")


def _migration_files() -> list[tuple[int, Path]]:
    files: list[tuple[int, Path]] = []
    if not MIGRATIONS_DIR.exists():
        return files
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        m = _MIGRATION_RE.match(path.name)
        if not m:
            continue
        files.append((int(m.group(1)), path))
    return files


def apply_migrations(conn: sqlite3.Connection) -> int:
    """Apply pending SQL migrations. Returns the resulting user_version."""
    current = int(conn.execute("PRAGMA user_version").fetchone()[0])
    applied_to = current
    for version, path in _migration_files():
        if version <= current:
            continue
        conn.executescript(path.read_text(encoding="utf-8"))
        conn.execute(f"PRAGMA user_version = {version}")
        conn.commit()
        applied_to = version
    return applied_to


def connect(path: Path | None = None) -> sqlite3.Connection:
    path = path or DEFAULT_DB
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    apply_migrations(conn)
    return conn


def init_db(path: Path | None = None) -> sqlite3.Connection:
    """Backward-compatible alias for connect()."""
    return connect(path)


@contextmanager
def get_conn(path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """Preferred API: with get_conn() as conn: ..."""
    conn = connect(path)
    try:
        yield conn
    finally:
        conn.close()
