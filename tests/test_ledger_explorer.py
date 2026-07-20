"""Sovereign Ledger Explorer read model tests."""

from __future__ import annotations

import unittest

from sre.evidence.cel import ConstitutionalEvidenceLedger
from sre.evidence.dantomax_client import DantomaxClient
from sre.evidence.ledger_explorer import SovereignLedgerExplorer


class TestSovereignLedgerExplorer(unittest.TestCase):
    def setUp(self) -> None:
        self.dmx = DantomaxClient(signing_key="explorer-test")
        self.cel = ConstitutionalEvidenceLedger(dantomax=self.dmx)
        self.explorer = SovereignLedgerExplorer(self.cel, dantomax=self.dmx)

    def test_fabric_overview(self) -> None:
        self.cel.record_hypothesis("recon_exp", {"confidence": 0.8})
        overview = self.explorer.fabric_overview()
        self.assertIn("cel", overview)
        self.assertIn("dantomax", overview)
        self.assertEqual(overview["cel"]["length"], 1)

    def test_explore_reconstruction(self) -> None:
        self.cel.record_hypothesis("recon_exp", {"proto_form": "*exp-"})
        self.cel.record_validation("recon_exp", {"is_valid": True, "failed_checks": []})
        bundle = self.explorer.explore_reconstruction("recon_exp")
        self.assertEqual(bundle["entry_count"], 2)
        self.assertIn("lineage", bundle)
        self.assertIn("HYPOTHESIS", bundle["lineage"]["human_readable"])

    def test_explore_entry(self) -> None:
        entry = self.cel.record_hypothesis("recon_x", {"proto_form": "*x-"})
        detail = self.explorer.explore_entry(entry.cel_entry_id)
        assert detail is not None
        self.assertEqual(detail["entry"]["cel_entry_id"], entry.cel_entry_id)

    def test_search_entries(self) -> None:
        self.cel.record_hypothesis("recon_a", {})
        self.cel.record_validation("recon_b", {})
        page = self.explorer.search_entries(entry_type="hypothesis")
        self.assertEqual(page["total"], 1)


if __name__ == "__main__":
    unittest.main()
