"""Sovereign Certificate model — schemas/sovereign_certificate.schema.json."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any


@dataclass
class SovereignCertificate:
    """Wire to GET /api/v1/certificates/{certificate_id} and OpenAPI SovereignCertificate."""

    certificate_id: str
    version: str = "1.0"
    issued_at: str = ""
    issuer: dict[str, Any] = field(default_factory=dict)
    subject: dict[str, Any] = field(default_factory=dict)
    scope: dict[str, Any] = field(default_factory=dict)
    constitutional_status: dict[str, Any] = field(default_factory=dict)
    signatures: dict[str, Any] = field(default_factory=dict)
    validity: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def issue(
        cls,
        *,
        project_id: str,
        reconstruction_id: str,
        target_language: str,
        time_period: str,
        domains: list[str] | None = None,
        constraints: dict[str, Any] | None = None,
        fac_e: dict[str, bool] | None = None,
        fac_v: dict[str, bool] | None = None,
        ledger_entry_id: str | None = None,
    ) -> SovereignCertificate:
        now = datetime.now(timezone.utc)
        issued = now.isoformat()
        cert_id = f"cert_{project_id}"
        return cls(
            certificate_id=cert_id,
            version="1.0",
            issued_at=issued,
            issuer={
                "authority": "HYFAL Executive Council",
                "authority_id": "hyfal_001",
            },
            subject={
                "project_id": project_id,
                "reconstruction_id": reconstruction_id,
                "target_language": target_language,
                "time_period": time_period,
            },
            scope={
                "domains": domains
                or ["phonology", "lexicon", "morphology"],
                "constraints": constraints or {"max_drift": 0.6, "evidence_min_count": 1},
            },
            constitutional_status={
                "fac_e": fac_e
                or {
                    "e1_authenticity": True,
                    "e2_integrity": True,
                    "e3_provenance": True,
                    "e4_constitutional_fit": True,
                },
                "fac_v": fac_v
                or {
                    "v1_coverage": True,
                    "v2_consistency": True,
                    "v3_drift_control": True,
                    "v4_alignment": True,
                    "v5_governance_fit": True,
                },
            },
            signatures={
                "council_signature": f"sig_{cert_id}",
                "ledger_entry_id": ledger_entry_id or f"ledger_{cert_id}",
            },
            validity={
                "not_before": issued,
                "not_after": (now + timedelta(days=365)).isoformat(),
                "revocation_status": "ACTIVE",
            },
        )
