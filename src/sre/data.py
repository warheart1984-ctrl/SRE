"""Data loading utilities for SRE."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_ancestor_hints(path: str | Path | None = None) -> dict[str, str]:
    """Load PIE and proto-language ancestor hints from data file."""
    p = Path(path) if path else _repo_root() / "data" / "ancestor_hints.json"
    if not p.is_file():
        return {}
    raw = p.read_text(encoding="utf-8")
    return dict(json.loads(raw))


def load_json_data(rel_path: str) -> dict[str, Any] | list[Any]:
    """Load a JSON file relative to the repository data directory."""
    p = _repo_root() / "data" / rel_path
    if not p.is_file():
        raise FileNotFoundError(f"data file not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))
