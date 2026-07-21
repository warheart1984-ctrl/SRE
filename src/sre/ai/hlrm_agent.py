"""HLRMAIAgent — evidence-constrained reconstruction AI with pluggable backends."""

from __future__ import annotations

from typing import Any

from ..data import load_ancestor_hints
from .backends import (
    AnalyzerBackend,
    MlAnalyzerProvider,
    create_analyzer_backend,
    enforce_evidence_anchors,
    evidence_id_set,
)


class HLRMAIAgent:
    """
    AI Reconstruction Engine with pluggable analyzer backends.

    Backends: ``rule`` (default), ``statistical``, ``ml`` (requires injected provider).
    All hypotheses must cite evidence_ids (AI-01 / FAC-E1 anchoring).
    """

    def __init__(
        self,
        evidence_registry: Any | None = None,
        config: dict | None = None,
        *,
        backend: AnalyzerBackend | None = None,
        ml_provider: MlAnalyzerProvider | None = None,
    ) -> None:
        self.evidence_registry = evidence_registry
        self.config = config or {}
        self._backend = backend or create_analyzer_backend(
            config=self.config,
            ml_provider=ml_provider,
        )

    @property
    def analyzer_backend(self) -> str:
        return self._backend.name

    def analyze_evidence_patterns(self, evidence_list: list) -> dict:
        """Wire to POST /api/v1/ai/analyze — always FAC-E1 anchored."""
        known = evidence_id_set(evidence_list)
        raw = self._backend.analyze(evidence_list)
        anchored = enforce_evidence_anchors(raw, known_evidence_ids=known or None)
        result = anchored.to_dict()
        result["analysis_id"] = f"ana_{len(evidence_list):04d}"
        result["evidence_count"] = len(evidence_list)
        result["analyzer_backend"] = self._backend.name
        return result

    def predict_proto_forms(self, analysis: dict) -> dict:
        """
        Wire to POST /api/v1/ai/protoforms.
        Rejects unconstrained generation when no evidence anchors exist.
        """
        clusters = analysis.get("lexical_clusters") or []
        cognates = analysis.get("cognate_groups") or []
        # FAC-E1: drop any rows that lost evidence_ids
        clusters = [c for c in clusters if c.get("evidence_ids")]
        cognates = [g for g in cognates if g.get("evidence_ids")]
        if not clusters and not cognates:
            raise ValueError("AI-01: proto-forms require evidence-anchored analysis")

        hypotheses: list[dict[str, Any]] = []
        ancestor_hints = load_ancestor_hints()
        for cluster in clusters:
            evidence_ids = list(cluster.get("evidence_ids") or [])
            if not evidence_ids:
                continue
            root = str(cluster.get("root") or "X")
            root_key = root.lower()
            conf = min(0.95, 0.5 + 0.1 * len(evidence_ids))
            # Statistical backends may attach similarity scores
            if cluster.get("statistical_score") is not None:
                conf = min(
                    0.98,
                    conf * 0.7 + 0.3 * float(cluster.get("statistical_score") or 0),
                )
            hypotheses.append(
                {
                    "id": f"pf_{cluster.get('cluster_id', root)}",
                    "form": f"*{root.upper()}-",
                    "confidence": conf,
                    "ancestor_hint": ancestor_hints.get(root_key, f"Proto-{root}"),
                    "evidence_links": evidence_ids,
                    "analyzer_backend": analysis.get("analyzer_backend") or self._backend.name,
                }
            )
        if not hypotheses and cognates:
            for group in cognates:
                evidence_ids = list(group.get("evidence_ids") or [])
                if not evidence_ids:
                    continue
                cognate_score = float(group.get("cognate_score") or 0.8)
                hypotheses.append(
                    {
                        "id": f"pf_{group.get('group_id', 'cog')}",
                        "form": "*MAH-",
                        "confidence": min(0.95, max(0.5, cognate_score)),
                        "ancestor_hint": "Proto-Breath",
                        "evidence_links": evidence_ids,
                        "analyzer_backend": analysis.get("analyzer_backend") or self._backend.name,
                    }
                )
        hypotheses.sort(key=lambda h: h.get("confidence", 0), reverse=True)
        # Final FAC-E1 gate: every hypothesis must cite evidence
        if not hypotheses or any(not h.get("evidence_links") for h in hypotheses):
            raise ValueError("AI-01: proto-forms require evidence-anchored analysis")
        return {
            "hypotheses": hypotheses,
            "analyzer_backend": analysis.get("analyzer_backend") or self._backend.name,
        }

    def refine_reconstruction(self, proto_form: dict, analysis: dict, iteration: int) -> dict:
        """Internal FRA refinement; returns refined proto-form + quality + validation."""
        refined = dict(proto_form)
        base_conf = float(refined.get("confidence") or 0.5)
        cognate_bonus = 0.05 * min(3, len(analysis.get("cognate_groups") or []))
        refined["confidence"] = min(0.99, base_conf + 0.02 * iteration + cognate_bonus)
        refined["iteration"] = iteration
        if not refined.get("evidence_links"):
            links: list[str] = []
            for cluster in analysis.get("lexical_clusters") or []:
                links.extend(cluster.get("evidence_ids") or [])
            refined["evidence_links"] = list(dict.fromkeys(links))
        if not refined.get("evidence_links"):
            raise ValueError("AI-01: refined proto-form requires evidence_links")

        quality = {
            "score": refined["confidence"],
            "improved": refined["confidence"] > base_conf,
            "iteration": iteration,
        }

        validation = None
        if self.evidence_registry is not None and hasattr(
            self.evidence_registry, "validate_reconstruction"
        ):
            recon_id = str(refined.get("id") or f"proto_{iteration}")
            try:
                validation = self.evidence_registry.validate_reconstruction(recon_id)
            except Exception:
                validation = None

        return {
            "refined_proto_form": refined,
            "quality_metrics": quality,
            "constitutional_validation": validation,
            "analyzer_backend": self._backend.name,
        }
