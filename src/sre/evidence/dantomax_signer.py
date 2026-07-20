"""Dantomax signing backends — local HMAC and remote KMS."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import urllib.error
import urllib.request
from typing import Protocol


class DantomaxSigner(Protocol):
    """Sign canonical Dantomax ledger payloads."""

    @property
    def mode(self) -> str:
        """Signer backend identifier (local_hmac, remote_kms, ...)."""

    def sign(self, message: str) -> str:
        """Return hex digest signature for message."""


class LocalHmacSigner:
    """Development / single-node HMAC-SHA256 signer."""

    def __init__(self, signing_key: str | bytes | None = None) -> None:
        if isinstance(signing_key, bytes):
            self._key = signing_key
        else:
            self._key = (signing_key or "sre-dantomax-dev-key").encode("utf-8")

    @property
    def mode(self) -> str:
        return "local_hmac"

    def sign(self, message: str) -> str:
        return hmac.new(self._key, message.encode("utf-8"), hashlib.sha256).hexdigest()


class RemoteKmsSigner:
    """
    Remote KMS signer — POST canonical message to a signing service.

    Expected request:  ``{"message": "<payload>"}``
    Expected response: ``{"signature": "<hex>"}``

    Environment:
    - ``SRE_KMS_URL`` — signing endpoint (required for remote mode)
    - ``SRE_KMS_AUTH`` — optional ``Authorization`` header value
      (e.g. ``Bearer <token>``)
    """

    def __init__(
        self,
        url: str,
        *,
        auth_header: str | None = None,
        timeout_s: float = 10.0,
    ) -> None:
        if not url.strip():
            raise ValueError("SRE_KMS_URL is required for remote KMS signing")
        self._url = url.strip()
        self._auth = auth_header
        self._timeout = timeout_s

    @property
    def mode(self) -> str:
        return "remote_kms"

    def sign(self, message: str) -> str:
        body = json.dumps({"message": message}).encode("utf-8")
        req = urllib.request.Request(
            self._url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        if self._auth:
            req.add_header("Authorization", self._auth)
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"KMS signing failed: {exc}") from exc
        signature = payload.get("signature")
        if not signature or not isinstance(signature, str):
            raise RuntimeError("KMS response missing signature field")
        return signature


def create_signer_from_env(
    signing_key: str | bytes | None = None,
) -> DantomaxSigner:
    """
    Factory: ``SRE_KMS_MODE=remote`` + ``SRE_KMS_URL`` → RemoteKmsSigner;
    otherwise LocalHmacSigner.
    """
    mode = os.environ.get("SRE_KMS_MODE", "local").strip().lower()
    if mode == "remote":
        url = os.environ.get("SRE_KMS_URL", "").strip()
        auth = os.environ.get("SRE_KMS_AUTH", "").strip() or None
        return RemoteKmsSigner(url, auth_header=auth)
    return LocalHmacSigner(signing_key)
