"""CIH governance service — project approval, certificates, governance traces."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from ..evidence.models import ConstitutionalStatus
from .certificates import SovereignCertificate

if TYPE_CHECKING:
    from ..evidence.registry import EvidenceRegistry


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class FAECLanguageReconstructionService:
    """
    CIH Governance Service
    - Backed by ProjectSpec, ProjectStatus, ApprovalResult, SovereignCertificate schemas
    """

    def __init__(self, evidence_registry: EvidenceRegistry) -> None:
        self.evidence_registry = evidence_registry
        self._projects: dict[str, dict[str, Any]] = {}
        self._certificates: dict[str, SovereignCertificate] = {}
        self._traces: dict[str, dict[str, Any]] = {}
        self._event_seq = 0

    def get_certificate(self, certificate_id: str) -> dict[str, Any] | None:
        cert = self._certificates.get(certificate_id)
        return cert.to_dict() if cert else None

    def get_governance_trace(self, trace_id: str) -> dict[str, Any] | None:
        return self._traces.get(trace_id)

    def approve_reconstruction_project(self, project_spec: dict) -> dict:
        """
        Wire to:
        - POST /api/v1/cih/projects
        - POST /api/v1/cih/projects/{project_id}/approve
        - GET /api/v1/certificates/{certificate_id}

        Outcomes:
        - REQUEST_CHANGES / REJECTED — incomplete architecture (CIH-03)
        - UNDER_REVIEW — registered, awaiting full evidence baseline (CIH-01)
        - REJECTED / not APPROVED — bad evidence baseline (CIH-02)
        - APPROVED — certificate + full governance trace (CIH-04/05)
        """
        project_id = str(project_spec.get("project_id") or "").strip()
        spec = project_spec.get("spec")
        if not isinstance(spec, dict):
            spec = {}

        trace = self._new_trace(project_id or "unknown", principal="cih_service")
        self._append_event(
            trace,
            actor="CIH_SERVICE",
            event_type="PROJECT_REGISTERED",
            payload={"project_spec_keys": sorted(spec.keys())},
        )

        # CIH-03: architecture review — empty / missing core fields
        if not project_id:
            return self._finalize(
                trace,
                status="REJECTED",
                project_id="",
                reason="CIH-03: missing project_id",
            )

        target_language = str(spec.get("target_language") or "").strip()
        time_period = str(spec.get("time_period") or "").strip()
        evidence_sources = list(spec.get("evidence_sources") or [])
        architecture = spec.get("architecture")

        arch_ok = bool(target_language) or bool(architecture)
        if not arch_ok and not evidence_sources:
            self._append_event(
                trace,
                actor="CIH_SERVICE",
                event_type="ARCHITECTURE_REVIEW_FAILED",
                payload={"reason": "incomplete architecture spec"},
            )
            self._projects[project_id] = {
                "project_id": project_id,
                "spec": spec,
                "status": "REQUEST_CHANGES",
            }
            return self._finalize(
                trace,
                status="REQUEST_CHANGES",
                project_id=project_id,
                reason="CIH-03: incomplete architecture spec",
            )

        self._projects[project_id] = {
            "project_id": project_id,
            "spec": spec,
            "status": "UNDER_REVIEW",
        }
        self._append_event(
            trace,
            actor="CIH_SERVICE",
            event_type="ARCHITECTURE_REVIEW_PASSED",
            payload={
                "target_language": target_language,
                "time_period": time_period,
            },
        )

        # CIH-01 / CIH-05: registered but not fully approvable yet
        if not evidence_sources:
            return self._finalize(
                trace,
                status="UNDER_REVIEW",
                project_id=project_id,
                reason="awaiting evidence baseline",
            )

        # CIH-02: evidence baseline (FAC-E status)
        baseline = self._evaluate_evidence_baseline(evidence_sources)
        self._append_event(
            trace,
            actor="CIH_SERVICE",
            event_type="EVIDENCE_BASELINE",
            payload=baseline,
            evidence_links=evidence_sources,
        )
        if not baseline["passed"]:
            self._projects[project_id]["status"] = "REJECTED"
            return self._finalize(
                trace,
                status="REJECTED",
                project_id=project_id,
                reason="CIH-02: evidence baseline failed",
                extra={"baseline": baseline},
            )

        # Full approval requires language + period + accepted evidence
        if not target_language or not time_period:
            return self._finalize(
                trace,
                status="UNDER_REVIEW",
                project_id=project_id,
                reason="awaiting complete project scope",
                extra={"baseline": baseline},
            )

        reconstruction_id = str(
            spec.get("reconstruction_id")
            or f"recon_{project_id}"
        )
        certificate = SovereignCertificate.issue(
            project_id=project_id,
            reconstruction_id=reconstruction_id,
            target_language=target_language,
            time_period=time_period,
            constraints=dict(spec.get("constraints") or {}),
        )
        self._certificates[certificate.certificate_id] = certificate
        self._projects[project_id]["status"] = "APPROVED"
        self._projects[project_id]["certificate_id"] = certificate.certificate_id

        # Mark linked reconstruction as governance-approved when present
        if hasattr(self.evidence_registry, "register_reconstruction"):
            existing = getattr(self.evidence_registry, "_reconstructions", {}).get(
                reconstruction_id
            )
            if existing is not None:
                existing["governance_approved"] = True
            else:
                self.evidence_registry.register_reconstruction(
                    reconstruction_id,
                    evidence_ids=evidence_sources,
                    proto_model={"id": reconstruction_id},
                    metrics={"drift": 0.0, "consistency": 1.0, "aligned": True},
                    constraints={
                        "evidence_min_count": 1,
                        "drift_threshold": 0.6,
                        "require_governance": True,
                    },
                    governance_approved=True,
                    alignment_ok=True,
                )

        self._append_event(
            trace,
            actor="CIH_SERVICE",
            event_type="CERTIFICATE_ISSUED",
            payload={"certificate_id": certificate.certificate_id},
            evidence_links=evidence_sources,
        )
        trace["certificate_id"] = certificate.certificate_id
        trace["constitutional_summary"] = {
            "fac_e": {"passed": True, "details": baseline},
            "fac_v": {"passed": True, "details": []},
        }

        return self._finalize(
            trace,
            status="APPROVED",
            project_id=project_id,
            certificate_id=certificate.certificate_id,
            extra={"certificate": certificate.to_dict(), "baseline": baseline},
        )

    def _evaluate_evidence_baseline(self, evidence_sources: list[str]) -> dict[str, Any]:
        accepted: list[str] = []
        rejected: list[str] = []
        missing: list[str] = []
        for eid in evidence_sources:
            status = self.evidence_registry.get_status(eid)
            if status is None:
                missing.append(eid)
            elif status == ConstitutionalStatus.ACCEPTED:
                accepted.append(eid)
            else:
                rejected.append(eid)
        passed = bool(accepted) and not rejected and not missing
        return {
            "passed": passed,
            "accepted": accepted,
            "rejected": rejected,
            "missing": missing,
        }

    def _new_trace(self, project_id: str, *, principal: str) -> dict[str, Any]:
        trace_id = f"trace_{project_id}_{len(self._traces) + 1:03d}"
        trace = {
            "trace_id": trace_id,
            "reconstruction_id": f"recon_{project_id}",
            "project_id": project_id,
            "certificate_id": None,
            "created_at": _now(),
            "principal": principal,
            "events": [],
            "constitutional_summary": {
                "fac_e": {"passed": False, "details": []},
                "fac_v": {"passed": False, "details": []},
            },
        }
        self._traces[trace_id] = trace
        return trace

    def _append_event(
        self,
        trace: dict[str, Any],
        *,
        actor: str,
        event_type: str,
        payload: dict[str, Any],
        evidence_links: list[str] | None = None,
    ) -> None:
        self._event_seq += 1
        trace["events"].append(
            {
                "event_id": f"ev_{self._event_seq:03d}",
                "timestamp": _now(),
                "actor": actor,
                "type": event_type,
                "payload": payload,
                "evidence_links": list(evidence_links or []),
            }
        )

    def _finalize(
        self,
        trace: dict[str, Any],
        *,
        status: str,
        project_id: str,
        reason: str = "",
        certificate_id: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = {
            "project_id": project_id,
            "status": status,
            "reason": reason,
            "trace_id": trace["trace_id"],
            "governance_trace": trace,
        }
        if certificate_id:
            result["certificate_id"] = certificate_id
        if extra:
            result.update(extra)
        return result
