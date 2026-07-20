"""Constitutional Promotion Gates — Substrate + Substration vertical slice."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from sre.ai.hlrm_agent import HLRMAIAgent
from sre.corpus.loader import seed_registry_from_corpus
from sre.evidence.models import ConstitutionalStatus
from sre.evidence.registry import EvidenceRegistry
from sre.fra.reconstruction_engine import ChronologicalReconstruction
from sre.governance.cih_service import FAECLanguageReconstructionService

ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "data" / "fra_corpus_v01.json"

_PENDING_CIH = "pending Substration — CIH / FAC-V4–V5 not in vertical slice"


def _valid_evidence(**overrides: object) -> dict:
    base: dict = {
        "evidence_id": "evid_gate_001",
        "evidence_type": "inscription",
        "source_reference": "Corpus A, Vol. 1",
        "content": {"text": "ma taru en", "gloss": "breath rises"},
        "submitted_by": "principal_test",
        "provenance_chain": [],
        "constitutional_tags": ["FAC-E"],
    }
    base.update(overrides)
    return base


class ConstitutionalPromotionTests(unittest.TestCase):
    """
    Promotion gates for SRE v0.1.
    Vertical slice: FAC-E, FAC-V, FRA, AI, CIH live on Mythar + IE corpora.
    """

    def setUp(self) -> None:
        self.registry = EvidenceRegistry(dantomax_client=None)
        self.ai_agent = HLRMAIAgent(self.registry, config={})
        self.fra = ChronologicalReconstruction(self.registry, self.ai_agent)
        self.cih = FAECLanguageReconstructionService(self.registry)

    # --- FAC-E1–E4 ---

    def test_fac_e1_rejects_missing_source_reference(self) -> None:
        evidence = self.registry.add_evidence(
            _valid_evidence(source_reference="", evidence_id="evid_e1_missing")
        )
        status = self.registry.get_status(evidence.evidence_id)
        report = self.registry.get_validation_report(evidence.evidence_id)
        assert report is not None
        self.assertEqual(status, ConstitutionalStatus.REJECTED)
        self.assertFalse(report.is_valid)
        self.assertTrue(
            any("FAC-E1" in check for check in report.failed_checks),
            report.failed_checks,
        )

    def test_fac_e1_rejects_invalid_source_reference(self) -> None:
        evidence = self.registry.add_evidence(
            _valid_evidence(source_reference="invalid", evidence_id="evid_e1_invalid")
        )
        report = self.registry.get_validation_report(evidence.evidence_id)
        assert report is not None
        self.assertEqual(
            self.registry.get_status(evidence.evidence_id),
            ConstitutionalStatus.REJECTED,
        )
        self.assertTrue(any("FAC-E1" in c for c in report.failed_checks))

    def test_fac_e2_rejects_claimed_hash_mismatch(self) -> None:
        evidence = self.registry.add_evidence(
            _valid_evidence(
                evidence_id="evid_e2_claim",
                claimed_sha256="0" * 64,
            )
        )
        report = self.registry.get_validation_report(evidence.evidence_id)
        assert report is not None
        self.assertEqual(
            self.registry.get_status(evidence.evidence_id),
            ConstitutionalStatus.REJECTED,
        )
        self.assertTrue(any("FAC-E2" in c for c in report.failed_checks))

    def test_fac_e2_detects_post_store_tampering(self) -> None:
        evidence = self.registry.add_evidence(
            _valid_evidence(evidence_id="evid_e2_tamper")
        )
        self.assertEqual(
            self.registry.get_status(evidence.evidence_id),
            ConstitutionalStatus.ACCEPTED,
        )
        stored = self.registry.get_evidence(evidence.evidence_id)
        assert stored is not None
        stored.content["text"] = "TAMPERED"
        report = self.registry.revalidate_evidence(evidence.evidence_id)
        self.assertFalse(report.is_valid)
        self.assertTrue(any("FAC-E2" in c for c in report.failed_checks))
        self.assertEqual(
            self.registry.get_status(evidence.evidence_id),
            ConstitutionalStatus.REJECTED,
        )

    def test_fac_e3_rejects_broken_provenance(self) -> None:
        evidence = self.registry.add_evidence(
            _valid_evidence(
                evidence_id="evid_e3_break",
                provenance_chain=["abc123", "BREAK"],
            )
        )
        report = self.registry.get_validation_report(evidence.evidence_id)
        assert report is not None
        self.assertEqual(
            self.registry.get_status(evidence.evidence_id),
            ConstitutionalStatus.REJECTED,
        )
        self.assertTrue(any("FAC-E3" in c for c in report.failed_checks))

    def test_fac_e3_rejects_empty_provenance_entry(self) -> None:
        evidence = self.registry.add_evidence(
            _valid_evidence(
                evidence_id="evid_e3_empty",
                provenance_chain=["ok_hash", ""],
            )
        )
        report = self.registry.get_validation_report(evidence.evidence_id)
        assert report is not None
        self.assertTrue(any("FAC-E3" in c for c in report.failed_checks))

    def test_fac_e4_rejects_forbidden_tags(self) -> None:
        evidence = self.registry.add_evidence(
            _valid_evidence(
                evidence_id="evid_e4_tag",
                constitutional_tags=["UNCONSTITUTIONAL"],
            )
        )
        report = self.registry.get_validation_report(evidence.evidence_id)
        assert report is not None
        self.assertEqual(
            self.registry.get_status(evidence.evidence_id),
            ConstitutionalStatus.REJECTED,
        )
        self.assertTrue(any("FAC-E4" in c for c in report.failed_checks))

    def test_fac_e4_rejects_empty_submitted_by(self) -> None:
        evidence = self.registry.add_evidence(
            _valid_evidence(evidence_id="evid_e4_actor", submitted_by="  ")
        )
        report = self.registry.get_validation_report(evidence.evidence_id)
        assert report is not None
        self.assertTrue(any("FAC-E4" in c for c in report.failed_checks))

    def test_fac_e_accepts_valid_evidence(self) -> None:
        evidence = self.registry.add_evidence(
            _valid_evidence(evidence_id="evid_ok_001")
        )
        report = self.registry.get_validation_report(evidence.evidence_id)
        assert report is not None
        self.assertEqual(
            self.registry.get_status(evidence.evidence_id),
            ConstitutionalStatus.ACCEPTED,
        )
        self.assertTrue(report.is_valid)
        self.assertEqual(report.failed_checks, [])
        self.assertTrue(len(evidence.sha256_hash) == 64)

    # --- FAC-V1–V3 (vertical slice) ---

    def test_fac_v1_coverage_insufficient_evidence(self) -> None:
        result = self.registry.validate_reconstruction("recon_empty")
        self.assertFalse(result.is_valid)
        self.assertTrue(any("FAC-V1" in c for c in result.failed_checks))

    def test_fac_v2_consistency(self) -> None:
        result = self.registry.validate_reconstruction("recon_inconsistent")
        self.assertFalse(result.is_valid)
        self.assertTrue(any("FAC-V2" in c for c in result.failed_checks))

    def test_fac_v3_drift_control(self) -> None:
        result = self.registry.validate_reconstruction("recon_drift")
        self.assertFalse(result.is_valid)
        self.assertTrue(any("FAC-V3" in c for c in result.failed_checks))

    def test_fac_v4_alignment(self) -> None:
        result = self.registry.validate_reconstruction("recon_align")
        self.assertFalse(result.is_valid)
        self.assertTrue(any("FAC-V4" in c for c in result.failed_checks))

    def test_fac_v5_governance_fit(self) -> None:
        result = self.registry.validate_reconstruction("recon_scope")
        self.assertFalse(result.is_valid)
        self.assertTrue(any("FAC-V5" in c for c in result.failed_checks))

    # --- FRA-01–04 ---

    def test_fra_01_stage_completion(self) -> None:
        corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
        evidence_ids = [
            e["evidence_id"]
            for lang in corpus["languages"]
            for period in lang["periods"]
            if period["name"] == "Phase I"
            for e in period["evidence"]
        ]
        result = self.fra.reconstruct_language("Mythar", "Phase I", evidence_ids)
        self.assertEqual(result.get("status"), "COMPLETED", result)
        self.assertEqual(result.get("fra_stage"), "ARCHIVE")
        self.assertEqual(len(result.get("stages_completed") or []), 10)

    def test_fra_02_evidence_constrained_iteration(self) -> None:
        result = self.fra.reconstruct_language("Mythar", "Phase I", [])
        self.assertNotEqual(result.get("status"), "COMPLETED")

    def test_fra_03_drift_detection(self) -> None:
        result = self.fra.reconstruct_language(
            "Mythar", "Phase I", ["evid_myt_001", "evid_myt_002"]
        )
        self.assertIn("drift", result.get("metrics", {}))

    def test_fra_04_progressive_refinement(self) -> None:
        result = self.fra.reconstruct_language(
            "Mythar", "Phase II", ["evid_myt_101", "evid_myt_102"]
        )
        self.assertTrue(
            result.get("refinement_halted") or result.get("quality_improved"),
            result,
        )

    # --- AI-01–04 ---

    def test_ai_01_evidence_anchoring(self) -> None:
        with self.assertRaises(ValueError):
            self.ai_agent.predict_proto_forms({"lexical_clusters": [], "cognate_groups": []})

    def test_ai_02_cognate_detection(self) -> None:
        seeded = seed_registry_from_corpus(
            self.registry, evidence_ids=["evid_myt_002", "evid_rel_001"]
        )
        analysis = self.ai_agent.analyze_evidence_patterns(seeded)
        groups = analysis.get("cognate_groups", [])
        self.assertTrue(groups)

    def test_ai_03_phonological_evolution(self) -> None:
        seeded = seed_registry_from_corpus(
            self.registry,
            evidence_ids=["evid_myt_002", "evid_rel_001", "evid_myt_102"],
        )
        analysis = self.ai_agent.analyze_evidence_patterns(seeded)
        shifts = analysis.get("phonological_shifts", [])
        self.assertTrue(shifts)

    def test_ai_04_constitutional_validation(self) -> None:
        seeded = seed_registry_from_corpus(
            self.registry, evidence_ids=["evid_myt_001", "evid_myt_002"]
        )
        analysis = self.ai_agent.analyze_evidence_patterns(seeded)
        hypotheses = self.ai_agent.predict_proto_forms(analysis)
        proto = hypotheses["hypotheses"][0]
        self.registry.register_reconstruction(
            proto["id"],
            evidence_ids=[e.evidence_id for e in seeded],
            proto_model={"primary": proto},
            metrics={"drift": 0.1, "consistency": 0.9},
            constraints={"evidence_min_count": 1, "drift_threshold": 0.6},
        )
        refined = self.ai_agent.refine_reconstruction(proto, analysis, 1)
        self.assertIn("constitutional_validation", refined)
        self.assertIsNotNone(refined["constitutional_validation"])

    # --- CIH-01–05 ---

    def test_cih_01_project_registration(self) -> None:
        result = self.cih.approve_reconstruction_project(
            {"project_id": "proj_gate_001", "spec": {"target_language": "Mythar"}}
        )
        self.assertEqual(result.get("status"), "UNDER_REVIEW")

    def test_cih_02_evidence_baseline_blocks_rejected(self) -> None:
        self.registry.add_evidence(
            _valid_evidence(evidence_id="evid_rej", source_reference="")
        )
        result = self.cih.approve_reconstruction_project(
            {
                "project_id": "proj_gate_002",
                "spec": {
                    "target_language": "Mythar",
                    "time_period": "Phase I",
                    "evidence_sources": ["evid_rej"],
                },
            }
        )
        self.assertNotEqual(result.get("status"), "APPROVED")

    def test_cih_03_architecture_review(self) -> None:
        result = self.cih.approve_reconstruction_project(
            {"project_id": "proj_gate_003", "spec": {}}
        )
        self.assertIn(result.get("status"), {"REJECTED", "REQUEST_CHANGES"})

    def test_cih_04_certificate_issuance(self) -> None:
        self.registry.add_evidence(_valid_evidence(evidence_id="evid_ok_001"))
        result = self.cih.approve_reconstruction_project(
            {
                "project_id": "proj_gate_004",
                "spec": {
                    "target_language": "Mythar",
                    "time_period": "Phase I",
                    "evidence_sources": ["evid_ok_001"],
                },
            }
        )
        self.assertEqual(result.get("status"), "APPROVED", result)
        self.assertTrue(result.get("certificate_id"))
        cert = self.cih.get_certificate(result["certificate_id"])
        assert cert is not None
        self.assertEqual(cert["subject"]["project_id"], "proj_gate_004")

    def test_cih_05_governance_trace(self) -> None:
        result = self.cih.approve_reconstruction_project(
            {"project_id": "proj_gate_005", "spec": {"target_language": "Mythar"}}
        )
        self.assertIn("trace_id", result)
        self.assertIn("events", result.get("governance_trace", {}))
        self.assertGreaterEqual(len(result["governance_trace"]["events"]), 1)


if __name__ == "__main__":
    unittest.main()
