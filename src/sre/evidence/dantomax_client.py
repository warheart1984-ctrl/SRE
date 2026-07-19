"""Dantomax integrity oracle — local hash-chained attestation ledger."""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class DantomaxRecord:
    """Single ledger attestation for an evidence hash."""

    dantomax_record_id: str
    evidence_id: str
    sha256_hash: str
    validation_summary: dict[str, Any]
    timestamp: str
    signature: str
    ledger_position: int
    prev_ledger_hash: str
    event_type: str = "REGISTER"
    ledger_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "dantomax_record_id": self.dantomax_record_id,
            "evidence_id": self.evidence_id,
            "sha256_hash": self.sha256_hash,
            "validation_summary": self.validation_summary,
            "timestamp": self.timestamp,
            "signature": self.signature,
            "ledger_position": self.ledger_position,
            "prev_ledger_hash": self.prev_ledger_hash,
            "event_type": self.event_type,
            "ledger_hash": self.ledger_hash,
        }


class DantomaxClient:
    """
    External integrity oracle for EvidenceRegistry.

    Local Substration implementation: append-only, HMAC-signed, hash-chained
    ledger. Suitable for constitutional attestations without an external network.
    Swap signing_key / backend for production KMS / remote Dantomax later.
    """

    GENESIS = "0" * 64

    def __init__(self, signing_key: str | bytes | None = None) -> None:
        if isinstance(signing_key, bytes):
            self._key = signing_key
        else:
            self._key = (signing_key or "sre-dantomax-dev-key").encode("utf-8")
        self._records: dict[str, list[DantomaxRecord]] = {}
        self._by_id: dict[str, DantomaxRecord] = {}
        self._chain: list[DantomaxRecord] = []
        self._head_hash = self.GENESIS

    @property
    def ledger_head(self) -> str:
        return self._head_hash

    @property
    def ledger_length(self) -> int:
        return len(self._chain)

    def register_evidence(
        self,
        evidence_id: str,
        sha256_hash: str,
        validation_report: dict[str, Any],
    ) -> dict[str, Any]:
        """Register evidence hash and validation summary; return ledger receipt."""
        if not evidence_id or not sha256_hash:
            raise ValueError("evidence_id and sha256_hash are required")
        position = len(self._chain)
        timestamp = _utc_now()
        record_id = f"dmx_{evidence_id}_{position:06d}"
        prev = self._head_hash
        signature = self._sign(
            evidence_id=evidence_id,
            sha256_hash=sha256_hash,
            timestamp=timestamp,
            prev_ledger_hash=prev,
            position=position,
        )
        ledger_hash = self._hash_link(
            prev=prev,
            evidence_id=evidence_id,
            sha256_hash=sha256_hash,
            signature=signature,
            position=position,
        )
        record = DantomaxRecord(
            dantomax_record_id=record_id,
            evidence_id=evidence_id,
            sha256_hash=sha256_hash,
            validation_summary={
                "failed_checks": list(validation_report.get("failed_checks") or []),
                "is_valid": not bool(validation_report.get("failed_checks")),
                "tags": list(validation_report.get("tags") or []),
            },
            timestamp=timestamp,
            signature=signature,
            ledger_position=position,
            prev_ledger_hash=prev,
            event_type="REGISTER",
            ledger_hash=ledger_hash,
        )
        self._records.setdefault(evidence_id, []).append(record)
        self._by_id[record_id] = record
        self._chain.append(record)
        self._head_hash = ledger_hash
        return {
            "dantomax_record_id": record_id,
            "signature": signature,
            "ledger_position": position,
            "ledger_hash": ledger_hash,
            "prev_ledger_hash": prev,
            "timestamp": timestamp,
            "is_attested": True,
        }

    def verify_evidence(self, evidence_id: str, sha256_hash: str) -> dict[str, Any]:
        """Confirm record existence, hash match, and signature validity."""
        history = self._records.get(evidence_id) or []
        if not history:
            return {
                "is_verified": False,
                "verification_details": {"reason": "not_found", "evidence_id": evidence_id},
            }
        latest = history[-1]
        sig_ok = self._verify_signature(latest)
        hash_ok = latest.sha256_hash == sha256_hash
        chain_ok = self._verify_chain_link(latest)
        is_verified = sig_ok and hash_ok and chain_ok
        return {
            "is_verified": is_verified,
            "verification_details": {
                "evidence_id": evidence_id,
                "expected_hash": sha256_hash,
                "attested_hash": latest.sha256_hash,
                "hash_match": hash_ok,
                "signature_valid": sig_ok,
                "chain_valid": chain_ok,
                "dantomax_record_id": latest.dantomax_record_id,
                "ledger_position": latest.ledger_position,
                "ledger_hash": latest.ledger_hash,
            },
        }

    def get_provenance_chain(self, evidence_id: str) -> list[dict[str, Any]]:
        """Return ordered (hash, timestamp, signature, event_type) records."""
        return [
            {
                "hash": r.sha256_hash,
                "timestamp": r.timestamp,
                "signature": r.signature,
                "event_type": r.event_type,
                "dantomax_record_id": r.dantomax_record_id,
                "ledger_position": r.ledger_position,
                "ledger_hash": r.ledger_hash,
            }
            for r in self._records.get(evidence_id, [])
        ]

    def verify_ledger_integrity(self) -> dict[str, Any]:
        """Walk the full chain; return integrity report."""
        prev = self.GENESIS
        for i, record in enumerate(self._chain):
            if record.ledger_position != i:
                return {"ok": False, "reason": "position_mismatch", "at": i}
            if record.prev_ledger_hash != prev:
                return {"ok": False, "reason": "prev_hash_mismatch", "at": i}
            if not self._verify_signature(record):
                return {"ok": False, "reason": "bad_signature", "at": i}
            expected = self._hash_link(
                prev=prev,
                evidence_id=record.evidence_id,
                sha256_hash=record.sha256_hash,
                signature=record.signature,
                position=i,
            )
            if record.ledger_hash != expected:
                return {"ok": False, "reason": "ledger_hash_mismatch", "at": i}
            prev = record.ledger_hash
        return {"ok": True, "length": len(self._chain), "head": self._head_hash}

    def export_ledger(self) -> list[dict[str, Any]]:
        return [r.to_dict() for r in self._chain]

    def _sign(
        self,
        *,
        evidence_id: str,
        sha256_hash: str,
        timestamp: str,
        prev_ledger_hash: str,
        position: int,
    ) -> str:
        payload = f"{evidence_id}|{sha256_hash}|{timestamp}|{prev_ledger_hash}|{position}"
        return hmac.new(self._key, payload.encode("utf-8"), hashlib.sha256).hexdigest()

    def _verify_signature(self, record: DantomaxRecord) -> bool:
        expected = self._sign(
            evidence_id=record.evidence_id,
            sha256_hash=record.sha256_hash,
            timestamp=record.timestamp,
            prev_ledger_hash=record.prev_ledger_hash,
            position=record.ledger_position,
        )
        return hmac.compare_digest(expected, record.signature)

    def _hash_link(
        self,
        *,
        prev: str,
        evidence_id: str,
        sha256_hash: str,
        signature: str,
        position: int,
    ) -> str:
        blob = json.dumps(
            {
                "prev": prev,
                "evidence_id": evidence_id,
                "sha256_hash": sha256_hash,
                "signature": signature,
                "position": position,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def _verify_chain_link(self, record: DantomaxRecord) -> bool:
        if record.ledger_position < 0 or record.ledger_position >= len(self._chain):
            return False
        if self._chain[record.ledger_position].dantomax_record_id != record.dantomax_record_id:
            return False
        expected = self._hash_link(
            prev=record.prev_ledger_hash,
            evidence_id=record.evidence_id,
            sha256_hash=record.sha256_hash,
            signature=record.signature,
            position=record.ledger_position,
        )
        return record.ledger_hash == expected
