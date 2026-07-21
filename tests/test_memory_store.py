"""Tests for MemoryStore persistence backend."""

from __future__ import annotations

import unittest
from datetime import UTC, datetime

from sre.evidence.models import (
    ConstitutionalStatus,
    ConstitutionalValidationResult,
    EvidenceType,
    LinguisticEvidence,
)
from sre.storage.memory_store import MemoryStore


class TestMemoryStore(unittest.TestCase):
    def setUp(self) -> None:
        self.store = MemoryStore()
        self.evidence = LinguisticEvidence(
            evidence_id="ev_mem_001",
            evidence_type=EvidenceType.INSCRIPTION,
            source_reference="Memory test",
            content={"text": "hello"},
            created_at=datetime.now(UTC),
            submitted_by="tester",
            sha256_hash="a" * 64,
            provenance_chain=["hash1"],
            constitutional_tags=["FAC-E"],
        )
        self.status = ConstitutionalStatus.ACCEPTED
        self.validation = ConstitutionalValidationResult(
            evidence_id="ev_mem_001",
            is_valid=True,
            failed_checks=[],
            report={"key": "value"},
            validated_at=datetime.now(UTC),
        )

    def test_save_and_load_evidence(self) -> None:
        self.store.save_evidence(self.evidence, self.status, self.validation)
        loaded = self.store.load_evidence()
        self.assertEqual(len(loaded), 1)
        ev, st, vl = loaded[0]
        self.assertEqual(ev.evidence_id, "ev_mem_001")
        self.assertEqual(st, ConstitutionalStatus.ACCEPTED)
        self.assertTrue(vl.is_valid)

    def test_save_evidence_overwrite(self) -> None:
        self.store.save_evidence(self.evidence, self.status, self.validation)
        updated_status = ConstitutionalStatus.REJECTED
        updated_val = ConstitutionalValidationResult(
            evidence_id="ev_mem_001",
            is_valid=False,
            failed_checks=["FAC-E1"],
            report={},
            validated_at=datetime.now(UTC),
        )
        self.store.save_evidence(self.evidence, updated_status, updated_val)
        loaded = self.store.load_evidence()
        self.assertEqual(len(loaded), 1)
        _, st, vl = loaded[0]
        self.assertEqual(st, ConstitutionalStatus.REJECTED)
        self.assertFalse(vl.is_valid)

    def test_load_evidence_empty(self) -> None:
        loaded = self.store.load_evidence()
        self.assertEqual(loaded, [])

    def test_reconstruction_meta_roundtrip(self) -> None:
        self.store.save_reconstruction_meta("recon_001", {"status": "COMPLETED"})
        result = self.store.load_reconstruction_meta("recon_001")
        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "COMPLETED")

    def test_reconstruction_meta_missing(self) -> None:
        result = self.store.load_reconstruction_meta("nonexistent")
        self.assertIsNone(result)

    def test_load_all_reconstruction_meta(self) -> None:
        self.store.save_reconstruction_meta("r1", {"a": 1})
        self.store.save_reconstruction_meta("r2", {"b": 2})
        all_meta = self.store.load_all_reconstruction_meta()
        self.assertEqual(len(all_meta), 2)
        self.assertIn("r1", all_meta)
        self.assertIn("r2", all_meta)

    def test_reconstruction_result_roundtrip(self) -> None:
        self.store.save_reconstruction_result("recon_001", {"drift": 0.2})
        result = self.store.load_reconstruction_result("recon_001")
        self.assertIsNotNone(result)
        self.assertEqual(result["drift"], 0.2)

    def test_reconstruction_result_missing(self) -> None:
        result = self.store.load_reconstruction_result("nonexistent")
        self.assertIsNone(result)

    def test_load_all_reconstruction_results(self) -> None:
        self.store.save_reconstruction_result("r1", {"x": 10})
        self.store.save_reconstruction_result("r2", {"y": 20})
        all_results = self.store.load_all_reconstruction_results()
        self.assertEqual(len(all_results), 2)

    def test_returns_copies_not_references(self) -> None:
        self.store.save_reconstruction_meta("recon_001", {"val": "original"})
        retrieved = self.store.load_reconstruction_meta("recon_001")
        retrieved["val"] = "mutated"
        retrieved2 = self.store.load_reconstruction_meta("recon_001")
        self.assertEqual(retrieved2["val"], "original")


if __name__ == "__main__":
    unittest.main()
