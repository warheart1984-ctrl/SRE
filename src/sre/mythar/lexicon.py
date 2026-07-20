"""Mythar living lexicon — load, clusters, gap-fill, Proto-World compare."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..corpus.loader import seed_registry_from_corpus
from ..evidence.models import LinguisticEvidence
from ..evidence.registry import EvidenceRegistry
from .data import DEFAULT_LEXICON_PATH, build_lexicon_document, write_lexicon_json

DOMAINS = ("kinship", "body", "motion", "abstract", "nature")
DEFAULT_LEXICON = DEFAULT_LEXICON_PATH


class MytharLexicon:
    """Load and query the Mythar Living Lexicon (clusters 12–48)."""

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path else DEFAULT_LEXICON
        if self.path.is_file():
            self._data = json.loads(self.path.read_text(encoding="utf-8"))
        else:
            self._data = build_lexicon_document()
            try:
                write_lexicon_json(self.path)
            except OSError:
                pass

    @property
    def lexicon_id(self) -> str:
        return str(self._data.get("lexicon_id", ""))

    @property
    def source_reference(self) -> str:
        return str(self._data.get("source_reference", ""))

    @property
    def raw(self) -> dict[str, Any]:
        return self._data

    def roots(self) -> list[dict[str, Any]]:
        return list(self._data.get("roots") or [])

    def clusters(self) -> list[dict[str, Any]]:
        return list(self._data.get("clusters") or [])

    def cluster_ids(self) -> list[int]:
        return [int(c["cluster_id"]) for c in self.clusters()]

    def list_clusters(self) -> list[dict[str, Any]]:
        """Return cluster summaries for gap-fill / inventory (includes 47–48)."""
        return [
            {
                "cluster_id": int(c["cluster_id"]),
                "name": c.get("name"),
                "forms": c.get("forms"),
                "phrase": c.get("phrase"),
                "domain": c.get("domain"),
                "interpretation": c.get("interpretation"),
            }
            for c in self.clusters()
        ]

    def get_cluster(self, cluster_id: int) -> dict[str, Any] | None:
        for c in self.clusters():
            if int(c["cluster_id"]) == cluster_id:
                return c
        return None

    def clusters_by_domain(self, domain: str) -> list[dict[str, Any]]:
        return [c for c in self.clusters() if c.get("domain") == domain]

    def root_forms(self) -> set[str]:
        return {str(r["form"]) for r in self.roots()}

    def evidence_ids(self) -> list[str]:
        ids: list[str] = []
        for lang in self._data.get("languages") or []:
            for period in lang.get("periods") or []:
                for item in period.get("evidence") or []:
                    ids.append(str(item["evidence_id"]))
        return ids

    def gap_fill(self, *, focus_domains: list[str] | None = None) -> dict[str, Any]:
        domains = focus_domains or list(DOMAINS)
        covered = {d: self.clusters_by_domain(d) for d in domains}
        root_by_domain: dict[str, list[str]] = {d: [] for d in domains}
        for r in self.roots():
            d = str(r.get("domain") or "abstract")
            if d in root_by_domain:
                root_by_domain[d].append(str(r["form"]))

        suggestions: list[dict[str, Any]] = []
        for d in domains:
            n_clusters = len(covered[d])
            n_roots = len(root_by_domain[d])
            status = "covered" if n_clusters >= 5 and n_roots >= 4 else "thin"
            suggestions.append(
                {
                    "domain": d,
                    "cluster_count": n_clusters,
                    "root_count": n_roots,
                    "status": status,
                    "proposed_roots": root_by_domain[d][:8],
                    "proposed_clusters": [
                        {
                            "cluster_id": c["cluster_id"],
                            "forms": c["forms"],
                            "phrase": c["phrase"],
                        }
                        for c in covered[d][:3]
                    ],
                }
            )
        return {
            "mode": "gap_fill",
            "lexicon_id": self.lexicon_id,
            "domains": suggestions,
            "invocation": self._data.get("invocation"),
        }

    def compare_proto_world(self) -> list[dict[str, Any]]:
        return list(self._data.get("proto_world_comparisons") or [])

    def seed_registry(
        self, registry: EvidenceRegistry
    ) -> list[LinguisticEvidence]:
        if not self.path.is_file():
            write_lexicon_json(self.path)
        return seed_registry_from_corpus(
            registry,
            path=self.path,
            search_catalog=False,
        )
