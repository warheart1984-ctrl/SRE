"""SRE v1.0 API — evidence, FRA, CIH POST integration tests."""

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
from sre.corpus.loader import seed_registry_from_corpus


@unittest.skipIf(TestClient is None, "install sre[api] for HTTP tests")
class TestAPIv1Workflow(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        store_path = Path(self.tmp.name) / "ledger.jsonl"
        state = AppState(cel_store_path=store_path, dantomax_signing_key="v1-test")
        seed_registry_from_corpus(
            state.registry,
            path="mythar",
            evidence_ids=["evid_myt_001", "evid_myt_002", "evid_rel_001"],
        )
        reset_app_state(state)
        self.client = TestClient(create_app(state))
        self.state = state

    def tearDown(self) -> None:
        reset_app_state(None)
        self.tmp.cleanup()

    def test_post_evidence(self) -> None:
        resp = self.client.post(
            "/api/v1/evidence",
            json={
                "evidence_id": "evid_api_post",
                "evidence_type": "inscription",
                "source_reference": "API test corpus",
                "content": {"text": "demo"},
                "submitted_by": "api_tester",
            },
        )
        self.assertEqual(resp.status_code, 201)
        body = resp.json()
        self.assertEqual(body["evidence_id"], "evid_api_post")
        self.assertEqual(body["status"], "accepted")

    def test_post_reconstruction_mythar(self) -> None:
        resp = self.client.post(
            "/api/v1/reconstruction",
            json={
                "target_language": "Mythar",
                "time_period": "Phase I",
                "evidence_sources": ["evid_myt_001", "evid_myt_002", "evid_rel_001"],
                "corpus": "mythar",
            },
        )
        self.assertEqual(resp.status_code, 202)
        result = resp.json()
        self.assertEqual(result["status"], "COMPLETED")
        recon_id = result["reconstruction_id"]
        assert recon_id

        get_resp = self.client.get(f"/api/v1/reconstruction/{recon_id}")
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(get_resp.json()["reconstruction_id"], recon_id)

        lineage = self.client.get(f"/api/v1/cel/lineage/{recon_id}")
        self.assertEqual(lineage.status_code, 200)
        self.assertIn("hypothesis", lineage.json().get("entries_by_type", {}))

    def test_cih_approve_after_reconstruction(self) -> None:
        recon = self.client.post(
            "/api/v1/reconstruction",
            json={
                "target_language": "Mythar",
                "time_period": "Phase I",
                "evidence_sources": ["evid_myt_001", "evid_myt_002"],
                "corpus": "mythar",
            },
        ).json()
        cert = recon.get("certificate") or {}

        reg = self.client.post(
            "/api/v1/cih/projects",
            json={
                "project_id": "proj_api_v1",
                "spec": {
                    "target_language": "Mythar",
                    "time_period": "Phase I",
                    "evidence_sources": ["evid_myt_001", "evid_myt_002"],
                    "reconstruction_id": recon.get("reconstruction_id"),
                    "corpus_hash": cert.get("corpus_hash"),
                    "validation_summary": cert.get("validation_summary"),
                },
            },
        )
        self.assertIn(reg.status_code, {201, 200})

        approval = self.client.post(
            "/api/v1/cih/projects/proj_api_v1/approve",
            json={
                "spec": {
                    "target_language": "Mythar",
                    "time_period": "Phase I",
                    "evidence_sources": ["evid_myt_001", "evid_myt_002"],
                    "reconstruction_id": recon.get("reconstruction_id"),
                },
            },
        )
        self.assertEqual(approval.status_code, 200)
        body = approval.json()
        self.assertEqual(body["status"], "APPROVED")
        cert_id = body.get("certificate_id")
        assert cert_id

        cert_resp = self.client.get(f"/api/v1/certificates/{cert_id}")
        self.assertEqual(cert_resp.status_code, 200)
        ledger_id = cert_resp.json()["signatures"]["ledger_entry_id"]
        self.assertTrue(ledger_id.startswith("cel_certification_"))

    def test_explorer_ui(self) -> None:
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Sovereign Ledger Explorer", resp.text)
        self.assertIn("Conformance dashboard", resp.text)

    def test_explorer_conformance_summary(self) -> None:
        resp = self.client.get("/api/v1/explorer/conformance")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["status"], "profiled")
        self.assertEqual(body["profile_id"], "sre-cih-conformance-v1")
        self.assertGreaterEqual(body["counts"]["conformance_gates"], 11)
        self.assertTrue(any(g["gate_id"] == "CIH-01" for g in body["gates"]))

    def test_health_signing_mode(self) -> None:
        resp = self.client.get("/health")
        self.assertEqual(resp.json()["signing_mode"], "local_hmac")


if __name__ == "__main__":
    unittest.main()
