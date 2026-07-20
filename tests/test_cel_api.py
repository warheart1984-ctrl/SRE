"""CEL + Explorer HTTP API tests (requires optional [api] deps)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

try:
    from fastapi.testclient import TestClient
except ImportError:  # pragma: no cover
    TestClient = None  # type: ignore[misc, assignment]

from sre.api.app import create_app
from sre.api.state import AppState, reset_app_state


@unittest.skipIf(TestClient is None, "install sre[api] for HTTP tests")
class TestCELAPI(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        store_path = Path(self.tmp.name) / "ledger.jsonl"
        state = AppState(cel_store_path=store_path, dantomax_signing_key="api-test")
        cel = state.cel
        cel.record_hypothesis("recon_api", {"proto_form": "*api-"})
        cel.record_validation("recon_api", {"is_valid": True, "failed_checks": []})
        reset_app_state(state)
        self.client = TestClient(create_app(state))

    def tearDown(self) -> None:
        reset_app_state(None)
        self.tmp.cleanup()

    def test_health(self) -> None:
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "ok")

    def test_cel_head(self) -> None:
        resp = self.client.get("/api/v1/cel/head")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertGreaterEqual(body["length"], 2)
        self.assertIn("fabric_root_hash", body)
        self.assertTrue(body["integrity"]["ok"])

    def test_cel_entries(self) -> None:
        resp = self.client.get("/api/v1/cel/entries", params={"entry_type": "hypothesis"})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertGreaterEqual(body["total"], 1)

    def test_cel_lineage(self) -> None:
        resp = self.client.get("/api/v1/cel/lineage/recon_api")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["reconstruction_id"], "recon_api")
        self.assertIn("hypothesis", body["entries_by_type"])

    def test_explorer_fabric(self) -> None:
        resp = self.client.get("/api/v1/explorer/fabric")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("cel", resp.json())

    def test_explorer_reconstruction(self) -> None:
        resp = self.client.get("/api/v1/explorer/reconstruction/recon_api")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["reconstruction_id"], "recon_api")

    def test_explorer_entry_not_found(self) -> None:
        resp = self.client.get("/api/v1/explorer/entry/cel_missing_000000")
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
