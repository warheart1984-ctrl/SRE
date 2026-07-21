"""In-memory persistence (testing / explicit opt-out of durability)."""

from __future__ import annotations

from typing import Any

from ..evidence.models import (
    ConstitutionalStatus,
    ConstitutionalValidationResult,
    LinguisticEvidence,
)


class MemoryStore:
    """Dict-backed store implementing the PersistStore protocol."""

    def __init__(self) -> None:
        self._evidence: dict[
            str,
            tuple[LinguisticEvidence, ConstitutionalStatus, ConstitutionalValidationResult],
        ] = {}
        self._reconstruction_meta: dict[str, dict[str, Any]] = {}
        self._reconstruction_results: dict[str, dict[str, Any]] = {}

    def save_evidence(
        self,
        evidence: LinguisticEvidence,
        status: ConstitutionalStatus,
        validation: ConstitutionalValidationResult,
    ) -> None:
        self._evidence[evidence.evidence_id] = (evidence, status, validation)

    def load_evidence(
        self,
    ) -> list[tuple[LinguisticEvidence, ConstitutionalStatus, ConstitutionalValidationResult]]:
        return list(self._evidence.values())

    def save_reconstruction_meta(self, reconstruction_id: str, data: dict[str, Any]) -> None:
        self._reconstruction_meta[reconstruction_id] = dict(data)

    def load_reconstruction_meta(self, reconstruction_id: str) -> dict[str, Any] | None:
        row = self._reconstruction_meta.get(reconstruction_id)
        return dict(row) if row is not None else None

    def load_all_reconstruction_meta(self) -> dict[str, dict[str, Any]]:
        return {k: dict(v) for k, v in self._reconstruction_meta.items()}

    def save_reconstruction_result(self, reconstruction_id: str, result: dict[str, Any]) -> None:
        self._reconstruction_results[reconstruction_id] = dict(result)

    def load_reconstruction_result(self, reconstruction_id: str) -> dict[str, Any] | None:
        row = self._reconstruction_results.get(reconstruction_id)
        return dict(row) if row is not None else None

    def load_all_reconstruction_results(self) -> dict[str, dict[str, Any]]:
        return {k: dict(v) for k, v in self._reconstruction_results.items()}
