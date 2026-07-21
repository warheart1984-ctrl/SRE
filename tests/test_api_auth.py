"""API key authentication tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

try:
    from fastapi.testclient import TestClient
except ImportError:  # pragma: no cover
    TestClient = None  # type: ignore[misc, assignment]

from sre.api.app import create_app
from sre.api.auth import ApiKeyMiddleware
from sre.api.state import AppState, reset_app_state


@unittest.skipIf(TestClient is None, "install sre[api] for HTTP tests")
class TestApiAuth(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        store_path = Path(self.tmp.name) / "ledger.jsonl"
        self.state = AppState(cel_store_path=store_path, dantomax_signing_key="auth-test")
        reset_app_state(self.state)

    def tearDown(self) -> None:
        reset_app_state(None)
        self.tmp.cleanup()

    def test_auth_disabled_by_default(self) -> None:
        client = TestClient(create_app(self.state))
        resp = client.get("/api/v1/explorer/conformance")
        self.assertEqual(resp.status_code, 200)

    def test_auth_required_rejects_missing_key(self) -> None:
        app = create_app(self.state)
        app.user_middleware = [
            m for m in app.user_middleware if getattr(m, "cls", None) is not ApiKeyMiddleware
        ]
        app.add_middleware(ApiKeyMiddleware, allowed_keys=frozenset({"secret-key"}), required=True)
        client = TestClient(app)
        denied = client.get("/api/v1/explorer/conformance")
        self.assertEqual(denied.status_code, 401)
        ok = client.get(
            "/api/v1/explorer/conformance",
            headers={"X-API-Key": "secret-key"},
        )
        self.assertEqual(ok.status_code, 200)
        health = client.get("/health")
        self.assertEqual(health.status_code, 200)


if __name__ == "__main__":
    unittest.main()
