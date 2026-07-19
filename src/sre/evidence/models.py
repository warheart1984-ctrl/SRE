"""Evidence domain models — aligned with OpenAPI EvidenceSubmission / EvidenceRecord."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class EvidenceType(Enum):
    INSCRIPTION = "inscription"
    LEXICAL_ITEM = "lexical_item"
    PHONOLOGICAL_RULE = "phonological_rule"
    CORPUS_SAMPLE = "corpus_sample"


class ConstitutionalStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    REVOKED = "revoked"


@dataclass
class LinguisticEvidence:
    """Immutable linguistic evidence record (EvidenceRecord.evidence)."""

    evidence_id: str
    evidence_type: EvidenceType
    source_reference: str
    content: dict[str, Any]
    created_at: datetime
    submitted_by: str
    sha256_hash: str
    provenance_chain: list[str] = field(default_factory=list)
    constitutional_tags: list[str] = field(default_factory=list)


@dataclass
class ConstitutionalValidationResult:
    """FAC-E1–E4 / FAC-V1–V5 validation report (OpenAPI ConstitutionalValidationResult)."""

    evidence_id: str
    is_valid: bool
    failed_checks: list[str]
    report: dict[str, Any]
    validated_at: datetime
