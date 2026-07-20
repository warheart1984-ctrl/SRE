"""CEL JSONL persistence tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sre.evidence.cel import CELEntryType, ConstitutionalEvidenceLedger
from sre.evidence.cel_store import CELStore


class TestCELStore(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "ledger.jsonl"
        self.store = CELStore(self.path)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_append_and_replay(self) -> None:
        ledger = ConstitutionalEvidenceLedger(store=self.store)
        ledger.record_hypothesis("recon_a", {"proto_form": "*test-"})
        ledger.record_validation("recon_a", {"is_valid": True, "failed_checks": []})

        self.assertTrue(self.store.exists())
        self.assertEqual(self.store.entry_count(), 2)

        reloaded = ConstitutionalEvidenceLedger.load_from_store(self.store)
        self.assertEqual(reloaded.cel_length, 2)
        self.assertTrue(reloaded.verify_integrity()["ok"])
        entries = reloaded.query_by_type(CELEntryType.HYPOTHESIS)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].subject_id, "recon_a")

    def test_persistence_survives_reload(self) -> None:
        ledger1 = ConstitutionalEvidenceLedger(store=self.store)
        ledger1.record_evidence(
            "evid_x",
            sha256_hash="abc",
            validation_report={"failed_checks": []},
        )
        head1 = ledger1.cel_head

        ledger2 = ConstitutionalEvidenceLedger.load_from_store(self.store)
        self.assertEqual(ledger2.cel_head, head1)
        self.assertEqual(ledger2.fabric_root_hash, ledger1.fabric_root_hash)

    def test_empty_store(self) -> None:
        self.assertFalse(self.store.exists())
        self.assertEqual(self.store.entry_count(), 0)
        ledger = ConstitutionalEvidenceLedger.load_from_store(self.store)
        self.assertEqual(ledger.cel_length, 0)


if __name__ == "__main__":
    unittest.main()
