"""Attestation ledger, lineage, correspondence search, and expanded IE tests."""

from __future__ import annotations

import unittest

from sre.ai.hlrm_agent import HLRMAIAgent
from sre.corpus.loader import list_evidence_ids, seed_registry_from_corpus
from sre.evidence.attestations import (
    EvidenceClass,
    HistoricalAttestation,
    compute_attestation_checksum,
    validate_attestation_fields,
)
from sre.evidence.dantomax_client import DantomaxClient
from sre.evidence.registry import EvidenceRegistry
from sre.fra.reconstruction_engine import ChronologicalReconstruction
from sre.governance.cih_service import FAECLanguageReconstructionService
from sre.linguistics.correspondence_engine import CorrespondenceEngine


def _base_att(**overrides):
    data = {
        "attestation_id": "att_test_pater",
        "language": "LAT",
        "normalized_form": "pater",
        "original_form": "pater",
        "gloss": "father",
        "grammatical_category": "noun",
        "source_id": "fortson2010",
        "source_title": "Indo-European Language and Culture",
        "source_author": "Benjamin W. Fortson IV",
        "publication_year": 2010,
        "page_or_entry": "§1.2",
        "evidence_class": EvidenceClass.DIRECTLY_ATTESTED.value,
        "confidence": 0.95,
    }
    data.update(overrides)
    return data


class TestAttestationValidation(unittest.TestCase):
    def test_missing_source_rejected(self) -> None:
        errors = validate_attestation_fields(_base_att(source_id="unknown"))
        self.assertTrue(any("unresolved_source" in e for e in errors))

    def test_malformed_citation(self) -> None:
        errors = validate_attestation_fields(
            _base_att(publication_year=999, source_author="")
        )
        self.assertTrue(any("malformed_citation" in e for e in errors))

    def test_checksum_integrity(self) -> None:
        att = HistoricalAttestation.from_dict(_base_att())
        self.assertEqual(att.checksum, compute_attestation_checksum(att))
        att.normalized_form = "tampered"
        self.assertNotEqual(att.checksum, compute_attestation_checksum(att))


class TestDantomaxAttestationLedger(unittest.TestCase):
    def setUp(self) -> None:
        self.dmx = DantomaxClient(signing_key="test-key")

    def test_register_and_duplicate(self) -> None:
        self.dmx.register_attestation(_base_att())
        with self.assertRaises(ValueError):
            self.dmx.register_attestation(_base_att())

    def test_supersession_not_silent_mutate(self) -> None:
        self.dmx.register_attestation(_base_att())
        old = self.dmx.get_attestation("att_test_pater")
        assert old is not None
        old_checksum = old.checksum
        result = self.dmx.supersede_attestation(
            "att_test_pater",
            _base_att(normalized_form="pater", notes="spelling normalization"),
            reason="normalize orthography",
        )
        new_id = result["attestation"]["attestation_id"]
        self.assertNotEqual(new_id, "att_test_pater")
        self.assertEqual(
            self.dmx.get_attestation("att_test_pater").status.value, "superseded"
        )
        # old checksum identity preserved on superseded record content fields
        self.assertEqual(
            self.dmx.get_attestation("att_test_pater").checksum, old_checksum
        )
        self.assertIsNotNone(self.dmx.get_attestation(new_id))

    def test_reject_evidence(self) -> None:
        self.dmx.register_attestation(_base_att(attestation_id="att_bad"))
        self.dmx.reject_attestation("att_bad", reason="spurious")
        bad = self.dmx.require_attested_sources(["att_bad"])
        self.assertTrue(any(x.startswith("rejected:") for x in bad))

    def test_correct_emits_governance(self) -> None:
        self.dmx.register_attestation(_base_att())
        self.dmx.correct_attestation(
            "att_test_pater",
            _base_att(notes="corrected page ref", page_or_entry="§1.3"),
            reason="page correction",
        )
        events = [e["event_type"] for e in self.dmx.governance_events()]
        self.assertIn("ATTESTATION_REGISTERED", events)
        self.assertIn("ATTESTATION_SUPERSEDED", events)
        self.assertIn("ATTESTATION_CORRECTED", events)
        self.assertTrue(
            any(r.event_type == "CORRECT" for r in self.dmx._chain)
        )

    def test_lineage_trace(self) -> None:
        self.dmx.register_attestation(_base_att())
        self.dmx.approve_attestation("att_test_pater")
        trace = self.dmx.build_lineage_trace(
            attestation_ids=["att_test_pater"],
            cognate_set_id="cognate_father",
            correspondence_ids=["corr_p_f"],
            sound_shift_ids=["grimm_p_f"],
            proto_form_id="pf_phter",
            certification_id="cert_demo",
        )
        self.assertEqual(
            trace["path"],
            [
                "attestation",
                "cognate_set",
                "correspondence",
                "sound_shift",
                "proto_form",
                "certification",
            ],
        )
        self.assertIn("→", trace["human_readable"])
        self.assertTrue(self.dmx.verify_ledger_integrity()["ok"])


class TestCorrespondenceEngine(unittest.TestCase):
    def test_competing_hypotheses_and_flags(self) -> None:
        engine = CorrespondenceEngine()
        hyps = engine.reconstruct_set(
            {"lat": "novem", "grc": "ennea", "skt": "nava", "lit": "devyni", "cu": "deveti"},
            flags_by_lang={
                "lit": ["analogy"],
                "cu": ["analogy"],
            },
            known_proto="newn",
        )
        self.assertGreaterEqual(len(hyps), 2)
        top = hyps[0]
        self.assertTrue(top.competing_hypotheses)
        flagged = any("analogy" in f for h in hyps for f in h.flags) or any(
            h.unresolved_conflicts for h in hyps
        )
        self.assertTrue(flagged)

    def test_leave_one_out(self) -> None:
        engine = CorrespondenceEngine()
        hyps = engine.reconstruct_set(
            {
                "lat": "pater",
                "grc": "pater",
                "skt": "pitar",
                "got": "fadar",
                "txb": "pacer",
            },
            known_proto="phter",
        )
        self.assertTrue(hyps)
        loo = hyps[0].leave_one_out
        self.assertTrue(loo.get("applicable"))
        self.assertTrue(loo.get("recovered"))


class TestExpandedIEPipeline(unittest.TestCase):
    def test_ie_expanded_through_cih(self) -> None:
        ids = [
            eid
            for eid in list_evidence_ids("ie-expanded")
            if any(
                x in eid
                for x in (
                    "_one",
                    "_two",
                    "_five",
                    "_father",
                    "_bear",
                    "_eat",
                    "_knee",
                    "_nine",
                    "_blood",
                    "rule_grimm",
                )
            )
        ]
        self.assertGreater(len(ids), 20)
        dmx = DantomaxClient()
        registry = EvidenceRegistry(dantomax_client=dmx)
        engine = ChronologicalReconstruction(
            registry,
            HLRMAIAgent(registry),
            corpus_path="ie-expanded",
            constraints={"require_attestation_lineage": True},
        )
        result = engine.reconstruct_language(
            "Proto-Indo-European", "IE expanded", ids
        )
        self.assertEqual(result.get("status"), "COMPLETED", result)
        self.assertEqual(result.get("fra_stage"), "ARCHIVE")
        self.assertEqual(len(result.get("stages_completed") or []), 10)
        cert = result.get("certificate") or {}
        self.assertTrue(cert.get("corpus_hash"))
        self.assertTrue(cert.get("attestation_root_hash"))
        self.assertTrue(cert.get("rule_set_version"))
        self.assertTrue(cert.get("reconstruction_ids"))
        self.assertTrue(cert.get("validation_summary"))
        self.assertTrue(result.get("human_lineage"))

        corr = result.get("correspondence_search") or {}
        self.assertTrue(corr.get("ambiguous_sets") or len(corr.get("hypotheses") or []) >= 2)
        self.assertTrue(corr.get("flagged_irregular"))
        self.assertTrue(corr.get("leave_one_out_examples"))

        att_ids = (result.get("governance") or {}).get("attestation_ids") or []
        cih = FAECLanguageReconstructionService(registry)
        approval = cih.approve_reconstruction_project(
            {
                "project_id": "proj_ie_expanded_test",
                "spec": {
                    "target_language": "Proto-Indo-European",
                    "time_period": "IE expanded",
                    "evidence_sources": ids,
                    "reconstruction_id": result.get("reconstruction_id"),
                    "attestation_ids": att_ids,
                    "require_attestation_lineage": True,
                    "corpus_hash": cert.get("corpus_hash"),
                    "attestation_root_hash": cert.get("attestation_root_hash"),
                    "rule_set_version": cert.get("rule_set_version"),
                    "validation_summary": cert.get("validation_summary"),
                },
            }
        )
        self.assertEqual(approval.get("status"), "APPROVED", approval)
        issued = approval.get("certificate") or {}
        self.assertTrue(issued.get("subject", {}).get("corpus_hash"))
        self.assertTrue(issued.get("subject", {}).get("attestation_root_hash"))

    def test_certify_rejects_missing_attestation_lineage(self) -> None:
        dmx = DantomaxClient()
        registry = EvidenceRegistry(dantomax_client=dmx)
        seeded = seed_registry_from_corpus(
            registry, path="mythar", evidence_ids=["evid_myt_001", "evid_myt_002"]
        )
        self.assertTrue(seeded)
        engine = ChronologicalReconstruction(
            registry,
            HLRMAIAgent(registry),
            corpus_path="mythar",
            constraints={"require_attestation_lineage": True},
        )
        result = engine.reconstruct_language(
            "Mythar", "Phase I", ["evid_myt_001", "evid_myt_002"]
        )
        # Mythar has no embedded attestations → cannot certify with lineage required
        self.assertNotEqual(result.get("status"), "COMPLETED")
        self.assertIn(result.get("fra_stage"), {"VALIDATE", "GOVERN", "ATTEST"})

    def test_mythar_still_works_without_dantomax(self) -> None:
        registry = EvidenceRegistry()
        engine = ChronologicalReconstruction(
            registry, HLRMAIAgent(registry), corpus_path="mythar"
        )
        result = engine.reconstruct_language(
            "Mythar", "Phase I", ["evid_myt_001", "evid_myt_002", "evid_rel_001"]
        )
        self.assertEqual(result.get("status"), "COMPLETED", result)
        self.assertEqual(len(result.get("stages_completed") or []), 10)


if __name__ == "__main__":
    unittest.main()
