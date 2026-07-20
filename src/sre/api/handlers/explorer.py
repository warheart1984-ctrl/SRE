"""Sovereign Ledger Explorer API handlers."""

from __future__ import annotations

from typing import Any

from ...evidence.ledger_explorer import SovereignLedgerExplorer


def get_fabric_overview(explorer: SovereignLedgerExplorer) -> dict[str, Any]:
    """Wire to GET /api/v1/explorer/fabric."""
    return explorer.fabric_overview()


def get_explorer_entry(
    explorer: SovereignLedgerExplorer,
    cel_entry_id: str,
) -> dict[str, Any] | None:
    """Wire to GET /api/v1/explorer/entry/{cel_entry_id}."""
    return explorer.explore_entry(cel_entry_id)


def get_explorer_reconstruction(
    explorer: SovereignLedgerExplorer,
    reconstruction_id: str,
) -> dict[str, Any]:
    """Wire to GET /api/v1/explorer/reconstruction/{reconstruction_id}."""
    return explorer.explore_reconstruction(reconstruction_id)


def search_explorer_entries(
    explorer: SovereignLedgerExplorer,
    *,
    entry_type: str | None = None,
    subject_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """Wire to GET /api/v1/explorer/entries."""
    return explorer.search_entries(
        entry_type=entry_type,
        subject_id=subject_id,
        limit=limit,
        offset=offset,
    )
