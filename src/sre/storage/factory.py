"""Factory for durable SRE stores."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .memory_store import MemoryStore
from .sqlite_store import SqliteStore


def create_store_from_env(
    *,
    sqlite_path: str | Path | None = None,
    backend: str | None = None,
) -> Any:
    """
    Resolve persistence backend from environment.

    ``SRE_STORE_BACKEND`` — ``memory`` (default), ``sqlite``, or ``postgres``.
    ``SRE_SQLITE_PATH`` — SQLite file (default ``.sre/sre.db`` when backend=sqlite).
    ``SRE_DATABASE_URL`` — Postgres DSN when backend=postgres.
    """
    mode = (backend or os.environ.get("SRE_STORE_BACKEND", "memory")).strip().lower()
    if mode == "memory":
        return MemoryStore()
    if mode == "sqlite":
        raw = sqlite_path or os.environ.get("SRE_SQLITE_PATH", "").strip() or ".sre/sre.db"
        return SqliteStore(raw)
    if mode == "postgres":
        from .postgres_store import PostgresStore

        dsn = os.environ.get("SRE_DATABASE_URL", "").strip()
        if not dsn:
            raise ValueError("SRE_DATABASE_URL is required when SRE_STORE_BACKEND=postgres")
        return PostgresStore(dsn)
    raise ValueError(f"unknown SRE_STORE_BACKEND: {mode}")
