"""Evidence API handlers."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ...evidence.models import ConstitutionalStatus
from ...evidence.registry import EvidenceRegistry


def _validation_dict(report: Any | None) -> dict[str, Any]:
    if report is None:
        return {}
    data = asdict(report)
    validated = data.get("validated_at")
    if validated is not None and hasattr(validated, "isoformat"):
        data["validated_at"] = validated.isoformat()
    return data


def submit_evidence(registry: EvidenceRegistry, body: dict[str, Any]) -> dict[str, Any]:
    """Wire to POST /api/v1/evidence."""
    evidence = registry.add_evidence(body)
    status = registry.get_status(evidence.evidence_id)
    report = registry.get_validation_report(evidence.evidence_id)
    return {
        "evidence_id": evidence.evidence_id,
        "status": status.value if status else ConstitutionalStatus.REJECTED.value,
        "sha256_hash": evidence.sha256_hash,
        "validation_report": _validation_dict(report),
    }


def _evidence_dict(evidence: Any) -> dict[str, Any]:
    return {
        "evidence_id": evidence.evidence_id,
        "evidence_type": evidence.evidence_type.value,
        "source_reference": evidence.source_reference,
        "content": evidence.content,
        "created_at": evidence.created_at.isoformat(),
        "submitted_by": evidence.submitted_by,
        "sha256_hash": evidence.sha256_hash,
        "provenance_chain": list(evidence.provenance_chain),
        "constitutional_tags": list(evidence.constitutional_tags),
    }


def get_evidence_record(registry: EvidenceRegistry, evidence_id: str) -> dict[str, Any] | None:
    """Wire to GET /api/v1/evidence/{evidence_id}."""
    evidence = registry.get_evidence(evidence_id)
    if evidence is None:
        return None
    status = registry.get_status(evidence_id)
    report = registry.get_validation_report(evidence_id)
    return {
        "evidence": _evidence_dict(evidence),
        "status": status.value if status else None,
        "validation_report": _validation_dict(report),
    }


def get_evidence_validation(registry: EvidenceRegistry, evidence_id: str) -> dict[str, Any] | None:
    """Wire to GET /api/v1/evidence/{evidence_id}/validation."""
    report = registry.get_validation_report(evidence_id)
    if report is None:
        return None
    return _validation_dict(report)
