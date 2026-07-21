"""Map SRE linguistic evidence into the FAE substrate registry.

Does not replace ``sre.evidence.registry.EvidenceRegistry``. Mirrors ACCEPTED
records into ``fae.EvidenceRegistry`` so constitutional substrate tooling can
see domain evidence without changing the linguistic wire API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fae.evidence.registry import (
    Evidence,
    EvidenceSource,
    EvidenceStatus,
    ProvenanceMetadata,
)
from fae.evidence.registry import (
    EvidenceRegistry as FAEEvidenceRegistry,
)

if TYPE_CHECKING:
    from ..evidence.models import LinguisticEvidence


def mirror_linguistic_evidence_to_fae(
    linguistic: LinguisticEvidence,
    *,
    fae_registry: FAEEvidenceRegistry,
    cycle_id: str = "sre-domain",
    stage: str = "OBSERVE",
    source: EvidenceSource = EvidenceSource.EXTERNAL_DATABASE,
) -> Evidence:
    """Register a copy of linguistic evidence content into a FAE registry.

    Uses EXTERNAL_DATABASE as the default source (FAC-E1 externality). Content
    is the linguistic payload plus source_reference; SHA256 integrity follows
    FAE ProvenanceMetadata rules.
    """
    content: dict[str, Any] = {
        "evidence_id": linguistic.evidence_id,
        "evidence_type": getattr(linguistic.evidence_type, "value", linguistic.evidence_type),
        "source_reference": linguistic.source_reference,
        "content": linguistic.content,
        "sha256_hash": getattr(linguistic, "sha256_hash", None),
    }
    provenance = ProvenanceMetadata.create(
        source=source,
        source_id=linguistic.source_reference or linguistic.evidence_id,
        acquisition_method="sre.evidence.registry.mirror",
        content=content,
        confidence=1.0,
        validation_status=EvidenceStatus.VERIFIED,
        validator_id="sre.substrate.bridge",
    )
    return fae_registry.register(
        content=content,
        content_type="linguistic_evidence",
        provenance=provenance,
        cycle_id=cycle_id,
        stage=stage,
        evidence_id=f"fae:{linguistic.evidence_id}",
    )
