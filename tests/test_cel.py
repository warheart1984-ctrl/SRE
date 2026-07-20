"""Constitutional Evidence Ledger (CEL) — charter promotion gates CEL-01..CEL-08."""

from __future__ import annotations

import unittest

from sre.ai.hlrm_agent import HLRMAIAgent
from sre.corpus.loader import seed_registry_from_corpus
from sre.evidence.cel import CELEntryType, ConstitutionalEvidenceLedger, CEL_VERSION
from sre.evidence.dantomax_client import DantomaxClient
from sre.evidence.registry import EvidenceRegistry
from sre.fra.reconstruction_engine import ChronologicalReconstruction
from sre.governance.cih_service import FAECLanguageReconstructionService


class TestCELIntegrity(unittest.TestCase):
    """CEL-01: append-only chain; verify_integrity passes."""

    def test_cel_integrity(self) -> None:
        cel = ConstitutionalEvidenceLedger()
        cel.record_evidence(
            "evid_test",
            sha256_hash="abc123",
            validation_report={"failed_checks": []},
        )
        cel.record_hypothesis("recon_test", {"proto_form": "*test-"})
        result = cel.verify_integrity()
        self.assertTrue(result["ok"])
        self.assertEqual(result["length"], 2)
        self.assertTrue(result["fabric_root_hash"])


class TestCELEvidenceRecord(unittest.TestCase):
    """CEL-02: evidence acceptance creates CEL entry."""

    def test_cel_evidence_record(self) -> None:
        dmx = DantomaxClient(signing_key="cel-test")
        registry = EvidenceRegistry(dantomax_client=dmx)
        assert registry.cel is not None
        seed_registry_from_corpus(
            registry,
            path="mythar",
            evidence_ids=["evid_myt_001"],
        )
        entries = registry.cel.query_by_type(CELEntryType.EVIDENCE)
        self.assertGreaterEqual(len(entries), 1)
        self.assertEqual(entries[0].subject_id, "evid_myt_001")


class TestCELAttestationRecord(unittest.TestCase):
    """CEL-03: attestation registration creates CEL entry."""

    def test_cel_attestation_record(self) -> None:
        dmx = DantomaxClient(signing_key="cel-attest")
        cel = ConstitutionalEvidenceLedger(dmx)
        receipt = dmx.register_attestation(
            {
                "attestation_id": "att_cel_demo",
                "language": "LAT",
                "normalized_form": "pater",
                "original_form": "pater",
                "gloss": "father",
                "grammatical_category": "noun",
                "source_id": "fortson2010",
                "source_title": "IE Language and Culture",
                "source_author": "Fortson",
                "publication_year": 2010,
                "page_or_entry": "§1",
                "evidence_class": "directly_attested",
                "confidence": 0.9,
            }
        )
        cel.record_attestation("att_cel_demo", receipt["attestation"], dantomax_receipt=receipt)
        entries = cel.query_by_type(CELEntryType.ATTESTATION)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].subject_id, "att_cel_demo")


class TestCELFRAIntegration(unittest.TestCase):
    """CEL-04: FRA pipeline creates correspondence + hypothesis entries."""

    def test_cel_fra_integration(self) -> None:
        dmx = DantomaxClient(signing_key="cel-fra")
        registry = EvidenceRegistry(dantomax_client=dmx)
        agent = HLRMAIAgent(registry)
        engine = ChronologicalReconstruction(
            registry,
            agent,
            corpus_path="ie",
            constraints={"require_attestation_lineage": False},
        )
        ids = [
            "evid_lat_pater",
            "evid_spa_padre",
            "evid_fra_pere",
            "evid_skt_pitar",
        ]
        result = engine.reconstruct_language(
            "Proto-Indo-European",
            "Classical→Modern",
            ids,
        )
        self.assertEqual(result["status"], "COMPLETED")
        cel = registry.cel
        assert cel is not None
        corr = cel.query_by_type(CELEntryType.CORRESPONDENCE)
        hyps = cel.query_by_type(CELEntryType.HYPOTHESIS)
        self.assertGreater(len(corr), 0)
        self.assertGreater(len(hyps), 0)


class TestCELValidationRecord(unittest.TestCase):
    """CEL-05: FAC-V validation creates CEL entry."""

    def test_cel_validation_record(self) -> None:
        dmx = DantomaxClient(signing_key="cel-val")
        registry = EvidenceRegistry(dantomax_client=dmx)
        seed_registry_from_corpus(registry, path="mythar", evidence_ids=["evid_myt_001"])
        registry.register_reconstruction(
            "recon_cel_val",
            evidence_ids=["evid_myt_001"],
            metrics={"drift": 0.1, "consistency": 1.0, "aligned": True},
            alignment_ok=True,
        )
        registry.validate_reconstruction("recon_cel_val")
        cel = registry.cel
        assert cel is not None
        entries = cel.query_by_type(CELEntryType.VALIDATION)
        self.assertGreaterEqual(len(entries), 1)
        self.assertEqual(entries[-1].subject_id, "recon_cel_val")


class TestCELCertificationAnchor(unittest.TestCase):
    """CEL-06: CIH certificate anchored to real CEL entry."""

    def test_cel_certification_anchor(self) -> None:
        dmx = DantomaxClient(signing_key="cel-cert")
        registry = EvidenceRegistry(dantomax_client=dmx)
        seed_registry_from_corpus(
            registry,
            path="mythar",
            evidence_ids=["evid_myt_001", "evid_myt_002"],
        )
        cih = FAECLanguageReconstructionService(registry)
        approval = cih.approve_reconstruction_project(
            {
                "project_id": "proj_cel_cert",
                "spec": {
                    "target_language": "Mythar",
                    "time_period": "Phase I",
                    "evidence_sources": ["evid_myt_001", "evid_myt_002"],
                    "reconstruction_id": "recon_cel_cert",
                },
            }
        )
        self.assertEqual(approval["status"], "APPROVED")
        cert = approval.get("certificate") or {}
        ledger_id = cert.get("signatures", {}).get("ledger_entry_id", "")
        self.assertTrue(ledger_id.startswith("cel_certification_"))
        cel = registry.cel
        assert cel is not None
        entry = cel.get_entry(ledger_id)
        self.assertIsNotNone(entry)
        self.assertEqual(entry.entry_type, CELEntryType.CERTIFICATION)


class TestCELLineageQuery(unittest.TestCase):
    """CEL-07: lineage query returns constitutional path."""

    def test_cel_lineage_query(self) -> None:
        dmx = DantomaxClient(signing_key="cel-lineage")
        registry = EvidenceRegistry(dantomax_client=dmx)
        agent = HLRMAIAgent(registry)
        engine = ChronologicalReconstruction(
            registry,
            agent,
            corpus_path="mythar",
            constraints={"require_attestation_lineage": False},
        )
        result = engine.reconstruct_language(
            "Mythar",
            "Phase I",
            ["evid_myt_001", "evid_myt_002", "evid_rel_001"],
        )
        self.assertEqual(result["status"], "COMPLETED")
        recon_id = str(result["reconstruction_id"])
        cel = registry.cel
        assert cel is not None
        lineage = cel.query_lineage(recon_id)
        self.assertIn("validation", lineage.get("entries_by_type", {}))
        self.assertIn("hypothesis", lineage.get("entries_by_type", {}))
        self.assertGreater(lineage["entry_count"], 0)


class TestCELFabricRootOnCert(unittest.TestCase):
    """CEL-08: fabric_root_hash included in Sovereign Certificate."""

    def test_cel_fabric_root_on_cert(self) -> None:
        dmx = DantomaxClient(signing_key="cel-fabric")
        registry = EvidenceRegistry(dantomax_client=dmx)
        agent = HLRMAIAgent(registry)
        engine = ChronologicalReconstruction(
            registry,
            agent,
            corpus_path="mythar",
            constraints={"require_attestation_lineage": False},
        )
        result = engine.reconstruct_language(
            "Mythar",
            "Phase I",
            ["evid_myt_001", "evid_myt_002", "evid_rel_001"],
        )
        self.assertEqual(result["status"], "COMPLETED")
        cert = result.get("certificate") or {}
        self.assertIn("fabric_root_hash", cert)
        self.assertTrue(cert["fabric_root_hash"])
        cel = registry.cel
        assert cel is not None
        self.assertEqual(cert["fabric_root_hash"], cel.fabric_root_hash)


class TestCELVersion(unittest.TestCase):
    def test_cel_version_constant(self) -> None:
        self.assertEqual(CEL_VERSION, "1.0")


if __name__ == "__main__":
    unittest.main()
