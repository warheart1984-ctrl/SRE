"""Statistical analyzer backend — stdlib similarity, no ML deps."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from ...evidence.models import LinguisticEvidence
from ..analysis_modules import (
    CognateDetector,
    LexicalAnalyzer,
    PhonologicalAnalyzer,
    forms_from_evidence,
    gloss_blob,
    meaning_key,
)
from ..cognate_scoring import cognate_pair_score, rank_cognate_groups
from .base import AnalysisBundle, AnalyzerBackend


class StatisticalAnalyzerBackend:
    """
    Meaning-seeded clusters refined by pairwise form similarity scores.

    Still rule-seeded for domains; ranking and weak-pair filtering use
    ``cognate_scoring`` (edit distance + bigram Dice).
    """

    name = "statistical"

    def __init__(self, *, min_pair_score: float = 0.35) -> None:
        self._min_pair_score = min_pair_score
        self._lexical = LexicalAnalyzer()
        self._base_cognates = CognateDetector()
        self._phonology = PhonologicalAnalyzer(cognate_detector=self._base_cognates)

    def analyze(self, evidence_list: list[Any]) -> AnalysisBundle:
        lexical = self._lexical.analyze(evidence_list)
        # Re-score lexical clusters by mean form similarity when multi-form
        enriched_lex: list[dict[str, Any]] = []
        for cluster in lexical:
            forms = list(cluster.get("forms") or [])
            if len(forms) >= 2:
                total = 0.0
                pairs = 0
                for i in range(len(forms)):
                    for j in range(i + 1, len(forms)):
                        total += cognate_pair_score(forms[i], forms[j])
                        pairs += 1
                cluster = dict(cluster)
                cluster["statistical_score"] = round(total / pairs if pairs else 0.0, 4)
            else:
                cluster = dict(cluster)
                cluster["statistical_score"] = 0.0
            enriched_lex.append(cluster)

        cognates = self._statistical_cognates(evidence_list)
        phonology = self._phonology.analyze(evidence_list)
        # Attach statistical cognate scores onto induced shifts when possible
        for shift in phonology:
            shift.setdefault("backend_hint", self.name)

        return AnalysisBundle(
            lexical_clusters=enriched_lex,
            phonological_shifts=phonology,
            cognate_groups=cognates,
            backend=self.name,
            metadata={
                "strategy": "edit_distance_and_bigram_dice",
                "min_pair_score": self._min_pair_score,
            },
        )

    def _statistical_cognates(self, evidence_list: list[Any]) -> list[dict[str, Any]]:
        """Seed by meaning, then keep pairs/groups that pass similarity threshold."""
        by_meaning: dict[str, list[LinguisticEvidence]] = defaultdict(list)
        for evidence in evidence_list:
            if not isinstance(evidence, LinguisticEvidence):
                continue
            meaning = meaning_key(evidence)
            by_meaning[meaning].append(evidence)

        groups: list[dict[str, Any]] = []
        for meaning, items in by_meaning.items():
            members: list[dict[str, Any]] = []
            evidence_ids: list[str] = []
            meanings: list[str] = []
            for evidence in items:
                gloss = gloss_blob(evidence)
                forms = forms_from_evidence(evidence) or ([meaning] if meaning != "general" else [])
                for form in forms:
                    members.append(
                        {
                            "form": form,
                            "language": evidence.content.get("language_code"),
                            "period": evidence.content.get("period"),
                            "evidence_id": evidence.evidence_id,
                        }
                    )
                if evidence.evidence_id not in evidence_ids:
                    evidence_ids.append(evidence.evidence_id)
                if gloss and gloss not in meanings:
                    meanings.append(gloss)

            if not members:
                continue
            # Drop weak multi-form groups by filtering members to cohesive pairs
            if len(members) >= 2:
                kept = self._filter_cohesive_members(members)
                if not kept:
                    continue
                members = kept
                evidence_ids = list(
                    dict.fromkeys(str(m["evidence_id"]) for m in members if m.get("evidence_id"))
                )
            groups.append(
                {
                    "group_id": f"stat_cognate_{meaning}",
                    "members": members,
                    "evidence_ids": evidence_ids,
                    "meanings": meanings,
                }
            )
        return rank_cognate_groups(groups, min_score=self._min_pair_score)

    def _filter_cohesive_members(self, members: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Keep members that share at least one strong pairwise link."""
        n = len(members)
        linked = [False] * n
        for i in range(n):
            for j in range(i + 1, n):
                score = cognate_pair_score(
                    str(members[i].get("form") or ""),
                    str(members[j].get("form") or ""),
                )
                if score >= self._min_pair_score:
                    linked[i] = True
                    linked[j] = True
        kept = [m for m, ok in zip(members, linked) if ok]
        return kept if kept else members[:1]


_: AnalyzerBackend = StatisticalAnalyzerBackend()
