#!/usr/bin/env python3
"""Minimal KMS signing server for SRE_KMS_MODE=remote development."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


def _sign(message: str, key: bytes) -> str:
    return hmac.new(key, message.encode("utf-8"), hashlib.sha256).hexdigest()


class KmsHandler(BaseHTTPRequestHandler):
    signing_key = b"sre-kms-dev-key"

    def do_POST(self) -> None:  # noqa: N802
        if self.path.rstrip("/") not in {"/v1/sign", "/sign"}:
            self.send_error(404, "not found")
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self.send_error(400, "invalid json")
            return
        message = payload.get("message")
        if not isinstance(message, str) or not message:
            self.send_error(400, "message required")
            return
        signature = _sign(message, self.signing_key)
        body = json.dumps({"signature": signature}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


def main() -> None:
    host = os.environ.get("SRE_KMS_HOST", "127.0.0.1")
    port = int(os.environ.get("SRE_KMS_PORT", "8020"))
    key = os.environ.get("SRE_KMS_DEV_KEY", "sre-kms-dev-key").encode("utf-8")
    KmsHandler.signing_key = key
    server = HTTPServer((host, port), KmsHandler)
    print(f"KMS dev server listening on http://{host}:{port}/v1/sign")
    server.serve_forever()


if __name__ == "__main__":
    main()
