"""Sovereign Ledger Explorer — read model over CEL + Dantomax."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .cel import CELEntryType

if TYPE_CHECKING:
    from .cel import ConstitutionalEvidenceLedger
    from .cel_store import CELStore
    from .dantomax_client import DantomaxClient


class SovereignLedgerExplorer:
    """
      Constitutional read model composing CEL semantic fabric with Dantomax
    cryptographic anchors. Serves explorer UI and API without duplicating
      query logic in route handlers.
    """

    def __init__(
        self,
        cel: ConstitutionalEvidenceLedger,
        *,
        dantomax: DantomaxClient | None = None,
        store: CELStore | None = None,
    ) -> None:
        self._cel = cel
        self._dantomax = dantomax
        self._store = store

    def fabric_overview(self) -> dict[str, Any]:
        """Top-level constitutional fabric snapshot."""
        summary = self._cel.summary()
        integrity = self._cel.verify_integrity()
        overview: dict[str, Any] = {
            "cel": summary,
            "integrity": integrity,
            "persistence": self._store.export_snapshot() if self._store else None,
        }
        if self._dantomax is not None:
            overview["dantomax"] = {
                "ledger_length": self._dantomax.ledger_length,
                "ledger_head": self._dantomax.ledger_head,
                "attestation_root_hash": self._dantomax.attestation_root_hash,
                "integrity": self._dantomax.verify_ledger_integrity(),
            }
        return overview

    def explore_entry(self, cel_entry_id: str) -> dict[str, Any] | None:
        """Single CEL entry with linked subjects and Dantomax anchor."""
        entry = self._cel.get_entry(cel_entry_id)
        if entry is None:
            return None
        detail: dict[str, Any] = {
            "entry": entry.to_dict(),
            "linked_entries": [],
        }
        for link_id in entry.links:
            linked = self._cel.get_entry(link_id)
            if linked is not None:
                detail["linked_entries"].append(
                    {
                        "cel_entry_id": linked.cel_entry_id,
                        "entry_type": linked.entry_type.value,
                        "subject_id": linked.subject_id,
                    }
                )
            elif self._dantomax is not None and link_id.startswith("att_"):
                att = self._dantomax.get_attestation(link_id)
                if att is not None:
                    detail.setdefault("dantomax_attestations", []).append(
                        {
                            "attestation_id": link_id,
                            "status": getattr(att, "status", None),
                            "language": getattr(att, "language", None),
                        }
                    )
        if entry.dantomax_record_id and self._dantomax is not None:
            detail["dantomax_anchor"] = {
                "record_id": entry.dantomax_record_id,
                "ledger_hash": entry.dantomax_ledger_hash,
            }
        return detail

    def explore_reconstruction(self, reconstruction_id: str) -> dict[str, Any]:
        """Full constitutional path for a reconstruction."""
        lineage = self._cel.query_lineage(reconstruction_id)
        entries = [
            e.to_dict()
            for e in self._cel.all_entries()
            if reconstruction_id in e.subject_id
            or reconstruction_id in e.links
            or any(reconstruction_id in str(v) for v in e.payload.values())
        ]
        result: dict[str, Any] = {
            "reconstruction_id": reconstruction_id,
            "lineage": lineage,
            "entries": entries,
            "entry_count": len(entries),
        }
        attestation_ids: list[str] = []
        for e in entries:
            if e.get("entry_type") == "attestation":
                attestation_ids.append(e["subject_id"])
            payload = e.get("payload") or {}
            if isinstance(payload.get("attestation_ids"), list):
                attestation_ids.extend(payload["attestation_ids"])
        attestation_ids = list(dict.fromkeys(attestation_ids))
        if self._dantomax is not None and attestation_ids:
            result["dantomax_lineage"] = self._dantomax.build_lineage_trace(
                attestation_ids=attestation_ids,
                proto_form_id=reconstruction_id,
            )
        return result

    def search_entries(
        self,
        *,
        entry_type: str | None = None,
        subject_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Paginated entry search for explorer tables."""
        if entry_type:
            try:
                typed = CELEntryType(entry_type)
                pool = self._cel.query_by_type(typed)
            except ValueError:
                return {
                    "entries": [],
                    "total": 0,
                    "limit": limit,
                    "offset": offset,
                    "error": f"unknown entry_type: {entry_type}",
                }
        elif subject_id:
            pool = self._cel.query_by_subject(subject_id)
        else:
            pool = self._cel.all_entries()

        total = len(pool)
        page = pool[offset : offset + limit]
        return {
            "entries": [e.to_dict() for e in page],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
