"""Dantomax signer backend tests."""

from __future__ import annotations

import hashlib
import json
import unittest
from unittest import mock

from sre.evidence.dantomax_client import DantomaxClient
from sre.evidence.dantomax_signer import LocalHmacSigner, RemoteKmsSigner


class TestLocalHmacSigner(unittest.TestCase):
    def test_deterministic(self) -> None:
        a = LocalHmacSigner("key-a")
        b = LocalHmacSigner("key-a")
        msg = "evid|hash|ts|prev|0"
        self.assertEqual(a.sign(msg), b.sign(msg))
        self.assertNotEqual(a.sign(msg), LocalHmacSigner("key-b").sign(msg))

    def test_dantomax_uses_signer(self) -> None:
        client = DantomaxClient(signer=LocalHmacSigner("unit-test"))
        self.assertEqual(client.signing_mode, "local_hmac")
        client.register_evidence("e1", "a" * 64, {"failed_checks": []})
        self.assertTrue(client.verify_evidence("e1", "a" * 64)["is_verified"])


class TestRemoteKmsSigner(unittest.TestCase):
    def test_remote_kms_sign(self) -> None:
        message = "test-payload"

        def fake_urlopen(req, timeout=0):  # noqa: ARG001
            body = json.loads(req.data.decode())
            sig = hashlib.sha256(body["message"].encode()).hexdigest()
            return mock.Mock(
                read=lambda: json.dumps({"signature": sig}).encode(),
                __enter__=lambda s: s,
                __exit__=lambda *a: None,
            )

        signer = RemoteKmsSigner("http://kms.local/sign")
        with mock.patch("sre.evidence.dantomax_signer.urllib.request.urlopen", fake_urlopen):
            sig = signer.sign(message)
        self.assertEqual(len(sig), 64)

        client = DantomaxClient(signer=signer)
        self.assertEqual(client.signing_mode, "remote_kms")
        with mock.patch("sre.evidence.dantomax_signer.urllib.request.urlopen", fake_urlopen):
            receipt = client.register_evidence("e2", "b" * 64, {"failed_checks": []})
        self.assertIn("signature", receipt)


if __name__ == "__main__":
    unittest.main()
