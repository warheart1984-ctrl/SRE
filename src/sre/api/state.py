"""Application state — shared registry, CEL, FRA, CIH, and explorer."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ..ai.hlrm_agent import HLRMAIAgent
from ..evidence.cel import ConstitutionalEvidenceLedger
from ..evidence.cel_store import CELStore, DEFAULT_CEL_PATH
from ..evidence.dantomax_client import DantomaxClient
from ..evidence.dantomax_signer import create_signer_from_env
from ..evidence.ledger_explorer import SovereignLedgerExplorer
from ..evidence.registry import EvidenceRegistry
from ..governance.cih_service import FAECLanguageReconstructionService
from ..substrate import FAEEvidenceRegistry, FactualAlignmentEngine, create_fae


def _resolve_cel_path() -> Path:
    raw = os.environ.get("SRE_CEL_STORE_PATH", "").strip()
    return Path(raw) if raw else DEFAULT_CEL_PATH


class AppState:
    """Process-wide state for API handlers."""

    def __init__(
        self,
        *,
        cel_store_path: str | Path | None = None,
        dantomax_signing_key: str | None = None,
    ) -> None:
        store_path = Path(cel_store_path) if cel_store_path else _resolve_cel_path()
        self.cel_store = CELStore(store_path)
        signing_key = dantomax_signing_key or os.environ.get("SRE_DANTOMAX_KEY")
        self.signer = create_signer_from_env(signing_key)
        self.dantomax = DantomaxClient(signer=self.signer)
        self.cel = ConstitutionalEvidenceLedger.load_from_store(
            self.cel_store,
            dantomax=self.dantomax,
        )
        # FAE constitutional substrate (generic FAC/FRA); linguistic registry stays SRE.
        self.fae: FactualAlignmentEngine = create_fae()
        self.fae_registry: FAEEvidenceRegistry = self.fae.registry
        self.registry = EvidenceRegistry(
            dantomax_client=self.dantomax,
            cel=self.cel,
            cel_store=self.cel_store,
            fae_registry=self.fae_registry,
        )
        self.agent = HLRMAIAgent(self.registry, config={})
        self.cih = FAECLanguageReconstructionService(self.registry)
        self.explorer = SovereignLedgerExplorer(
            self.cel,
            dantomax=self.dantomax,
            store=self.cel_store,
        )
        self.reconstruction_cache: dict[str, dict[str, Any]] = {}
        self.project_registry: dict[str, dict[str, Any]] = {}

    def require_cel(self) -> ConstitutionalEvidenceLedger:
        if self.cel is None:
            raise RuntimeError("CEL not configured")
        return self.cel

    def summary(self) -> dict[str, Any]:
        return {
            "cel_length": self.cel.cel_length,
            "cel_head": self.cel.cel_head,
            "fabric_root_hash": self.cel.fabric_root_hash,
            "store_path": str(self.cel_store.path),
            "signing_mode": self.dantomax.signing_mode,
        }


_default_state: AppState | None = None


def get_app_state() -> AppState:
    """Lazy singleton for API process."""
    global _default_state
    if _default_state is None:
        _default_state = AppState()
    return _default_state


def reset_app_state(state: AppState | None = None) -> None:
    """Reset singleton (testing)."""
    global _default_state
    _default_state = state
