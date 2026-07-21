"""Mythar CEL binding after seed_registry."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sre.evidence.cel import ConstitutionalEvidenceLedger
from sre.evidence.dantomax_client import DantomaxClient
from sre.evidence.registry import EvidenceRegistry
from sre.mythar import MytharLexicon

ROOT = Path(__file__).resolve().parents[1]
LEX_PATH = ROOT / "data" / "mythar_lexicon_v01.json"


class TestMytharCelBinding(unittest.TestCase):
    def test_seed_binds_governance_when_cel_present(self) -> None:
        with tempfile.TemporaryDirectory():
            dmx = DantomaxClient(signing_key="mythar-bind-test")
            cel = ConstitutionalEvidenceLedger(dmx)
            registry = EvidenceRegistry(dantomax_client=dmx, cel=cel)
            lex = MytharLexicon(LEX_PATH)
            lex.seed_registry(registry)

            ev = registry.get_evidence("evid_myt_cluster_12")
            self.assertIsNotNone(ev)
            assert ev is not None
            meta = (ev.content or {}).get("metadata") or {}
            gov = meta.get("cra_governance") or {}
            lineage = gov.get("cel_lineage") or {}
            self.assertEqual(lineage.get("binding_status"), "bound")
            self.assertTrue(str(lineage.get("cel_entry_id") or "").startswith("cel_"))

            bound_count = 0
            for eid in ("evid_myt_root_ma", "evid_myt_cluster_95"):
                row = registry.get_evidence(eid)
                if row is None:
                    continue
                lineage = (
                    (row.content or {})
                    .get("metadata", {})
                    .get("cra_governance", {})
                    .get("cel_lineage", {})
                )
                if lineage.get("binding_status") == "bound":
                    bound_count += 1
            self.assertGreaterEqual(bound_count, 1)


if __name__ == "__main__":
    unittest.main()
