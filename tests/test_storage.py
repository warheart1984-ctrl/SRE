"""Durable SQLite store tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sre.evidence.dantomax_client import DantomaxClient
from sre.evidence.registry import EvidenceRegistry
from sre.storage.reconstruction_cache import ReconstructionCache
from sre.storage.sqlite_store import SqliteStore


class TestSqliteStore(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "sre.db"
        self.store = SqliteStore(self.db_path)

    def tearDown(self) -> None:
        self.store.close()
        self.tmp.cleanup()

    def test_evidence_roundtrip(self) -> None:
        dmx = DantomaxClient(signing_key="sqlite-test")
        registry = EvidenceRegistry(dantomax_client=dmx, persist_store=self.store)
        registry.add_evidence(
            {
                "evidence_id": "evid_sqlite_001",
                "evidence_type": "inscription",
                "source_reference": "SQLite durability test",
                "content": {"text": "persist me"},
                "submitted_by": "tester",
            }
        )
        reloaded = EvidenceRegistry(dantomax_client=dmx, persist_store=self.store)
        ev = reloaded.get_evidence("evid_sqlite_001")
        self.assertIsNotNone(ev)
        assert ev is not None
        self.assertEqual(ev.content["text"], "persist me")

    def test_reconstruction_cache_persists(self) -> None:
        cache = ReconstructionCache(self.store)
        cache["recon_persist_1"] = {"reconstruction_id": "recon_persist_1", "status": "COMPLETED"}
        cache2 = ReconstructionCache(self.store)
        self.assertEqual(cache2.get("recon_persist_1")["status"], "COMPLETED")


if __name__ == "__main__":
    unittest.main()
