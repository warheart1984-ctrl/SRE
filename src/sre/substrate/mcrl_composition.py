"""Compose SRE MCRLRosettaEngine with FAE Rosetta for richer alignment.

SRE's MCRLRosettaEngine provides temporal / cross-branch alignment over
LinguisticEvidence. FAE's MCRLRosettaEngine provides formal cross-language
alignment entries with constitutional anchors and conformance profiles.

This module bridges the two: SRE temporal maps feed into FAE alignment entries
so that Mythar ↔ external-language correspondences get constitutional provenance.
"""

from __future__ import annotations

from typing import Any

from fae.mcr.rosetta import (
    AlignmentMode,
    ExternalRoot,
    MCRLRosettaEngine as FAERosettaEngine,
    get_mcrl_engine,
)

from ..mcrl.rosetta_engine import MCRLRosettaEngine as SRERosettaEngine


class ComposedRosettaEngine:
    """Layer SRE temporal mapping onto FAE formal alignment.

    Usage:
        composed = ComposedRosettaEngine(sre_rosetta, fae_rosetta)
        result = composed.map_and_align(evidence_list)
        # result includes both SRE temporal_map and FAE alignment entries.
    """

    def __init__(
        self,
        sre_engine: SRERosettaEngine | None = None,
        fae_engine: FAERosettaEngine | None = None,
    ) -> None:
        self.sre = sre_engine or SRERosettaEngine()
        self.fae = fae_engine or get_mcrl_engine()

    def map_and_align(
        self,
        evidence: Any,
        *,
        source_language: str = "mythar",
        target_language: str = "external",
        evidence_id: str = "auto",
    ) -> dict[str, Any]:
        """Run SRE temporal mapping, then register FAE alignments for each period pair.

        Returns combined result dict with ``temporal_map`` (SRE) and
        ``fae_alignments`` (list of AlignmentEntry dicts).
        """
        temporal_map = self.sre.map_temporal(evidence)

        fae_alignments: list[dict[str, Any]] = []
        for alignment in temporal_map.get("alignments", []):
            from_period = alignment.get("from_period", "")
            to_period = alignment.get("to_period", "")
            if not from_period or not to_period:
                continue

            entry = self.fae.create_alignment(
                mythar_expr=f"period:{from_period}",
                external_expr=f"period:{to_period}",
                mode=AlignmentMode.EVIDENTIAL,
                source_lang=source_language,
                target_lang=target_language,
                evidence_id=evidence_id,
                source_domain="temporal",
                target_domain="temporal",
            )
            fae_alignments.append({
                "id": entry.id,
                "from_period": from_period,
                "to_period": to_period,
                "mode": entry.mode.value,
                "confidence": entry.alignment_confidence,
            })

        return {
            "temporal_map": temporal_map,
            "fae_alignments": fae_alignments,
            "alignment_count": len(fae_alignments),
            "temporal_valid": temporal_map.get("valid", False),
        }

    def register_external_root(
        self,
        language: str,
        form: str,
        domain: str,
        gloss: str,
        evidence_id: str,
    ) -> ExternalRoot:
        """Register an external root in the FAE Rosetta layer."""
        root = ExternalRoot(
            language=language,
            form=form,
            domain=domain,
            gloss=gloss,
            evidence_id=evidence_id,
        )
        self.fae.register_external_root(root)
        return root
