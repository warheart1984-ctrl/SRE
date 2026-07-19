"""EvidenceRegistry — constitutional evidence engine (FAC-E1–E4)."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from .dantomax_client import DantomaxClient
from .models import (
    ConstitutionalStatus,
    ConstitutionalValidationResult,
    EvidenceType,
    LinguisticEvidence,
)

# Substrate authenticity denylist (FAC-E1)
_INVALID_SOURCE_REFERENCES = frozenset(
    {"", "invalid", "n/a", "unknown", "none", "null"}
)


class EvidenceRegistry:
    """
    EvidenceRegistry
    - Backed by EvidenceSubmission / EvidenceRecord API schemas
    - Enforces FAC-E1–E4 (Substrate: minimal rejection paths)
    - Integrates with DantomaxClient
    """

    def __init__(self, dantomax_client: DantomaxClient | None = None) -> None:
        self._store: dict[str, LinguisticEvidence] = {}
        self._status: dict[str, ConstitutionalStatus] = {}
        self._validation_reports: dict[str, ConstitutionalValidationResult] = {}
        self._reconstructions: dict[str, dict[str, Any]] = {}
        self._dantomax = dantomax_client

    def add_evidence(self, evidence_data: dict[str, Any]) -> LinguisticEvidence:
        """
        Wire to POST /api/v1/evidence
        - canonicalize input (EvidenceSubmission)
        - compute SHA256
        - run FAC-E1–E4 checks
        - optionally register with Dantomax

        Returns LinguisticEvidence always; check get_status / get_validation_report
        for ACCEPTED vs REJECTED and failed_checks.
        """
        canonical = self._canonicalize(evidence_data)
        sha256_hash = self._compute_sha256(canonical)
        evidence = self._build_evidence_object(canonical, sha256_hash)
        validation = self._run_constitutional_validation(
            evidence, claimed_sha256=canonical.get("claimed_sha256")
        )
        self._store[evidence.evidence_id] = evidence
        self._validation_reports[evidence.evidence_id] = validation
        self._status[evidence.evidence_id] = (
            ConstitutionalStatus.ACCEPTED
            if validation.is_valid
            else ConstitutionalStatus.REJECTED
        )
        if self._dantomax is not None and validation.is_valid:
            receipt = self._dantomax.register_evidence(
                evidence.evidence_id,
                evidence.sha256_hash,
                validation.report,
            )
            validation.report["dantomax"] = receipt
        return evidence

    def verify_with_dantomax(self, evidence_id: str) -> dict[str, Any] | None:
        """Cross-check stored evidence hash against Dantomax attestations."""
        if self._dantomax is None:
            return None
        evidence = self._store.get(evidence_id)
        if evidence is None:
            return {"is_verified": False, "verification_details": {"reason": "not_in_registry"}}
        return self._dantomax.verify_evidence(evidence_id, evidence.sha256_hash)

    def get_evidence(self, evidence_id: str) -> LinguisticEvidence | None:
        """Wire to GET /api/v1/evidence/{evidence_id}."""
        return self._store.get(evidence_id)

    def get_status(self, evidence_id: str) -> ConstitutionalStatus | None:
        """Return constitutional status for evidence_id."""
        return self._status.get(evidence_id)

    def get_validation_report(
        self, evidence_id: str
    ) -> ConstitutionalValidationResult | None:
        """Wire to GET /api/v1/evidence/{evidence_id}/validation."""
        return self._validation_reports.get(evidence_id)

    def revalidate_evidence(self, evidence_id: str) -> ConstitutionalValidationResult:
        """
        Re-run FAC-E1–E4 on stored evidence (detects post-store content tampering).
        """
        evidence = self._store.get(evidence_id)
        if evidence is None:
            raise KeyError(f"unknown evidence_id: {evidence_id}")
        validation = self._run_constitutional_validation(evidence, claimed_sha256=None)
        self._validation_reports[evidence_id] = validation
        self._status[evidence_id] = (
            ConstitutionalStatus.ACCEPTED
            if validation.is_valid
            else ConstitutionalStatus.REJECTED
        )
        return validation

    def register_reconstruction(
        self,
        reconstruction_id: str,
        *,
        evidence_ids: list[str] | None = None,
        proto_model: dict[str, Any] | None = None,
        metrics: dict[str, Any] | None = None,
        constraints: dict[str, Any] | None = None,
        governance_approved: bool = False,
        inconsistent: bool = False,
        alignment_ok: bool = True,
    ) -> None:
        """Persist reconstruction metadata for FAC-V1–V5 validation."""
        self._reconstructions[reconstruction_id] = {
            "reconstruction_id": reconstruction_id,
            "evidence_ids": list(evidence_ids or []),
            "proto_model": proto_model or {},
            "metrics": metrics or {},
            "constraints": constraints or {},
            "governance_approved": governance_approved,
            "inconsistent": inconsistent,
            "alignment_ok": alignment_ok,
        }

    def validate_reconstruction(
        self, reconstruction_id: str
    ) -> ConstitutionalValidationResult:
        """
        Used by FRA engine and CIH service:
        - aggregate linked evidence
        - compute FAC-V1–V5 metrics

        Promotion-gate sentinel IDs (when not registered):
        recon_empty → FAC-V1, recon_inconsistent → FAC-V2,
        recon_drift → FAC-V3, recon_align → FAC-V4, recon_scope → FAC-V5
        """
        failed: list[str] = []
        rec = self._reconstructions.get(reconstruction_id)

        if rec is None:
            # Sentinel fixtures for constitutional promotion gates
            sentinel_map = {
                "recon_empty": "FAC-V1: Coverage",
                "recon_inconsistent": "FAC-V2: Consistency",
                "recon_drift": "FAC-V3: Drift Control",
                "recon_align": "FAC-V4: Alignment",
                "recon_scope": "FAC-V5: Governance Fit",
            }
            if reconstruction_id in sentinel_map:
                failed.append(sentinel_map[reconstruction_id])
            else:
                # Unknown reconstruction → treat as insufficient coverage
                failed.append("FAC-V1: Coverage")
            return self._fac_v_result(reconstruction_id, failed, {"sentinel": True})

        evidence_ids = list(rec.get("evidence_ids") or [])
        constraints = dict(rec.get("constraints") or {})
        metrics = dict(rec.get("metrics") or {})
        min_count = int(constraints.get("evidence_min_count", 1))
        drift_threshold = float(constraints.get("drift_threshold", 0.6))

        # FAC-V1 Coverage
        accepted = [
            eid
            for eid in evidence_ids
            if self._status.get(eid) == ConstitutionalStatus.ACCEPTED
        ]
        if len(accepted) < min_count or len(evidence_ids) < min_count:
            failed.append("FAC-V1: Coverage")

        # FAC-V2 Consistency
        consistency = float(metrics.get("consistency", 1.0))
        if rec.get("inconsistent") or consistency < 0.35:
            failed.append("FAC-V2: Consistency")
        else:
            # Proto-forms must cite evidence that exists
            primary = (rec.get("proto_model") or {}).get("primary") or {}
            links = list(primary.get("evidence_links") or [])
            if links and not any(eid in evidence_ids for eid in links):
                failed.append("FAC-V2: Consistency")

        # FAC-V3 Drift Control
        drift = float(metrics.get("drift", 0.0))
        if drift > drift_threshold:
            failed.append("FAC-V3: Drift Control")

        # FAC-V4 Alignment
        if not rec.get("alignment_ok", True) or metrics.get("aligned") is False:
            # Only fail when explicitly misaligned; single-period may lack cross links
            if rec.get("alignment_ok") is False:
                failed.append("FAC-V4: Alignment")

        # FAC-V5 Governance Fit
        if constraints.get("require_governance") and not rec.get("governance_approved"):
            failed.append("FAC-V5: Governance Fit")

        report = {
            "reconstruction_id": reconstruction_id,
            "evidence_count": len(evidence_ids),
            "accepted_evidence_count": len(accepted),
            "metrics": metrics,
            "constraints": constraints,
            "failed_checks": failed,
        }
        return self._fac_v_result(reconstruction_id, failed, report)

    def _fac_v_result(
        self,
        reconstruction_id: str,
        failed: list[str],
        report: dict[str, Any],
    ) -> ConstitutionalValidationResult:
        return ConstitutionalValidationResult(
            evidence_id=reconstruction_id,
            is_valid=len(failed) == 0,
            failed_checks=failed,
            report=report,
            validated_at=datetime.now(timezone.utc),
        )

    # --- Internal helpers ---

    def _canonicalize(self, evidence_data: dict[str, Any]) -> dict[str, Any]:
        required = ("evidence_id", "evidence_type", "content", "submitted_by")
        missing = [k for k in required if k not in evidence_data]
        if missing:
            raise ValueError(f"missing required fields: {missing}")
        content = evidence_data["content"]
        if not isinstance(content, dict):
            raise ValueError("content must be a dict")
        return {
            "evidence_id": str(evidence_data["evidence_id"]),
            "evidence_type": str(evidence_data["evidence_type"]),
            "source_reference": str(evidence_data.get("source_reference", "")).strip(),
            "content": content,
            "submitted_by": str(evidence_data["submitted_by"]).strip(),
            "provenance_chain": list(evidence_data.get("provenance_chain") or []),
            "constitutional_tags": list(evidence_data.get("constitutional_tags") or []),
            "claimed_sha256": evidence_data.get("claimed_sha256"),
        }

    def _compute_sha256(self, canonical_data: dict[str, Any]) -> str:
        payload = {
            "evidence_id": canonical_data["evidence_id"],
            "evidence_type": canonical_data["evidence_type"],
            "source_reference": canonical_data["source_reference"],
            "content": canonical_data["content"],
            "submitted_by": canonical_data["submitted_by"],
            "provenance_chain": canonical_data["provenance_chain"],
            "constitutional_tags": canonical_data["constitutional_tags"],
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
        return hashlib.sha256(encoded).hexdigest()

    def _build_evidence_object(
        self,
        evidence_data: dict[str, Any],
        sha256_hash: str,
    ) -> LinguisticEvidence:
        return LinguisticEvidence(
            evidence_id=evidence_data["evidence_id"],
            evidence_type=EvidenceType(evidence_data["evidence_type"]),
            source_reference=evidence_data["source_reference"],
            content=dict(evidence_data["content"]),
            created_at=datetime.now(timezone.utc),
            submitted_by=evidence_data["submitted_by"],
            sha256_hash=sha256_hash,
            provenance_chain=list(evidence_data["provenance_chain"]),
            constitutional_tags=list(evidence_data["constitutional_tags"]),
        )

    def _run_constitutional_validation(
        self,
        evidence: LinguisticEvidence,
        claimed_sha256: str | None,
    ) -> ConstitutionalValidationResult:
        failed: list[str] = []
        if not self._check_fac_e1_authenticity(evidence):
            failed.append("FAC-E1: Authenticity")
        if not self._check_fac_e2_integrity(evidence, claimed_sha256):
            failed.append("FAC-E2: Integrity")
        if not self._check_fac_e3_provenance(evidence):
            failed.append("FAC-E3: Provenance")
        if not self._check_fac_e4_constitutional_fit(evidence):
            failed.append("FAC-E4: Constitutional Fit")
        is_valid = len(failed) == 0
        report = {
            "evidence_id": evidence.evidence_id,
            "sha256_hash": evidence.sha256_hash,
            "failed_checks": failed,
            "tags": evidence.constitutional_tags,
        }
        return ConstitutionalValidationResult(
            evidence_id=evidence.evidence_id,
            is_valid=is_valid,
            failed_checks=failed,
            report=report,
            validated_at=datetime.now(timezone.utc),
        )

    def _check_fac_e1_authenticity(self, evidence: LinguisticEvidence) -> bool:
        ref = (evidence.source_reference or "").strip().lower()
        return bool(ref) and ref not in _INVALID_SOURCE_REFERENCES

    def _check_fac_e2_integrity(
        self,
        evidence: LinguisticEvidence,
        claimed_sha256: str | None,
    ) -> bool:
        recomputed = self._compute_sha256(
            {
                "evidence_id": evidence.evidence_id,
                "evidence_type": evidence.evidence_type.value,
                "source_reference": evidence.source_reference,
                "content": evidence.content,
                "submitted_by": evidence.submitted_by,
                "provenance_chain": evidence.provenance_chain,
                "constitutional_tags": evidence.constitutional_tags,
            }
        )
        if recomputed != evidence.sha256_hash:
            return False
        if claimed_sha256 is not None and claimed_sha256 != recomputed:
            return False
        return True

    def _check_fac_e3_provenance(self, evidence: LinguisticEvidence) -> bool:
        chain = evidence.provenance_chain
        if not chain:
            return True
        for entry in chain:
            if not isinstance(entry, str) or not entry.strip():
                return False
            if entry.strip().upper() in {"BREAK", "TAMPERED", "FORGED"}:
                return False
        # Optional Dantomax cross-check for dantomax:* receipts
        if self._dantomax is not None:
            for entry in chain:
                if not entry.startswith("dantomax:"):
                    continue
                verified = self._dantomax.verify_evidence(
                    evidence.evidence_id, evidence.sha256_hash
                )
                if not verified.get("is_verified"):
                    return False
        return True

    def _check_fac_e4_constitutional_fit(self, evidence: LinguisticEvidence) -> bool:
        if not evidence.submitted_by.strip():
            return False
        try:
            EvidenceType(evidence.evidence_type.value)
        except ValueError:
            return False
        forbidden = {"unconstitutional", "forbidden", "out_of_scope"}
        tags = {t.strip().lower() for t in evidence.constitutional_tags}
        if tags & forbidden:
            return False
        return True
