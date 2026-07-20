"""CEL API handlers — framework-agnostic request/response dicts."""

from __future__ import annotations

from typing import Any

from ...evidence.cel import CELEntryType, ConstitutionalEvidenceLedger


def get_cel_head(cel: ConstitutionalEvidenceLedger) -> dict[str, Any]:
    """Wire to GET /api/v1/cel/head."""
    summary = cel.summary()
    integrity = cel.verify_integrity()
    return {
        **summary,
        "integrity": integrity,
    }


def list_cel_entries(
    cel: ConstitutionalEvidenceLedger,
    *,
    entry_type: str | None = None,
    subject_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """Wire to GET /api/v1/cel/entries."""
    limit = max(1, min(limit, 500))
    offset = max(0, offset)

    if entry_type:
        try:
            typed = CELEntryType(entry_type)
            pool = cel.query_by_type(typed)
        except ValueError:
            return {
                "entries": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "error": f"unknown entry_type: {entry_type}",
            }
    elif subject_id:
        pool = cel.query_by_subject(subject_id)
    else:
        pool = cel.all_entries()

    total = len(pool)
    page = pool[offset : offset + limit]
    return {
        "entries": [e.to_dict() for e in page],
        "total": total,
        "limit": limit,
        "offset": offset,
        "head": cel.cel_head,
        "fabric_root_hash": cel.fabric_root_hash,
    }


def get_cel_lineage(
    cel: ConstitutionalEvidenceLedger,
    reconstruction_id: str,
) -> dict[str, Any]:
    """Wire to GET /api/v1/cel/lineage/{reconstruction_id}."""
    return cel.query_lineage(reconstruction_id)
