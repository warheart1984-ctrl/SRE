"""FRA reconstruction API handlers."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ...ai.hlrm_agent import HLRMAIAgent
from ...evidence.registry import EvidenceRegistry
from ...fra.reconstruction_engine import ChronologicalReconstruction
from ...storage.reconstruction_cache import ReconstructionCache


def start_reconstruction(
    registry: EvidenceRegistry,
    agent: HLRMAIAgent,
    body: dict[str, Any],
    *,
    reconstruction_cache: ReconstructionCache | dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Wire to POST /api/v1/reconstruction."""
    corpus = str(body.get("corpus_path") or body.get("corpus") or "mythar")
    evidence_sources = list(body.get("evidence_sources") or body.get("evidence_ids") or [])
    constraints = dict(body.get("constraints") or {})
    if body.get("require_attestation_lineage") is True:
        constraints["require_attestation_lineage"] = True

    engine = ChronologicalReconstruction(
        registry,
        agent,
        corpus_path=corpus,
        constraints=constraints,
    )
    result = engine.reconstruct_language(
        str(body["target_language"]),
        str(body["time_period"]),
        evidence_sources,
    )
    recon_id = result.get("reconstruction_id")
    if recon_id:
        reconstruction_cache[str(recon_id)] = result
    return result


def get_reconstruction(
    reconstruction_cache: ReconstructionCache | dict[str, dict[str, Any]],
    reconstruction_id: str,
) -> dict[str, Any] | None:
    """Wire to GET /api/v1/reconstruction/{reconstruction_id}."""
    return reconstruction_cache.get(reconstruction_id)


def get_reconstruction_validation(
    registry: EvidenceRegistry,
    reconstruction_id: str,
) -> dict[str, Any]:
    """Wire to GET /api/v1/reconstruction/{reconstruction_id}/validation."""
    result = registry.validate_reconstruction(reconstruction_id)
    data = asdict(result)
    validated = data.get("validated_at")
    if validated is not None and hasattr(validated, "isoformat"):
        data["validated_at"] = validated.isoformat()
    return data
