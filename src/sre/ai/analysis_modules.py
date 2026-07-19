"""Rule-based analysis modules for evidence-constrained reconstruction."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from ..evidence.models import EvidenceType, LinguisticEvidence
from .sound_change import cognate_form_pairs, induce_sound_changes

_BREATH_GLOSS = re.compile(r"\b(breath|spirit|wind|air)\b", re.IGNORECASE)
_ROOT_PATTERN = re.compile(r"^(ma+h?r?a?h?)", re.IGNORECASE)

# IE stems covering kin, body, numbers, verbs (ie_cognate_mini_v01+)
_IE_STEMS: dict[str, re.Pattern[str]] = {
    "pater": re.compile(r"^(pater|padre|pere|pitar|phter)", re.I),
    "mater": re.compile(r"^(mater|madre|mere|matar|mehter)", re.I),
    "ped": re.compile(r"^(pes|ped|pie|pied|pad)", re.I),
    "kerd": re.compile(r"^(cor|cord|corazon|coeur|hrd|kerd|heart)", re.I),
    "okw": re.compile(r"^(oculus|ojo|oeil|aksi|eye)", re.I),
    "dent": re.compile(r"^(dens|dent|diente|dant|tooth)", re.I),
    "genu": re.compile(r"^(genu|rodilla|genou|janu|knee)", re.I),
    "eshr": re.compile(r"^(sanguis|sangre|sang|asrj|blood)", re.I),
    "oinos": re.compile(r"^(unus|uno|un|eka|one)", re.I),
    "duwo": re.compile(r"^(duo|dos|deux|dva|two)", re.I),
    "treyes": re.compile(r"^(tres|trois|tri|three)", re.I),
    "kwetwer": re.compile(r"^(quattuor|cuatro|quatre|catur|four)", re.I),
    "penkwe": re.compile(r"^(quinque|cinco|cinq|panca|five)", re.I),
    "es": re.compile(r"^(esse|est|ser|etre|as|be)", re.I),
    "bher": re.compile(r"^(ferre|llevar|porter|bhar|bear)", re.I),
    "gno": re.compile(r"^(gnoscere|conocer|connaitre|jna|know)", re.I),
    "ed": re.compile(r"^(edere|comer|manger|ad|eat)", re.I),
}


def _forms_from_evidence(evidence: LinguisticEvidence) -> list[str]:
    content = evidence.content
    forms: list[str] = []
    if content.get("form"):
        forms.append(str(content["form"]).lower())
    text = content.get("text")
    if text:
        forms.extend(tok.lower() for tok in str(text).split() if tok.isalpha())
    return forms


def _gloss_blob(evidence: LinguisticEvidence) -> str:
    content = evidence.content
    parts = [content.get("gloss"), content.get("meaning")]
    return " ".join(str(p) for p in parts if p)


def _normalize_root(form: str) -> str:
    form = form.lower()
    for stem, pattern in _IE_STEMS.items():
        if pattern.match(form):
            return stem
    match = _ROOT_PATTERN.match(form)
    if match:
        root = match.group(1)
        if root.startswith("mah") or root.startswith("mar") or root == "ma":
            return "mah"
        return root
    if form.startswith("ma"):
        return "mah"
    alpha = re.sub(r"[^a-z]", "", form)
    return alpha[:4] if alpha else form


def _meaning_key(evidence: LinguisticEvidence) -> str:
    gloss = _gloss_blob(evidence).lower().strip()
    if not gloss:
        return "general"
    primary = gloss.split(",")[0].strip().split()[0]
    return primary or "general"


class LexicalAnalyzer:
    """Lexical clustering by shared normalized root and meaning domain."""

    def analyze(self, evidence_list: list[Any]) -> list[dict[str, Any]]:
        clusters: dict[str, dict[str, Any]] = {}
        for evidence in evidence_list:
            if not isinstance(evidence, LinguisticEvidence):
                continue
            forms = _forms_from_evidence(evidence)
            gloss = _gloss_blob(evidence)
            meaning = _meaning_key(evidence)
            domain = "breath_spirit" if _BREATH_GLOSS.search(gloss) else meaning
            if not forms and meaning != "general":
                forms = [meaning]
            for form in forms:
                root = _normalize_root(form)
                key = f"{root}:{domain}"
                bucket = clusters.setdefault(
                    key,
                    {
                        "cluster_id": key,
                        "root": root,
                        "domain": domain,
                        "forms": [],
                        "evidence_ids": [],
                    },
                )
                if form not in bucket["forms"]:
                    bucket["forms"].append(form)
                if evidence.evidence_id not in bucket["evidence_ids"]:
                    bucket["evidence_ids"].append(evidence.evidence_id)
        return list(clusters.values())


class PhonologicalAnalyzer:
    """
    Infer phonological shifts from:
    1. Attested phonological_rule evidence
    2. Induced pairwise sound changes across cognate groups
    """

    def __init__(self, cognate_detector: CognateDetector | None = None) -> None:
        self._cognates = cognate_detector or CognateDetector()

    def analyze(self, evidence_list: list[Any]) -> list[dict[str, Any]]:
        shifts: list[dict[str, Any]] = []
        seen: set[str] = set()

        for evidence in evidence_list:
            if not isinstance(evidence, LinguisticEvidence):
                continue
            if evidence.evidence_type == EvidenceType.PHONOLOGICAL_RULE:
                rule = str(evidence.content.get("rule") or "")
                if rule and rule not in seen:
                    seen.add(rule)
                    shifts.append(
                        {
                            "rule": rule,
                            "evidence_ids": [evidence.evidence_id],
                            "source": "attested_rule",
                            "support": 1,
                            "score": 10.0,
                        }
                    )

        # Stronger search: induce rules from cognate alignments
        groups = self._cognates.detect(evidence_list)
        all_pairs: list[tuple[str, str, str, str]] = []
        for group in groups:
            all_pairs.extend(cognate_form_pairs(group.get("members") or []))

        induced = induce_sound_changes(all_pairs, min_support=1)
        for item in induced:
            rule = item["rule"]
            if rule in seen:
                continue
            seen.add(rule)
            shifts.append(item)

        shifts.sort(
            key=lambda s: (
                -float(s.get("score") or s.get("support") or 0),
                s.get("source") != "attested_rule",
                s.get("rule", ""),
            )
        )
        return shifts


class CognateDetector:
    """Detect cognate groups by shared meaning and/or known IE stems."""

    def detect(self, evidence_list: list[Any]) -> list[dict[str, Any]]:
        groups: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "group_id": "",
                "members": [],
                "evidence_ids": [],
                "meanings": [],
            }
        )
        for evidence in evidence_list:
            if not isinstance(evidence, LinguisticEvidence):
                continue
            gloss = _gloss_blob(evidence)
            meaning = _meaning_key(evidence)
            forms = _forms_from_evidence(evidence)
            if not forms and meaning == "general":
                continue
            if not forms:
                forms = [meaning]

            for form in forms:
                root = _normalize_root(form)
                key = meaning if meaning != "general" else root
                if _BREATH_GLOSS.search(gloss):
                    key = "mah"
                group = groups[key]
                group["group_id"] = f"cognate_{key}"
                member = {
                    "form": form,
                    "language": evidence.content.get("language_code"),
                    "period": evidence.content.get("period"),
                    "evidence_id": evidence.evidence_id,
                }
                group["members"].append(member)
                if evidence.evidence_id not in group["evidence_ids"]:
                    group["evidence_ids"].append(evidence.evidence_id)
                if gloss and gloss not in group["meanings"]:
                    group["meanings"].append(gloss)
        return [g for g in groups.values() if len(g["members"]) >= 1]
