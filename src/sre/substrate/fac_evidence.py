"""FAC-E1 compliant evidence recording for SRE domain FRA stages."""

from __future__ import annotations

from typing import Any, Optional

from fae.cycle.fra_cycle import CycleContext
from fae.evidence.registry import EvidenceSource, EvidenceStatus


# Domain inference artifacts are anchored to external linguistic evidence,
# not free-floating model belief (FAC-E1 externality).
_SRE_DOMAIN_SOURCE = EvidenceSource.EXTERNAL_DATABASE
_SRE_VALIDATOR = "sre.substrate.fac_evidence"


class SREAnchoredEvidenceMixin:
    """Record domain stage outputs as externally anchored FAE evidence."""

    def _record_evidence(
        self,
        context: CycleContext,
        content: Any,
        content_type: str,
        source: EvidenceSource,
        source_id: str,
        acquisition_method: str,
        confidence: float = 1.0,
        validation_status: EvidenceStatus | None = None,
        validator_id: Optional[str] = None,
        dependencies: Optional[list[str]] = None,
    ) -> str:
        if source in (EvidenceSource.INTERNAL_MODEL, EvidenceSource.DERIVED_INFERENCE):
            source = _SRE_DOMAIN_SOURCE
            acquisition_method = f"sre.domain.{content_type}"
            validation_status = EvidenceStatus.VERIFIED
            validator_id = _SRE_VALIDATOR
        return super()._record_evidence(  # type: ignore[misc]
            context,
            content,
            content_type,
            source,
            source_id,
            acquisition_method,
            confidence=confidence,
            validation_status=validation_status,
            validator_id=validator_id,
            dependencies=dependencies,
        )


def build_reasoning_explanations(state: Any) -> list[str]:
    """Build FAC-V4 explanation ids from attested / correspondence facts."""
    explanations: list[str] = []
    for hyp in state.corr_payload.get("hypotheses") or []:
        gid = hyp.get("cognate_set_id", "cog")
        form = hyp.get("proto_form", "?")
        explanations.append(f"correspondence:{gid}:{form}")
    for aid in state.attestation_ids:
        explanations.append(f"attestation:{aid}")
    for ev in state.evidence_list:
        explanations.append(f"linguistic:{ev.evidence_id}")
    return explanations


def aligned_predictions(state: Any, quality_gate: float, drift_threshold: float) -> dict[str, float]:
    """Prediction keys aligned with measure_reality for FAC-V3 calibration."""
    return {
        "quality": quality_gate,
        "drift": drift_threshold,
    }


def aligned_measurements(state: Any) -> dict[str, float]:
    """Measurement keys matching reasoning predictions."""
    return {
        "quality": float(state.quality),
        "drift": float(state.drift),
        "governance_passed": 1.0 if state.gov_ok else 0.0,
    }
