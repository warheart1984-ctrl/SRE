"""Sovereign Ledger Explorer API handlers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ...evidence.ledger_explorer import SovereignLedgerExplorer

_REPO_ROOT = Path(__file__).resolve().parents[4]
_PROFILE_PATH = _REPO_ROOT / "docs" / "conformance" / "SRE_ConformanceProfile_v1.json"


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


def get_conformance_summary() -> dict[str, Any]:
    """Wire to GET /api/v1/explorer/conformance — read-only SRE profile summary."""
    if not _PROFILE_PATH.is_file():
        return {
            "status": "profile_missing",
            "summary_md": "docs/conformance/SRE_ConformanceProfile_v1.md",
        }

    profile = json.loads(_PROFILE_PATH.read_text(encoding="utf-8"))
    gates = profile.get("conformance_gates") or []
    runtime = profile.get("runtime") or {}
    invariants = profile.get("invariants") or []

    return {
        "status": "profiled",
        "profile_id": profile.get("profile_id"),
        "profile_version": profile.get("profile_version"),
        "runtime": {
            "name": runtime.get("name"),
            "implementation_id": runtime.get("implementation_id"),
            "version": runtime.get("version"),
            "role": runtime.get("role"),
        },
        "counts": {
            "conformance_gates": len(gates),
            "invariants": len(invariants),
            "entities": len(profile.get("entities") or []),
        },
        "gates": [
            {
                "gate_id": g.get("gate_id"),
                "classification": g.get("classification"),
                "test_module": g.get("test_module"),
                "test_name": g.get("test_name"),
                "ci_status": "profiled",
            }
            for g in gates
        ],
        "references": {
            "profile_json": "docs/conformance/SRE_ConformanceProfile_v1.json",
            "summary_md": "docs/conformance/SRE_ConformanceProfile_v1.md",
            "test_suite": "tests/test_cih_conformance.py",
        },
    }
