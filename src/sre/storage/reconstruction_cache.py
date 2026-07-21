"""Durable reconstruction result cache (API GET /reconstruction)."""

from __future__ import annotations

from typing import Any

from .base import PersistStore


class ReconstructionCache:
    """Dict-like cache backed by optional durable store."""

    def __init__(self, store: PersistStore | None = None) -> None:
        self._store = store
        self._memory: dict[str, dict[str, Any]] = {}
        if store is not None:
            self._memory.update(store.load_all_reconstruction_results())

    def get(self, reconstruction_id: str) -> dict[str, Any] | None:
        return self._memory.get(reconstruction_id)

    def __setitem__(self, reconstruction_id: str, result: dict[str, Any]) -> None:
        self._memory[reconstruction_id] = result
        if self._store is not None:
            self._store.save_reconstruction_result(reconstruction_id, result)

    def __contains__(self, reconstruction_id: str) -> bool:
        return reconstruction_id in self._memory

    def as_dict(self) -> dict[str, dict[str, Any]]:
        return dict(self._memory)
