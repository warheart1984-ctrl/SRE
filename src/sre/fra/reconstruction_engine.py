"""ChronologicalReconstruction — FRA engine (rule-based vertical slice)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..corpus.loader import seed_registry_from_corpus
from ..mcrl.rosetta_engine import MCRLRosettaEngine
from .stages import FRAStages

if TYPE_CHECKING:
    from ..ai.hlrm_agent import HLRMAIAgent
    from ..evidence.registry import EvidenceRegistry


class ChronologicalReconstruction:
    """
    FRA Engine
    - Executes 9-stage FRA cycle on EvidenceRegistry-backed evidence
    - Auto-seeds missing IDs from data/fra_corpus_v01.json
    """

    def __init__(
        self,
        evidence_registry: EvidenceRegistry,
        ai_agent: HLRMAIAgent | None = None,
        *,
        constraints: dict[str, Any] | None = None,
        rosetta: MCRLRosettaEngine | None = None,
        corpus_path: str | None = None,
    ) -> None:
        self.evidence_registry = evidence_registry
        self.ai_agent = ai_agent
        self.corpus_path = corpus_path
        self.constraints = {
            "max_iterations": 5,
            "drift_threshold": 0.6,
            "evidence_min_count": 1,
            "quality_gate": 0.35,
            "require_drift_metrics": True,
            **(constraints or {}),
        }
        self.stages = FRAStages()
        self.rosetta = rosetta or MCRLRosettaEngine()

    def reconstruct_language(
        self,
        target_language: str,
        time_period: str,
        evidence_sources: list[str],
    ) -> dict:
        """
        Wire to POST /api/v1/reconstruction
        Returns ReconstructionDetail-shaped dict.
        """
        stages_completed: list[str] = []

        # FRA-02: empty evidence list → halt
        if not evidence_sources:
            return {
                "reconstruction_id": None,
                "status": "FAILED",
                "fra_stage": "OBSERVE",
                "reason": "FRA-02: empty evidence list",
                "stages_completed": [],
                "metrics": {},
            }

        # Ensure corpus evidence is present for requested IDs (Mythar + IE catalogs)
        seed_registry_from_corpus(
            self.evidence_registry,
            path=self.corpus_path,
            evidence_ids=list(evidence_sources),
            search_catalog=True,
        )

        evidence_list = []
        missing = []
        for eid in evidence_sources:
            ev = self.evidence_registry.get_evidence(eid)
            if ev is None:
                missing.append(eid)
            else:
                evidence_list.append(ev)

        if missing or not evidence_list:
            return {
                "reconstruction_id": None,
                "status": "FAILED",
                "fra_stage": "OBSERVE",
                "reason": f"missing evidence: {missing}",
                "stages_completed": [],
                "metrics": {},
            }

        if self.ai_agent is None:
            from ..ai.hlrm_agent import HLRMAIAgent

            self.ai_agent = HLRMAIAgent(self.evidence_registry, config={})

        # 1. OBSERVE
        observed = self.stages.observe(evidence_list)
        stages_completed.append("OBSERVE")

        # 2. EXTRACT
        analysis = self.ai_agent.analyze_evidence_patterns(evidence_list)
        extracted = self.stages.extract(analysis)
        stages_completed.append("EXTRACT")

        # 3. BUILD
        hypotheses = self.ai_agent.predict_proto_forms(analysis)
        proto_model = self.stages.build(hypotheses, target_language, time_period)
        stages_completed.append("BUILD")

        # 4. TEST (+ mandatory drift metrics)
        test_result = self.stages.test(proto_model, evidence_list)
        stages_completed.append("TEST")
        if self.constraints.get("require_drift_metrics") and "drift" not in test_result:
            return {
                "reconstruction_id": proto_model.get("id"),
                "status": "FAILED",
                "fra_stage": "TEST",
                "reason": "FRA-03: drift metrics required",
                "stages_completed": stages_completed,
                "metrics": test_result,
            }

        drift = float(test_result.get("drift", 1.0))
        quality = float(test_result.get("quality", 0.0))
        threshold = float(self.constraints["drift_threshold"])
        quality_gate = float(self.constraints["quality_gate"])

        # 5. REFINE — always run progressive refinement (FRA-04).
        # Extra iterations when drift is high or coverage quality is below gate.
        needs_extra = drift > threshold or quality < quality_gate
        max_iterations = int(self.constraints["max_iterations"]) if needs_extra else 1
        refine_out = self.stages.refine(
            proto_model,
            analysis,
            self.ai_agent,
            max_iterations=max_iterations,
            quality_gate=quality_gate,
        )
        proto_model = refine_out["proto_model"]
        test_result = self.stages.test(proto_model, evidence_list)
        drift = float(test_result.get("drift", drift))
        quality = float(refine_out.get("quality", quality))
        stages_completed.append("REFINE")

        # 6. ALIGN
        temporal_map = self.rosetta.map_temporal(evidence_list)
        aligned = self.stages.align(proto_model, temporal_map)
        proto_model = aligned.get("proto_model") or proto_model
        stages_completed.append("ALIGN")

        metrics = {
            "drift": drift,
            "coverage": float(test_result.get("coverage", 0.0)),
            "quality": quality,
            "consistency": float(test_result.get("coverage", 0.0)),
            "evidence_count": len(evidence_list),
            "observe": observed,
            "extract_summary": {
                "clusters": len(extracted.get("lexical_clusters") or []),
                "shifts": len(extracted.get("phonological_shifts") or []),
                "cognates": len(extracted.get("cognate_groups") or []),
            },
            "aligned": aligned.get("aligned", False),
        }

        # Register reconstruction for FAC-V
        recon_id = str(proto_model.get("id"))
        self.evidence_registry.register_reconstruction(
            recon_id,
            evidence_ids=[e.evidence_id for e in evidence_list],
            proto_model=proto_model,
            metrics=metrics,
            constraints={
                "evidence_min_count": int(self.constraints["evidence_min_count"]),
                "drift_threshold": threshold,
            },
            governance_approved=False,
        )

        # 7. VALIDATE
        validation = self.evidence_registry.validate_reconstruction(recon_id)
        validate_out = self.stages.validate(validation)
        stages_completed.append("VALIDATE")

        if not validation.is_valid:
            return {
                "reconstruction_id": recon_id,
                "status": "FAILED",
                "fra_stage": "VALIDATE",
                "proto_language_model": proto_model,
                "validation": validate_out,
                "stages_completed": stages_completed,
                "metrics": metrics,
                "refinement_halted": refine_out.get("refinement_halted"),
                "quality_improved": refine_out.get("quality_improved"),
            }

        # 8. CERTIFY
        certificate = self.stages.certify(proto_model, validation)
        stages_completed.append("CERTIFY")

        # 9. ARCHIVE
        archive = self.stages.archive(
            proto_model, certificate, stages_completed, metrics
        )
        stages_completed.append("ARCHIVE")

        # Ensure all nine stages listed
        if set(FRAStages.STAGE_ORDER) - set(stages_completed):
            return {
                "reconstruction_id": recon_id,
                "status": "FAILED",
                "fra_stage": stages_completed[-1] if stages_completed else "OBSERVE",
                "reason": "FRA-01: incomplete stage set",
                "stages_completed": stages_completed,
                "metrics": metrics,
            }

        return {
            "reconstruction_id": recon_id,
            "status": "COMPLETED",
            "fra_stage": "ARCHIVE",
            "proto_language_model": proto_model,
            "certificate_id": certificate.get("certificate_id"),
            "archive_record": archive,
            "validation": validate_out,
            "stages_completed": stages_completed,
            "metrics": metrics,
            "refinement_halted": refine_out.get("refinement_halted"),
            "quality_improved": refine_out.get("quality_improved"),
        }
