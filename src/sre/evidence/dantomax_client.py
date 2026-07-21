"""Dantomax integrity oracle — append-only attestation + evidence ledger."""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .attestations import (
    AttestationStatus,
    HistoricalAttestation,
    compute_attestation_checksum,
    validate_attestation_fields,
)
from .dantomax_signer import DantomaxSigner, LocalHmacSigner


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class DantomaxRecord:
    """Single ledger entry (evidence hash and/or historical attestation event)."""

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
    attestation_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)

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
            "attestation_id": self.attestation_id,
            "payload": self.payload,
        }


class DantomaxClient:
    """
    Evidence and lineage substrate.

    Append-only, HMAC-signed, hash-chained ledger for:
    - Evidence integrity receipts (REGISTER)
    - Historical attestations (ATTEST / SUPERSEDE / REJECT / APPROVE / CORRECT)
    """

    GENESIS = "0" * 64
    ATTESTATION_EVENTS = frozenset(
        {"ATTEST", "SUPERSEDE", "REJECT", "APPROVE", "CORRECT"}
    )

    def __init__(
        self,
        signing_key: str | bytes | None = None,
        *,
        signer: DantomaxSigner | None = None,
    ) -> None:
        if signer is not None:
            self._signer = signer
        else:
            self._signer = LocalHmacSigner(signing_key)
        self._records: dict[str, list[DantomaxRecord]] = {}
        self._by_id: dict[str, DantomaxRecord] = {}
        self._chain: list[DantomaxRecord] = []
        self._head_hash = self.GENESIS
        self._attestations: dict[str, HistoricalAttestation] = {}
        self._attestation_history: dict[str, list[str]] = {}
        self._governance_events: list[dict[str, Any]] = []
        self._content_checksums: dict[str, str] = {}

    @property
    def signing_mode(self) -> str:
        return self._signer.mode

    @property
    def ledger_head(self) -> str:
        return self._head_hash

    @property
    def ledger_length(self) -> int:
        return len(self._chain)

    @property
    def attestation_root_hash(self) -> str:
        """Merkle-style root over active attestation checksums (sorted)."""
        active = [
            a.checksum
            for a in self._attestations.values()
            if a.status in {AttestationStatus.ACTIVE, AttestationStatus.APPROVED}
        ]
        blob = json.dumps(sorted(active), separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    # --- Evidence integrity (existing API) ---

    def register_evidence(
        self,
        evidence_id: str,
        sha256_hash: str,
        validation_report: dict[str, Any],
    ) -> dict[str, Any]:
        if not evidence_id or not sha256_hash:
            raise ValueError("evidence_id and sha256_hash are required")
        return self._append(
            subject_id=evidence_id,
            sha256_hash=sha256_hash,
            event_type="REGISTER",
            validation_summary={
                "failed_checks": list(validation_report.get("failed_checks") or []),
                "is_valid": not bool(validation_report.get("failed_checks")),
                "tags": list(validation_report.get("tags") or []),
            },
            attestation_id=None,
            payload={},
        )

    def verify_evidence(self, evidence_id: str, sha256_hash: str) -> dict[str, Any]:
        history = [
            r
            for r in (self._records.get(evidence_id) or [])
            if r.event_type == "REGISTER"
        ]
        if not history:
            return {
                "is_verified": False,
                "verification_details": {"reason": "not_found", "evidence_id": evidence_id},
            }
        latest = history[-1]
        sig_ok = self._verify_signature(latest)
        hash_ok = latest.sha256_hash == sha256_hash
        chain_ok = self._verify_chain_link(latest)
        return {
            "is_verified": bool(sig_ok and hash_ok and chain_ok),
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
        return [
            {
                "hash": r.sha256_hash,
                "timestamp": r.timestamp,
                "signature": r.signature,
                "event_type": r.event_type,
                "dantomax_record_id": r.dantomax_record_id,
                "ledger_position": r.ledger_position,
                "ledger_hash": r.ledger_hash,
                "attestation_id": r.attestation_id,
            }
            for r in self._records.get(evidence_id, [])
        ]

    # --- Historical attestations ---

    def register_attestation(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Register a historical attestation. Rejects unresolved/malformed sources,
        duplicate active attestation_ids, and checksum mismatches.
        """
        errors = validate_attestation_fields(data)
        if errors:
            self._gov_event("ATTESTATION_REJECTED", {"errors": errors, "data_id": data.get("attestation_id")})
            raise ValueError(f"attestation rejected: {errors}")

        att = HistoricalAttestation.from_dict(data)
        if att.attestation_id in self._attestations:
            existing = self._attestations[att.attestation_id]
            if existing.status not in {AttestationStatus.SUPERSEDED, AttestationStatus.REJECTED}:
                raise ValueError(f"duplicate attestation: {att.attestation_id}")

        # Verify checksum integrity
        expected = compute_attestation_checksum(att)
        if att.checksum and att.checksum != expected:
            raise ValueError("checksum integrity failure")
        att.checksum = expected
        att.status = AttestationStatus.ACTIVE
        self._attestations[att.attestation_id] = att
        self._attestation_history.setdefault(att.attestation_id, []).append(att.attestation_id)
        self._content_checksums[att.attestation_id] = att.checksum

        receipt = self._append(
            subject_id=f"att:{att.attestation_id}",
            sha256_hash=att.checksum,
            event_type="ATTEST",
            validation_summary={"attestation_id": att.attestation_id, "status": att.status.value},
            attestation_id=att.attestation_id,
            payload=att.to_dict(),
        )
        self._gov_event(
            "ATTESTATION_REGISTERED",
            {"attestation_id": att.attestation_id, "ledger": receipt},
        )
        return {**receipt, "attestation": att.to_dict()}

    def supersede_attestation(
        self,
        old_attestation_id: str,
        new_data: dict[str, Any],
        *,
        reason: str,
    ) -> dict[str, Any]:
        """Corrections must create a superseding record — never mutate silently."""
        old = self._attestations.get(old_attestation_id)
        if old is None:
            raise KeyError(f"unknown attestation: {old_attestation_id}")
        if old.status == AttestationStatus.REJECTED:
            raise ValueError("cannot supersede rejected attestation")

        new_data = dict(new_data)
        new_data["supersedes"] = old_attestation_id
        if "attestation_id" not in new_data or new_data["attestation_id"] == old_attestation_id:
            new_data["attestation_id"] = f"{old_attestation_id}__v{len(self._attestation_history.get(old_attestation_id, [])) + 1}"

        result = self.register_attestation(new_data)
        new_id = result["attestation"]["attestation_id"]
        old.status = AttestationStatus.SUPERSEDED
        old.superseded_by = new_id
        new_att = self._attestations[new_id]

        receipt = self._append(
            subject_id=f"att:{old_attestation_id}",
            sha256_hash=new_att.checksum,
            event_type="SUPERSEDE",
            validation_summary={
                "old": old_attestation_id,
                "new": new_id,
                "reason": reason,
            },
            attestation_id=new_id,
            payload={"reason": reason, "old": old.to_dict(), "new": new_att.to_dict()},
        )
        self._gov_event(
            "ATTESTATION_SUPERSEDED",
            {"old": old_attestation_id, "new": new_id, "reason": reason},
        )
        return {**receipt, "attestation": new_att.to_dict()}

    def correct_attestation(
        self,
        old_attestation_id: str,
        new_data: dict[str, Any],
        *,
        reason: str,
    ) -> dict[str, Any]:
        """Governance CORRECT event — always supersedes; never mutates in place."""
        result = self.supersede_attestation(
            old_attestation_id, new_data, reason=reason
        )
        self._gov_event(
            "ATTESTATION_CORRECTED",
            {
                "old": old_attestation_id,
                "new": result["attestation"]["attestation_id"],
                "reason": reason,
            },
        )
        # Append explicit CORRECT ledger event for audit trails
        new_id = result["attestation"]["attestation_id"]
        new_att = self._attestations[new_id]
        self._append(
            subject_id=f"att:{old_attestation_id}",
            sha256_hash=new_att.checksum,
            event_type="CORRECT",
            validation_summary={"old": old_attestation_id, "new": new_id, "reason": reason},
            attestation_id=new_id,
            payload={"reason": reason},
        )
        return result

    def reject_attestation(self, attestation_id: str, *, reason: str) -> dict[str, Any]:
        att = self._attestations.get(attestation_id)
        if att is None:
            raise KeyError(f"unknown attestation: {attestation_id}")
        att.status = AttestationStatus.REJECTED
        receipt = self._append(
            subject_id=f"att:{attestation_id}",
            sha256_hash=att.checksum,
            event_type="REJECT",
            validation_summary={"reason": reason},
            attestation_id=attestation_id,
            payload={"reason": reason},
        )
        self._gov_event("ATTESTATION_REJECTED", {"attestation_id": attestation_id, "reason": reason})
        return receipt

    def approve_attestation(self, attestation_id: str) -> dict[str, Any]:
        att = self._attestations.get(attestation_id)
        if att is None:
            raise KeyError(f"unknown attestation: {attestation_id}")
        if att.status == AttestationStatus.REJECTED:
            raise ValueError("cannot approve rejected attestation")
        if att.status == AttestationStatus.SUPERSEDED:
            raise ValueError("cannot approve superseded attestation")
        att.status = AttestationStatus.APPROVED
        receipt = self._append(
            subject_id=f"att:{attestation_id}",
            sha256_hash=att.checksum,
            event_type="APPROVE",
            validation_summary={"status": "approved"},
            attestation_id=attestation_id,
            payload=att.to_dict(),
        )
        self._gov_event("ATTESTATION_APPROVED", {"attestation_id": attestation_id})
        return receipt

    def get_attestation(self, attestation_id: str) -> HistoricalAttestation | None:
        return self._attestations.get(attestation_id)

    def list_active_attestations(self) -> list[HistoricalAttestation]:
        return [
            a
            for a in self._attestations.values()
            if a.status in {AttestationStatus.ACTIVE, AttestationStatus.APPROVED}
        ]

    def require_attested_sources(self, attestation_ids: list[str]) -> list[str]:
        """Return list of missing/invalid attestation IDs (empty = all valid)."""
        bad: list[str] = []
        for aid in attestation_ids:
            att = self._attestations.get(aid)
            if att is None:
                bad.append(f"missing:{aid}")
            elif att.status == AttestationStatus.REJECTED:
                bad.append(f"rejected:{aid}")
            elif att.status == AttestationStatus.SUPERSEDED:
                bad.append(f"superseded:{aid}")
            else:
                if att.checksum != compute_attestation_checksum(att):
                    bad.append(f"checksum:{aid}")
        return bad

    def build_lineage_trace(
        self,
        *,
        attestation_ids: list[str],
        cognate_set_id: str | None = None,
        correspondence_ids: list[str] | None = None,
        sound_shift_ids: list[str] | None = None,
        proto_form_id: str | None = None,
        certification_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Deterministic provenance:
        attestation → cognate set → correspondence → sound shift → proto-form → certification
        """
        nodes: list[dict[str, Any]] = []
        for aid in attestation_ids:
            att = self._attestations.get(aid)
            nodes.append(
                {
                    "kind": "attestation",
                    "id": aid,
                    "present": att is not None,
                    "status": att.status.value if att else None,
                    "form": att.normalized_form if att else None,
                    "language": att.language if att else None,
                    "evidence_class": att.evidence_class.value if att else None,
                    "checksum": att.checksum if att else None,
                }
            )
        if cognate_set_id:
            nodes.append({"kind": "cognate_set", "id": cognate_set_id})
        for cid in correspondence_ids or []:
            nodes.append({"kind": "correspondence", "id": cid})
        for sid in sound_shift_ids or []:
            nodes.append({"kind": "sound_shift", "id": sid})
        if proto_form_id:
            nodes.append({"kind": "proto_form", "id": proto_form_id})
        if certification_id:
            nodes.append({"kind": "certification", "id": certification_id})

        edges = []
        for i in range(len(nodes) - 1):
            edges.append({"from": nodes[i]["id"], "to": nodes[i + 1]["id"]})

        return {
            "path": [
                "attestation",
                "cognate_set",
                "correspondence",
                "sound_shift",
                "proto_form",
                "certification",
            ],
            "nodes": nodes,
            "edges": edges,
            "attestation_root_hash": self.attestation_root_hash,
            "ledger_head": self.ledger_head,
            "human_readable": self._format_lineage_human(nodes),
        }

    def governance_events(self) -> list[dict[str, Any]]:
        return list(self._governance_events)

    def verify_ledger_integrity(self) -> dict[str, Any]:
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
        # Attestation checksums
        for aid, att in self._attestations.items():
            if att.checksum != compute_attestation_checksum(att):
                return {"ok": False, "reason": "attestation_checksum", "at": aid}
        return {
            "ok": True,
            "length": len(self._chain),
            "head": self._head_hash,
            "attestation_root_hash": self.attestation_root_hash,
        }

    def export_ledger(self) -> list[dict[str, Any]]:
        return [r.to_dict() for r in self._chain]

    # --- internals ---

    def _append(
        self,
        *,
        subject_id: str,
        sha256_hash: str,
        event_type: str,
        validation_summary: dict[str, Any],
        attestation_id: str | None,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        position = len(self._chain)
        timestamp = _utc_now()
        record_id = f"dmx_{subject_id.replace(':', '_')}_{position:06d}"
        prev = self._head_hash
        signature = self._sign(
            evidence_id=subject_id,
            sha256_hash=sha256_hash,
            timestamp=timestamp,
            prev_ledger_hash=prev,
            position=position,
        )
        ledger_hash = self._hash_link(
            prev=prev,
            evidence_id=subject_id,
            sha256_hash=sha256_hash,
            signature=signature,
            position=position,
        )
        record = DantomaxRecord(
            dantomax_record_id=record_id,
            evidence_id=subject_id,
            sha256_hash=sha256_hash,
            validation_summary=validation_summary,
            timestamp=timestamp,
            signature=signature,
            ledger_position=position,
            prev_ledger_hash=prev,
            event_type=event_type,
            ledger_hash=ledger_hash,
            attestation_id=attestation_id,
            payload=payload,
        )
        self._records.setdefault(subject_id, []).append(record)
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
            "event_type": event_type,
        }

    def _gov_event(self, event_type: str, payload: dict[str, Any]) -> None:
        self._governance_events.append(
            {
                "event_type": event_type,
                "timestamp": _utc_now(),
                "payload": payload,
            }
        )

    def _format_lineage_human(self, nodes: list[dict[str, Any]]) -> str:
        parts: list[str] = []
        for n in nodes:
            kind = n.get("kind")
            if kind == "attestation":
                if n.get("present"):
                    parts.append(
                        f"[{n['language']}] {n.get('form')} "
                        f"({n.get('evidence_class')}, {n.get('status')}) id={n['id']}"
                    )
                else:
                    parts.append(f"[missing attestation] id={n['id']}")
            else:
                parts.append(f"{kind}: {n.get('id')}")
        return " → ".join(parts)

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
        return self._signer.sign(payload)

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
