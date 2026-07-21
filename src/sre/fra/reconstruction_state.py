"""Mutable state for incremental SRE FRA pipeline execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fae.cycle.fra_cycle import FRACycleStage

# SRE domain stage → FAE constitutional stage (many-to-one).
SRE_TO_FAE_STAGE_MAP: dict[str, FRACycleStage] = {
    "OBSERVE": FRACycleStage.OBSERVE,
    "INGEST": FRACycleStage.OBSERVE,
    "ATTEST": FRACycleStage.EXTRACT_FACTS,
    "ALIGN": FRACycleStage.BUILD_MODEL,
    "CLUSTER": FRACycleStage.BUILD_MODEL,
    "INFER": FRACycleStage.REASON,
    "VALIDATE": FRACycleStage.ACT,
    "GOVERN": FRACycleStage.MEASURE_REALITY,
    "CERTIFY": FRACycleStage.COMPARE,
    "ARCHIVE": FRACycleStage.UPDATE_MODEL,
}

FAE_TO_SRE_STAGE_GROUPS: dict[FRACycleStage, tuple[str, ...]] = {
    FRACycleStage.OBSERVE: ("OBSERVE", "INGEST"),
    FRACycleStage.EXTRACT_FACTS: ("ATTEST",),
    FRACycleStage.BUILD_MODEL: ("ALIGN", "CLUSTER"),
    FRACycleStage.REASON: ("INFER",),
    FRACycleStage.ACT: ("VALIDATE",),
    FRACycleStage.MEASURE_REALITY: ("GOVERN",),
    FRACycleStage.COMPARE: ("CERTIFY",),
    FRACycleStage.UPDATE_MODEL: ("ARCHIVE",),
}


@dataclass
class ReconstructionRunState:
    """Carries intermediate artifacts across SRE FRA stage groups."""

    target_language: str
    time_period: str
    evidence_sources: list[str]
    iteration: int = 0

    evidence_list: list[Any] = field(default_factory=list)
    stages_completed: list[str] = field(default_factory=list)

    observed: dict[str, Any] = field(default_factory=dict)
    ingested: dict[str, Any] = field(default_factory=dict)
    attest_out: dict[str, Any] = field(default_factory=dict)
    attestation_ids: list[str] = field(default_factory=list)
    att_summary: dict[str, Any] = field(default_factory=dict)

    analysis: dict[str, Any] = field(default_factory=dict)
    flags_by_lang: dict[str, list[str]] = field(default_factory=dict)
    corr_payload: dict[str, Any] = field(default_factory=dict)

    temporal_map: dict[str, Any] = field(default_factory=dict)
    aligned: dict[str, Any] = field(default_factory=dict)
    clustered: dict[str, Any] = field(default_factory=dict)

    proto_model: dict[str, Any] = field(default_factory=dict)
    refine_out: dict[str, Any] = field(default_factory=dict)
    test_result: dict[str, Any] = field(default_factory=dict)
    drift: float = 1.0
    quality: float = 0.0

    metrics: dict[str, Any] = field(default_factory=dict)
    recon_id: str = ""

    validation: Any = None
    validate_out: dict[str, Any] = field(default_factory=dict)

    govern_out: dict[str, Any] = field(default_factory=dict)
    lineage: dict[str, Any] | None = None
    gov_ok: bool = True
    gov_reason: str = ""

    certificate: dict[str, Any] = field(default_factory=dict)
    archive: dict[str, Any] = field(default_factory=dict)

    status: str = "RUNNING"
    failed_stage: str | None = None
    reason: str | None = None

    @property
    def dantomax(self) -> Any:
        return getattr(self._engine.evidence_registry, "_dantomax", None)

    @property
    def cel(self) -> Any:
        return getattr(self._engine.evidence_registry, "cel", None)

    _engine: Any = field(default=None, repr=False)

    def fail(self, stage: str, reason: str, **extra: Any) -> dict[str, Any]:
        self.status = "FAILED"
        self.failed_stage = stage
        self.reason = reason
        out: dict[str, Any] = {
            "reconstruction_id": self.recon_id or None,
            "status": "FAILED",
            "fra_stage": stage,
            "reason": reason,
            "stages_completed": list(self.stages_completed),
            "metrics": self.metrics or {},
        }
        out.update(extra)
        return out

    def complete(self) -> dict[str, Any]:
        self.status = "COMPLETED"
        return {
            "reconstruction_id": self.recon_id,
            "status": "COMPLETED",
            "fra_stage": "ARCHIVE",
            "proto_language_model": self.proto_model,
            "certificate_id": self.certificate.get("certificate_id"),
            "certificate": self.certificate,
            "archive_record": self.archive,
            "validation": self.validate_out,
            "governance": self.govern_out,
            "stages_completed": list(self.stages_completed),
            "metrics": self.metrics,
            "lineage": self.lineage,
            "human_lineage": self.govern_out.get("human_lineage"),
            "refinement_halted": self.refine_out.get("refinement_halted"),
            "quality_improved": self.refine_out.get("quality_improved"),
            "correspondence_search": self.corr_payload,
            "cel": self.cel.summary() if self.cel is not None else None,
            "iteration": self.iteration,
            "drift": self.drift,
            "quality": self.quality,
        }
