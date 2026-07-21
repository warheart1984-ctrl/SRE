"""Tests for CEL API handlers."""

from __future__ import annotations

import unittest

from sre.api.handlers.cel import get_cel_head, get_cel_lineage, list_cel_entries
from sre.evidence.cel import CELEntryType, ConstitutionalEvidenceLedger
from sre.evidence.dantomax_client import DantomaxClient


class TestCELApiHandlers(unittest.TestCase):
    def setUp(self) -> None:
        self.dmx = DantomaxClient(signing_key="test-cel-handlers")
        self.cel = ConstitutionalEvidenceLedger(dantomax=self.dmx)
        self.cel.append(CELEntryType.EVIDENCE, "ev_001", {"text": "a"})
        self.cel.append(CELEntryType.ATTESTATION, "att_001", {"form": "x"})
        self.cel.append(CELEntryType.GOVERNANCE, "gov_001", {"decision": "approved"})

    def test_get_cel_head(self) -> None:
        result = get_cel_head(self.cel)
        self.assertEqual(result["version"], "1.0")
        self.assertEqual(result["length"], 3)
        self.assertIn("integrity", result)
        self.assertTrue(result["integrity"]["ok"])

    def test_list_cel_entries_all(self) -> None:
        result = list_cel_entries(self.cel)
        self.assertEqual(result["total"], 3)
        self.assertEqual(len(result["entries"]), 3)
        self.assertIn("fabric_root_hash", result)

    def test_list_cel_entries_by_type(self) -> None:
        result = list_cel_entries(self.cel, entry_type="evidence")
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["entries"][0]["entry_type"], "evidence")

    def test_list_cel_entries_by_subject(self) -> None:
        result = list_cel_entries(self.cel, subject_id="att_001")
        self.assertEqual(result["total"], 1)

    def test_list_cel_entries_pagination(self) -> None:
        result = list_cel_entries(self.cel, limit=1, offset=0)
        self.assertEqual(len(result["entries"]), 1)
        self.assertEqual(result["limit"], 1)
        self.assertEqual(result["offset"], 0)
        self.assertEqual(result["total"], 3)

    def test_list_cel_entries_invalid_type(self) -> None:
        result = list_cel_entries(self.cel, entry_type="invalid")
        self.assertEqual(result["total"], 0)
        self.assertIn("error", result)

    def test_get_cel_lineage(self) -> None:
        self.cel.append(CELEntryType.HYPOTHESIS, "recon_001", {"form": "*foo"})
        self.cel.append(CELEntryType.VALIDATION, "recon_001", {"valid": True})
        result = get_cel_lineage(self.cel, "recon_001")
        self.assertEqual(result["reconstruction_id"], "recon_001")
        self.assertIn("hypothesis", result["entries_by_type"])
        self.assertIn("human_readable", result)
        self.assertGreaterEqual(result["entry_count"], 2)

    def test_get_cel_lineage_empty(self) -> None:
        result = get_cel_lineage(self.cel, "nonexistent")
        self.assertEqual(result["reconstruction_id"], "nonexistent")
        self.assertEqual(result["entry_count"], 0)

    def test_list_cel_entries_clamps_limit(self) -> None:
        result = list_cel_entries(self.cel, limit=0)
        self.assertEqual(result["limit"], 1)

    def test_list_cel_entries_clamps_limit_high(self) -> None:
        result = list_cel_entries(self.cel, limit=1000)
        self.assertEqual(result["limit"], 500)


if __name__ == "__main__":
    unittest.main()
