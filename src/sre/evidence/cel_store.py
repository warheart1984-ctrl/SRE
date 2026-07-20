"""Append-only JSONL persistence for the Constitutional Evidence Ledger."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from .cel import CELEntry, ConstitutionalEvidenceLedger

DEFAULT_CEL_PATH = Path("data/cel/ledger.jsonl")


class CELStore:
    """
    File-backed append log for CEL entries.

    Each line is one JSON object matching ``schemas/cel_entry.schema.json``.
    """

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path or DEFAULT_CEL_PATH)

    def exists(self) -> bool:
        return self.path.is_file() and self.path.stat().st_size > 0

    def append_entry(self, entry: CELEntry) -> None:
        """Append one CEL entry to the JSONL log."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(entry.to_dict(), separators=(",", ":"), ensure_ascii=False)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def iter_entries(self) -> Iterator[dict[str, Any]]:
        """Yield raw entry dicts from the append log."""
        if not self.path.is_file():
            return
        with self.path.open(encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    yield json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid JSON at {self.path}:{line_no}") from exc

    def load_all(self) -> list[dict[str, Any]]:
        return list(self.iter_entries())

    def entry_count(self) -> int:
        return sum(1 for _ in self.iter_entries())

    def replay_into(self, ledger: ConstitutionalEvidenceLedger) -> int:
        """Restore persisted entries into an in-memory ledger. Returns count loaded."""
        count = 0
        for raw in self.iter_entries():
            ledger.restore_entry(raw)
            count += 1
        return count

    def export_snapshot(self) -> dict[str, Any]:
        """Metadata snapshot for explorer / API head responses."""
        return {
            "store_path": str(self.path),
            "entry_count": self.entry_count(),
            "exists": self.exists(),
        }
