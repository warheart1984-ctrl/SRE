"""Constitutional Evidence Ledger (CEL) — unified constitutional evidence fabric."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .dantomax_client import DantomaxClient

CEL_VERSION = "1.0"
GENESIS = "0" * 64


class CELEntryType(str, Enum):
    """Typed constitutional events unified under CEL."""

    ATTESTATION = "attestation"
    CORRESPONDENCE = "correspondence"
    HYPOTHESIS = "hypothesis"
    VALIDATION = "validation"
    CERTIFICATION = "certification"
    EVIDENCE = "evidence"
    GOVERNANCE = "governance"


@dataclass
class CELEntry:
    """Single append-only constitutional ledger entry."""

    cel_entry_id: str
    entry_type: CELEntryType
    subject_id: str
    payload: dict[str, Any]
    links: list[str] = field(default_factory=list)
    timestamp: str = ""
    position: int = 0
    prev_cel_hash: str = GENESIS
    cel_hash: str = ""
    checksum: str = ""
    dantomax_record_id: str | None = None
    dantomax_ledger_hash: str | None = None
    constitutional_article: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["entry_type"] = self.entry_type.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CELEntry:
        entry_type = data["entry_type"]
        if isinstance(entry_type, str):
            entry_type = CELEntryType(entry_type)
        return cls(
            cel_entry_id=str(data["cel_entry_id"]),
            entry_type=entry_type,
            subject_id=str(data["subject_id"]),
            payload=dict(data.get("payload") or {}),
            links=list(data.get("links") or []),
            timestamp=str(data.get("timestamp") or ""),
            position=int(data.get("position", 0)),
            prev_cel_hash=str(data.get("prev_cel_hash") or GENESIS),
            cel_hash=str(data.get("cel_hash") or ""),
            checksum=str(data.get("checksum") or ""),
            dantomax_record_id=data.get("dantomax_record_id"),
            dantomax_ledger_hash=data.get("dantomax_ledger_hash"),
            constitutional_article=str(data.get("constitutional_article") or ""),
        )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_entry_body(
    *,
    entry_type: str,
    subject_id: str,
    payload: dict[str, Any],
    links: list[str],
    constitutional_article: str,
) -> dict[str, Any]:
    return {
        "entry_type": entry_type,
        "subject_id": subject_id,
        "payload": payload,
        "links": sorted(links),
        "constitutional_article": constitutional_article,
    }


def compute_cel_checksum(entry: CELEntry) -> str:
    body = _canonical_entry_body(
        entry_type=entry.entry_type.value,
        subject_id=entry.subject_id,
        payload=entry.payload,
        links=list(entry.links),
        constitutional_article=entry.constitutional_article,
    )
    blob = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class ConstitutionalEvidenceLedger:
    """
    Unified constitutional evidence fabric.

    CEL indexes and chains constitutional events from Dantomax, FRA, and CIH.
    Dantomax remains the cryptographic integrity oracle; CEL is the semantic,
    queryable, constitutionally-typed audit trail.
    """

    ARTICLE_MAP = {
        CELEntryType.EVIDENCE: "Article II",
        CELEntryType.ATTESTATION: "Article II §2",
        CELEntryType.CORRESPONDENCE: "Article III",
        CELEntryType.HYPOTHESIS: "Article III §2",
        CELEntryType.VALIDATION: "Article III §3",
        CELEntryType.CERTIFICATION: "Article V §1",
        CELEntryType.GOVERNANCE: "Article V §2",
    }

    def __init__(
        self,
        dantomax: DantomaxClient | None = None,
        store: Any | None = None,
    ) -> None:
        self._dantomax = dantomax
        self._store = store
        self._chain: list[CELEntry] = []
        self._by_id: dict[str, CELEntry] = {}
        self._by_subject: dict[str, list[str]] = {}
        self._by_type: dict[CELEntryType, list[str]] = {}
        self._head_hash = GENESIS
        if store is not None and store.exists():
            store.replay_into(self)

    @classmethod
    def load_from_store(
        cls,
        store: Any,
        *,
        dantomax: DantomaxClient | None = None,
    ) -> ConstitutionalEvidenceLedger:
        """Create a ledger and replay persisted entries from a CEL store."""
        return cls(dantomax=dantomax, store=store)

    @property
    def cel_head(self) -> str:
        return self._head_hash

    @property
    def cel_length(self) -> int:
        return len(self._chain)

    @property
    def fabric_root_hash(self) -> str:
        """Merkle-style root over active entry checksums (sorted)."""
        checksums = sorted(e.checksum for e in self._chain)
        blob = json.dumps(checksums, separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def append(
        self,
        entry_type: CELEntryType,
        subject_id: str,
        payload: dict[str, Any],
        *,
        links: list[str] | None = None,
        dantomax_record_id: str | None = None,
        dantomax_ledger_hash: str | None = None,
    ) -> CELEntry:
        """Append a typed constitutional event to CEL."""
        if not subject_id or not str(subject_id).strip():
            raise ValueError("CEL: subject_id is required")
        position = len(self._chain)
        entry_id = f"cel_{entry_type.value}_{subject_id}_{position:06d}"
        article = self.ARTICLE_MAP.get(entry_type, "Article I")
        entry = CELEntry(
            cel_entry_id=entry_id,
            entry_type=entry_type,
            subject_id=subject_id,
            payload=dict(payload),
            links=list(links or []),
            timestamp=_utc_now(),
            position=position,
            prev_cel_hash=self._head_hash,
            constitutional_article=article,
            dantomax_record_id=dantomax_record_id,
            dantomax_ledger_hash=dantomax_ledger_hash
            or (self._dantomax.ledger_head if self._dantomax else None),
        )
        entry.checksum = compute_cel_checksum(entry)
        entry.cel_hash = self._hash_link(
            prev=entry.prev_cel_hash,
            entry_id=entry.cel_entry_id,
            checksum=entry.checksum,
            position=position,
        )
        self._chain.append(entry)
        self._by_id[entry.cel_entry_id] = entry
        self._by_subject.setdefault(subject_id, []).append(entry.cel_entry_id)
        self._by_type.setdefault(entry_type, []).append(entry.cel_entry_id)
        self._head_hash = entry.cel_hash
        if self._store is not None:
            self._store.append_entry(entry)
        return entry

    def restore_entry(self, data: dict[str, Any] | CELEntry) -> CELEntry:
        """Restore a persisted entry without re-writing to the store."""
        entry = data if isinstance(data, CELEntry) else CELEntry.from_dict(data)
        if len(self._chain) != entry.position:
            raise ValueError(
                f"CEL restore position mismatch: expected {len(self._chain)}, "
                f"got {entry.position}"
            )
        if entry.checksum != compute_cel_checksum(entry):
            raise ValueError(f"CEL restore checksum mismatch: {entry.cel_entry_id}")
        expected = self._hash_link(
            prev=entry.prev_cel_hash,
            entry_id=entry.cel_entry_id,
            checksum=entry.checksum,
            position=entry.position,
        )
        if entry.cel_hash != expected:
            raise ValueError(f"CEL restore hash mismatch: {entry.cel_entry_id}")
        self._chain.append(entry)
        self._by_id[entry.cel_entry_id] = entry
        self._by_subject.setdefault(entry.subject_id, []).append(entry.cel_entry_id)
        self._by_type.setdefault(entry.entry_type, []).append(entry.cel_entry_id)
        self._head_hash = entry.cel_hash
        return entry

    def all_entries(self) -> list[CELEntry]:
        """Return all entries in append order."""
        return list(self._chain)

    # --- Typed record helpers ---

    def record_evidence(
        self,
        evidence_id: str,
        *,
        sha256_hash: str,
        validation_report: dict[str, Any],
        dantomax_receipt: dict[str, Any] | None = None,
    ) -> CELEntry:
        receipt = dantomax_receipt or {}
        return self.append(
            CELEntryType.EVIDENCE,
            evidence_id,
            {
                "evidence_id": evidence_id,
                "sha256_hash": sha256_hash,
                "validation_report": validation_report,
                "is_valid": not bool(validation_report.get("failed_checks")),
            },
            links=[evidence_id],
            dantomax_record_id=receipt.get("dantomax_record_id"),
            dantomax_ledger_hash=receipt.get("ledger_hash"),
        )

    def record_attestation(
        self,
        attestation_id: str,
        attestation: dict[str, Any],
        *,
        dantomax_receipt: dict[str, Any] | None = None,
    ) -> CELEntry:
        receipt = dantomax_receipt or {}
        return self.append(
            CELEntryType.ATTESTATION,
            attestation_id,
            {"attestation": attestation, "event": receipt.get("event_type", "ATTEST")},
            links=[attestation_id],
            dantomax_record_id=receipt.get("dantomax_record_id"),
            dantomax_ledger_hash=receipt.get("ledger_hash"),
        )

    def record_correspondence(
        self,
        cognate_set_id: str,
        discovery: dict[str, Any],
        *,
        links: list[str] | None = None,
    ) -> CELEntry:
        return self.append(
            CELEntryType.CORRESPONDENCE,
            cognate_set_id,
            discovery,
            links=links or [cognate_set_id],
        )

    def record_hypothesis(
        self,
        reconstruction_id: str,
        hypothesis: dict[str, Any],
        *,
        links: list[str] | None = None,
    ) -> CELEntry:
        return self.append(
            CELEntryType.HYPOTHESIS,
            reconstruction_id,
            hypothesis,
            links=links or [],
        )

    def record_validation(
        self,
        reconstruction_id: str,
        validation: dict[str, Any],
    ) -> CELEntry:
        return self.append(
            CELEntryType.VALIDATION,
            reconstruction_id,
            validation,
            links=[reconstruction_id],
        )

    def record_certification(
        self,
        certificate_id: str,
        certificate: dict[str, Any],
        *,
        trace_id: str | None = None,
        links: list[str] | None = None,
    ) -> CELEntry:
        payload = {"certificate": certificate}
        if trace_id:
            payload["trace_id"] = trace_id
        link_set = list(links or [certificate_id])
        if trace_id:
            link_set.append(trace_id)
        return self.append(
            CELEntryType.CERTIFICATION,
            certificate_id,
            payload,
            links=link_set,
        )

    def record_governance(
        self,
        trace_id: str,
        event: dict[str, Any],
        *,
        links: list[str] | None = None,
    ) -> CELEntry:
        return self.append(
            CELEntryType.GOVERNANCE,
            trace_id,
            event,
            links=links or [trace_id],
        )

    # --- Query ---

    def get_entry(self, cel_entry_id: str) -> CELEntry | None:
        return self._by_id.get(cel_entry_id)

    def query_by_type(self, entry_type: CELEntryType) -> list[CELEntry]:
        return [self._by_id[eid] for eid in self._by_type.get(entry_type, [])]

    def query_by_subject(self, subject_id: str) -> list[CELEntry]:
        return [self._by_id[eid] for eid in self._by_subject.get(subject_id, [])]

    def query_lineage(self, reconstruction_id: str) -> dict[str, Any]:
        """
        Constitutional path for a reconstruction:
        attestations → correspondences → hypotheses → validation → certification
        """
        entries = [
            e
            for e in self._chain
            if reconstruction_id in e.subject_id
            or reconstruction_id in e.links
            or any(reconstruction_id in str(v) for v in e.payload.values())
        ]
        by_type: dict[str, list[dict[str, Any]]] = {}
        for e in entries:
            by_type.setdefault(e.entry_type.value, []).append(
                {
                    "cel_entry_id": e.cel_entry_id,
                    "subject_id": e.subject_id,
                    "checksum": e.checksum,
                    "dantomax_ledger_hash": e.dantomax_ledger_hash,
                }
            )
        path_order = [
            "attestation",
            "correspondence",
            "hypothesis",
            "validation",
            "governance",
            "certification",
        ]
        return {
            "reconstruction_id": reconstruction_id,
            "cel_head": self._head_hash,
            "fabric_root_hash": self.fabric_root_hash,
            "entries_by_type": by_type,
            "path": path_order,
            "entry_count": len(entries),
            "human_readable": self._format_lineage(entries, path_order),
        }

    def verify_integrity(self) -> dict[str, Any]:
        prev = GENESIS
        for i, entry in enumerate(self._chain):
            if entry.position != i:
                return {"ok": False, "reason": "position_mismatch", "at": i}
            if entry.prev_cel_hash != prev:
                return {"ok": False, "reason": "prev_hash_mismatch", "at": i}
            if entry.checksum != compute_cel_checksum(entry):
                return {"ok": False, "reason": "checksum_mismatch", "at": entry.cel_entry_id}
            expected = self._hash_link(
                prev=prev,
                entry_id=entry.cel_entry_id,
                checksum=entry.checksum,
                position=i,
            )
            if entry.cel_hash != expected:
                return {"ok": False, "reason": "cel_hash_mismatch", "at": i}
            prev = entry.cel_hash
        dantomax_ok = True
        if self._dantomax is not None:
            dantomax_ok = bool(self._dantomax.verify_ledger_integrity().get("ok"))
        return {
            "ok": dantomax_ok,
            "length": len(self._chain),
            "head": self._head_hash,
            "fabric_root_hash": self.fabric_root_hash,
            "dantomax_integrity": dantomax_ok,
        }

    def export_ledger(self) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self._chain]

    def summary(self) -> dict[str, Any]:
        return {
            "version": CEL_VERSION,
            "length": self.cel_length,
            "head": self.cel_head,
            "fabric_root_hash": self.fabric_root_hash,
            "by_type": {t.value: len(ids) for t, ids in self._by_type.items()},
            "dantomax_head": self._dantomax.ledger_head if self._dantomax else None,
        }

    def _hash_link(
        self,
        *,
        prev: str,
        entry_id: str,
        checksum: str,
        position: int,
    ) -> str:
        blob = json.dumps(
            {"prev": prev, "entry_id": entry_id, "checksum": checksum, "position": position},
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def _format_lineage(
        self, entries: list[CELEntry], path_order: list[str]
    ) -> str:
        parts: list[str] = []
        for kind in path_order:
            typed = [e for e in entries if e.entry_type.value == kind]
            if not typed:
                continue
            preview = ", ".join(e.subject_id for e in typed[:4])
            if len(typed) > 4:
                preview += f" … (+{len(typed) - 4})"
            parts.append(f"{kind.upper()}: {preview}")
        return " → ".join(parts) if parts else "(no CEL entries)"
