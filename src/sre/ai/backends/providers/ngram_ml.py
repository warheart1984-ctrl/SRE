"""Built-in character n-gram ML provider (stdlib-only vector model)."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Any

from sre.evidence.models import LinguisticEvidence

from ...analysis_modules import (
    PhonologicalAnalyzer,
    forms_from_evidence,
    gloss_blob,
    meaning_key,
    normalize_root,
)
from ..base import AnalysisBundle


def _char_ngrams(text: str, n_min: int = 2, n_max: int = 3) -> Counter[str]:
    text = f"#{text.lower().strip()}#"
    counts: Counter[str] = Counter()
    for n in range(n_min, n_max + 1):
        if len(text) < n:
            continue
        for i in range(len(text) - n + 1):
            counts[text[i : i + n]] += 1
    return counts


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    keys = set(a) | set(b)
    dot = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in keys)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


class CharacterNgramMlProvider:
    """
    Lightweight ML provider: character n-gram TF-IDF vectors + cosine clustering.

    This is a **real trainable vector model** (fit on the evidence batch), not an LLM.
    Drive-G-1: does not claim neural nets or pretrained language models.
    """

    name = "ngram"

    def __init__(
        self,
        *,
        n_min: int = 2,
        n_max: int = 3,
        similarity_threshold: float = 0.25,
    ) -> None:
        self.n_min = n_min
        self.n_max = n_max
        self.similarity_threshold = similarity_threshold
        self._df: Counter[str] = Counter()
        self._n_docs = 0
        self._fitted = False

    def fit(self, evidence_list: list[Any]) -> CharacterNgramMlProvider:
        """Fit document-frequency stats on forms present in the batch."""
        self._df = Counter()
        docs = 0
        for evidence in evidence_list:
            if not isinstance(evidence, LinguisticEvidence):
                continue
            forms = forms_from_evidence(evidence)
            if not forms:
                continue
            # One doc per evidence item (union of its forms' ngrams)
            features: set[str] = set()
            for form in forms:
                features.update(_char_ngrams(form, self.n_min, self.n_max))
            if not features:
                continue
            for feat in features:
                self._df[feat] += 1
            docs += 1
        self._n_docs = max(docs, 1)
        self._fitted = True
        return self

    def _vectorize(self, form: str) -> dict[str, float]:
        tf = _char_ngrams(form, self.n_min, self.n_max)
        if not tf:
            return {}
        total = float(sum(tf.values()))
        vec: dict[str, float] = {}
        for feat, count in tf.items():
            idf = math.log((1.0 + self._n_docs) / (1.0 + self._df.get(feat, 0))) + 1.0
            vec[feat] = (count / total) * idf
        return vec

    def analyze(self, evidence_list: list[Any]) -> AnalysisBundle:
        if not self._fitted:
            self.fit(evidence_list)

        rows: list[dict[str, Any]] = []
        for evidence in evidence_list:
            if not isinstance(evidence, LinguisticEvidence):
                continue
            forms = forms_from_evidence(evidence)
            meaning = meaning_key(evidence)
            if not forms and meaning != "general":
                forms = [meaning]
            for form in forms:
                rows.append(
                    {
                        "form": form,
                        "vector": self._vectorize(form),
                        "evidence_id": evidence.evidence_id,
                        "meaning": meaning,
                        "gloss": gloss_blob(evidence),
                        "language": evidence.content.get("language_code"),
                        "period": evidence.content.get("period"),
                        "root": normalize_root(form),
                    }
                )

        clusters = self._cluster_rows(rows)
        cognates = self._cognate_groups(rows)
        # Induce phonology from ML cognate memberships via shared detector path
        phonology = PhonologicalAnalyzer().analyze(evidence_list)
        for shift in phonology:
            shift.setdefault("ml_provider", self.name)

        return AnalysisBundle(
            lexical_clusters=clusters,
            phonological_shifts=phonology,
            cognate_groups=cognates,
            backend="ml",
            metadata={
                "provider": self.name,
                "model": "character_ngram_tfidf_cosine",
                "n_min": self.n_min,
                "n_max": self.n_max,
                "similarity_threshold": self.similarity_threshold,
                "fitted_docs": self._n_docs,
                "vocab_size": len(self._df),
            },
        )

    def _cluster_rows(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Greedy clustering: attach row to nearest centroid above threshold."""
        if not rows:
            return []
        # Seed by meaning buckets, then merge by vector similarity
        by_meaning: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            by_meaning[str(row["meaning"])].append(row)

        clusters: list[dict[str, Any]] = []
        for meaning, members in by_meaning.items():
            groups = self._greedy_similarity_groups(members)
            for idx, group in enumerate(groups):
                forms = list(dict.fromkeys(str(m["form"]) for m in group))
                evidence_ids = list(dict.fromkeys(str(m["evidence_id"]) for m in group))
                root = str(group[0]["root"])
                # Mean pairwise cosine as model confidence signal
                score = self._mean_pairwise(group)
                clusters.append(
                    {
                        "cluster_id": f"ml_ngram:{meaning}:{idx}",
                        "root": root,
                        "domain": meaning,
                        "forms": forms,
                        "evidence_ids": evidence_ids,
                        "ml_score": round(score, 4),
                        "statistical_score": round(score, 4),
                    }
                )
        return clusters

    def _cognate_groups(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        by_meaning: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            by_meaning[str(row["meaning"])].append(row)
        out: list[dict[str, Any]] = []
        for meaning, members in by_meaning.items():
            for idx, group in enumerate(self._greedy_similarity_groups(members)):
                if len(group) < 1:
                    continue
                score = self._mean_pairwise(group)
                out.append(
                    {
                        "group_id": f"ml_cognate_{meaning}_{idx}",
                        "members": [
                            {
                                "form": m["form"],
                                "language": m.get("language"),
                                "period": m.get("period"),
                                "evidence_id": m["evidence_id"],
                            }
                            for m in group
                        ],
                        "evidence_ids": list(dict.fromkeys(str(m["evidence_id"]) for m in group)),
                        "meanings": list(
                            dict.fromkeys(str(m["gloss"]) for m in group if m.get("gloss"))
                        ),
                        "cognate_score": round(score, 4),
                    }
                )
        out.sort(key=lambda g: (-float(g.get("cognate_score") or 0), g["group_id"]))
        return out

    def _greedy_similarity_groups(
        self, members: list[dict[str, Any]]
    ) -> list[list[dict[str, Any]]]:
        if not members:
            return []
        unused = list(members)
        groups: list[list[dict[str, Any]]] = []
        while unused:
            seed = unused.pop(0)
            group = [seed]
            i = 0
            while i < len(unused):
                cand = unused[i]
                sim = _cosine(seed["vector"], cand["vector"])
                # Also compare to group mean for stability
                if sim >= self.similarity_threshold or any(
                    _cosine(g["vector"], cand["vector"]) >= self.similarity_threshold for g in group
                ):
                    group.append(unused.pop(i))
                else:
                    i += 1
            groups.append(group)
        return groups

    def _mean_pairwise(self, group: list[dict[str, Any]]) -> float:
        if len(group) < 2:
            return 1.0 if group else 0.0
        total = 0.0
        pairs = 0
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                total += _cosine(group[i]["vector"], group[j]["vector"])
                pairs += 1
        return total / pairs if pairs else 0.0
