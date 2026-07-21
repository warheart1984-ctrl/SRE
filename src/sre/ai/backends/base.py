"""Pluggable analyzer backend protocol — FAC-E1 evidence anchoring required."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from ...evidence.models import LinguisticEvidence


@dataclass
class AnalysisBundle:
    """Normalized analysis output from any backend."""

    lexical_clusters: list[dict[str, Any]] = field(default_factory=list)
    phonological_shifts: list[dict[str, Any]] = field(default_factory=list)
    cognate_groups: list[dict[str, Any]] = field(default_factory=list)
    backend: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lexical_clusters": self.lexical_clusters,
            "phonological_shifts": self.phonological_shifts,
            "cognate_groups": self.cognate_groups,
            "backend": self.backend,
            "metadata": self.metadata,
        }


def _has_evidence_ids(item: dict[str, Any]) -> bool:
    ids = item.get("evidence_ids") or item.get("evidence_links") or []
    return isinstance(ids, list) and any(str(x).strip() for x in ids)


def enforce_evidence_anchors(
    bundle: AnalysisBundle,
    *,
    known_evidence_ids: set[str] | None = None,
) -> AnalysisBundle:
    """
    FAC-E1 / AI-01 gate: drop clusters, shifts, and cognate groups that lack
    evidence_ids, or that cite IDs not present in the input set when provided.
    """

    def ok(item: dict[str, Any]) -> bool:
        if not _has_evidence_ids(item):
            return False
        if known_evidence_ids is None:
            return True
        cited = {
            str(x)
            for x in (item.get("evidence_ids") or item.get("evidence_links") or [])
            if str(x).strip()
        }
        return bool(cited) and cited.issubset(known_evidence_ids)

    return AnalysisBundle(
        lexical_clusters=[c for c in bundle.lexical_clusters if ok(c)],
        phonological_shifts=[s for s in bundle.phonological_shifts if ok(s)],
        cognate_groups=[g for g in bundle.cognate_groups if ok(g)],
        backend=bundle.backend,
        metadata={
            **bundle.metadata,
            "fac_e1_anchored": True,
            "dropped_unanchored": True,
        },
    )


def evidence_id_set(evidence_list: list[Any]) -> set[str]:
    ids: set[str] = set()
    for item in evidence_list:
        if isinstance(item, LinguisticEvidence):
            ids.add(item.evidence_id)
        elif isinstance(item, dict) and item.get("evidence_id"):
            ids.add(str(item["evidence_id"]))
    return ids


@runtime_checkable
class AnalyzerBackend(Protocol):
    """Pluggable analysis backend for HLRMAIAgent."""

    @property
    def name(self) -> str:
        """Backend identifier: rule | statistical | ml."""

    def analyze(self, evidence_list: list[Any]) -> AnalysisBundle:
        """
        Analyze evidence. Implementations MUST attach ``evidence_ids`` on every
        cluster, shift, and cognate group. The agent re-validates with
        ``enforce_evidence_anchors`` before emitting results.
        """
        ...
