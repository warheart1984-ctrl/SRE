"""Persistence store protocol for SRE evidence and reconstructions."""

from __future__ import annotations

from typing import Any, Protocol

from ..evidence.models import (
    ConstitutionalStatus,
    ConstitutionalValidationResult,
    LinguisticEvidence,
)


class PersistStore(Protocol):
    """Backend for evidence rows, reconstruction metadata, and API result cache."""

    def save_evidence(
        self,
        evidence: LinguisticEvidence,
        status: ConstitutionalStatus,
        validation: ConstitutionalValidationResult,
    ) -> None: ...

    def load_evidence(
        self,
    ) -> list[tuple[LinguisticEvidence, ConstitutionalStatus, ConstitutionalValidationResult]]: ...

    def save_reconstruction_meta(self, reconstruction_id: str, data: dict[str, Any]) -> None: ...

    def load_reconstruction_meta(self, reconstruction_id: str) -> dict[str, Any] | None: ...

    def load_all_reconstruction_meta(self) -> dict[str, dict[str, Any]]: ...

    def save_reconstruction_result(
        self, reconstruction_id: str, result: dict[str, Any]
    ) -> None: ...

    def load_reconstruction_result(self, reconstruction_id: str) -> dict[str, Any] | None: ...

    def load_all_reconstruction_results(self) -> dict[str, dict[str, Any]]: ...
