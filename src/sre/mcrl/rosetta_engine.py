"""MCRL Rosetta engine — temporal / cross-branch mapping."""

from __future__ import annotations

from typing import Any

from ..evidence.models import LinguisticEvidence
from .temporal_mapping import TemporalMapping


class MCRLRosettaEngine:
    """Mythar Cross-Language Rosetta Layer — temporal mapping for FRA ALIGN."""

    def map_temporal(self, evidence: Any) -> dict[str, Any]:
        """Map evidence across periods / branches; return alignment record."""
        items: list[LinguisticEvidence] = []
        if isinstance(evidence, list):
            items = [e for e in evidence if isinstance(e, LinguisticEvidence)]
        elif isinstance(evidence, LinguisticEvidence):
            items = [evidence]

        by_period: dict[str, list[str]] = {}
        by_lang: dict[str, list[str]] = {}
        for ev in items:
            period = str(ev.content.get("period") or "unknown")
            lang = str(ev.content.get("language_code") or "?")
            by_period.setdefault(period, []).append(ev.evidence_id)
            by_lang.setdefault(lang, []).append(ev.evidence_id)

        alignments: list[dict[str, Any]] = []
        periods = sorted(by_period.keys())
        for i in range(len(periods) - 1):
            alignments.append(
                {
                    "from_period": periods[i],
                    "to_period": periods[i + 1],
                    "evidence_from": by_period[periods[i]],
                    "evidence_to": by_period[periods[i + 1]],
                }
            )
        # Cross-branch alignment when both MYT and REL present
        if "MYT" in by_lang and "REL" in by_lang:
            alignments.append(
                {
                    "from_branch": "MYT",
                    "to_branch": "REL",
                    "evidence_from": by_lang["MYT"],
                    "evidence_to": by_lang["REL"],
                }
            )

        mapping = TemporalMapping(
            source_period=periods[0] if periods else "",
            target_period=periods[-1] if periods else "",
            alignments=alignments,
        )
        return {
            "source_period": mapping.source_period,
            "target_period": mapping.target_period,
            "alignments": mapping.alignments,
            "valid": mapping.validate(),
            "by_period": by_period,
            "by_language": by_lang,
        }
