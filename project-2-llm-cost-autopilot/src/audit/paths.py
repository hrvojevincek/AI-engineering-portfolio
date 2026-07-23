"""Shared paths for the audit package."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "requests.db"
MIGRATIONS_DIR = ROOT / "migrations"
