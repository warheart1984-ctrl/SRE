"""Correspondence-driven sound-change search (linguistics-only; no Dantomax)."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any

from .alignment import AlignCell, weighted_align
from .tokenization import tokenize, tokens_to_str


@dataclass
class CorrespondenceSet:
    pattern: tuple[str, ...]  # ordered by language key
    languages: tuple[str, ...]
    count: int
    environments: list[str] = field(default_factory=list)


@dataclass
class ProtoHypothesis:
    proto_form: str
    confidence: float
    supporting_attestation_ids: list[str]
    aligned_daughter_forms: dict[str, str]
    correspondence_sets: list[dict[str, Any]]
    sound_change_sequence: list[dict[str, Any]]
    competing_hypotheses: list[dict[str, Any]]
    unresolved_conflicts: list[str]
    leave_one_out: dict[str, Any]
    flags: list[str] = field(default_factory=list)
    regularity_score: float = 0.0
    exception_penalty: float = 0.0


# Branch-specific directional transforms (proto → daughter heuristics)
BRANCH_TRANSFORMS: dict[str, list[tuple[str, str, str]]] = {
    "lat": [("p", "p", "retain"), ("bh", "f", "italic_aspirate"), ("dh", "f", "italic_aspirate")],
    "grc": [("bh", "ph", "greek_aspirate"), ("dh", "th", "greek_aspirate"), ("gh", "kh", "greek_aspirate")],
    "skt": [("e", "a", "indo_iranian_a"), ("o", "a", "indo_iranian_a")],
    "got": [("p", "f", "grimm"), ("t", "þ", "grimm"), ("k", "h", "grimm")],
    "ang": [("p", "f", "grimm"), ("t", "þ", "grimm"), ("k", "h", "grimm")],
    "sga": [("p", "", "celtic_p_loss"), ("kw", "k", "celtic_kw")],
    "cu": [("s", "s", "retain"), ("k", "k", "retain")],
    "lit": [("k", "k", "retain"), ("s", "s", "retain")],
    "hit": [("h", "ḫ", "anatolian_h"), ("e", "e", "retain")],
    "txb": [("k", "k", "retain"), ("p", "p", "retain")],
}


class CorrespondenceEngine:
    """Discover recurring correspondences and rank competing proto-forms."""

    def __init__(
        self,
        *,
        min_correspondence_count: int = 2,
        borrowing_penalty: float = 0.25,
        analogy_penalty: float = 0.15,
        irregularity_penalty: float = 0.2,
    ) -> None:
        self.min_correspondence_count = min_correspondence_count
        self.borrowing_penalty = borrowing_penalty
        self.analogy_penalty = analogy_penalty
        self.irregularity_penalty = irregularity_penalty

    def reconstruct_set(
        self,
        forms: dict[str, str],
        *,
        attestation_ids: dict[str, list[str]] | None = None,
        flags_by_lang: dict[str, list[str]] | None = None,
        known_proto: str | None = None,
        directionality: str = "proto_to_daughter",
    ) -> list[ProtoHypothesis]:
        """
        Generate confidence-ranked proto hypotheses for a cognate set.

        forms: language_code → surface form (normalized or original)
        """
        attestation_ids = attestation_ids or {}
        flags_by_lang = flags_by_lang or {}
        langs = sorted(forms.keys())
        if len(langs) < 2:
            return []

        alignments = self._pairwise_alignments(forms)
        corr_sets = self._discover_correspondences(forms, alignments)
        primary = self._majority_vote_proto(forms, corr_sets)
        alternatives = self._generate_competitors(forms, primary, known_proto)

        all_ids: list[str] = []
        for ids in attestation_ids.values():
            all_ids.extend(ids)

        hypotheses: list[ProtoHypothesis] = []
        for proto, base_conf, label in alternatives:
            seq = self._infer_sound_changes(proto, forms, directionality=directionality)
            reg, exc, conflicts, hyp_flags = self._score_regularity(
                proto, forms, seq, flags_by_lang, corr_sets
            )
            loo = self._leave_one_out(forms, proto)
            conf = max(
                0.0,
                min(
                    1.0,
                    base_conf * reg - exc
                    - self._flag_penalties(flags_by_lang)
                    + (0.05 if loo.get("recovered") else 0.0),
                ),
            )
            competitors = [
                {"proto_form": p, "label": lab, "confidence": round(c, 4)}
                for p, c, lab in alternatives
                if p != proto
            ]
            hypotheses.append(
                ProtoHypothesis(
                    proto_form=proto,
                    confidence=round(conf, 4),
                    supporting_attestation_ids=list(dict.fromkeys(all_ids)),
                    aligned_daughter_forms=dict(forms),
                    correspondence_sets=[
                        {
                            "pattern": list(cs.pattern),
                            "languages": list(cs.languages),
                            "count": cs.count,
                            "environments": cs.environments[:5],
                        }
                        for cs in corr_sets[:12]
                    ],
                    sound_change_sequence=seq,
                    competing_hypotheses=competitors,
                    unresolved_conflicts=conflicts,
                    leave_one_out=loo,
                    flags=sorted(set(hyp_flags)),
                    regularity_score=round(reg, 4),
                    exception_penalty=round(exc, 4),
                )
            )

        hypotheses.sort(key=lambda h: h.confidence, reverse=True)
        # annotate competing list on each with others' scores
        for h in hypotheses:
            h.competing_hypotheses = [
                {
                    "proto_form": o.proto_form,
                    "confidence": o.confidence,
                    "flags": o.flags,
                }
                for o in hypotheses
                if o.proto_form != h.proto_form
            ]
        return hypotheses

    def _pairwise_alignments(
        self, forms: dict[str, str]
    ) -> dict[tuple[str, str], list[AlignCell]]:
        out: dict[tuple[str, str], list[AlignCell]] = {}
        langs = list(forms.keys())
        for i, la in enumerate(langs):
            for lb in langs[i + 1 :]:
                ta, tb = tokenize(forms[la]), tokenize(forms[lb])
                path, _ = weighted_align(ta, tb)
                out[(la, lb)] = path
        return out

    def _discover_correspondences(
        self,
        forms: dict[str, str],
        alignments: dict[tuple[str, str], list[AlignCell]],
    ) -> list[CorrespondenceSet]:
        # Build per-position multi-language columns from pairwise alignments
        # Heuristic: collect recurring symbol tuples across language pairs
        pair_counts: Counter[tuple[str, str, str, str]] = Counter()
        envs: dict[tuple[str, str, str, str], list[str]] = defaultdict(list)
        for (la, lb), path in alignments.items():
            prev_a = "#"
            for cell in path:
                if cell.a and cell.b:
                    key = (la, cell.a.symbol, lb, cell.b.symbol)
                    pair_counts[key] += 1
                    envs[key].append(f"{prev_a}_")
                    prev_a = cell.a.symbol
                elif cell.a:
                    prev_a = cell.a.symbol
        sets: list[CorrespondenceSet] = []
        for (la, sa, lb, sb), cnt in pair_counts.most_common(40):
            if cnt < self.min_correspondence_count and sa != sb:
                continue
            langs = tuple(sorted([la, lb]))
            pattern = (sa, sb) if la <= lb else (sb, sa)
            sets.append(
                CorrespondenceSet(
                    pattern=pattern,
                    languages=langs,
                    count=cnt,
                    environments=envs[(la, sa, lb, sb)],
                )
            )
        return sets

    def _majority_vote_proto(
        self, forms: dict[str, str], corr_sets: list[CorrespondenceSet]
    ) -> str:
        # Prefer longest shared prefix/suffix skeleton via tokenization vote
        tokenized = {lang: tokenize(f) for lang, f in forms.items()}
        max_len = max(len(t) for t in tokenized.values())
        chars: list[str] = []
        for i in range(max_len):
            votes: Counter[str] = Counter()
            for toks in tokenized.values():
                if i < len(toks):
                    votes[toks[i].symbol] += 1
            if not votes:
                break
            top, n = votes.most_common(1)[0]
            # require relative agreement
            if n >= max(1, len(tokenized) // 2):
                chars.append(top)
            elif len(votes) >= 2 and votes.most_common(2)[0][1] == votes.most_common(2)[1][1]:
                # tie → keep first alphabetically for determinism, mark later
                chars.append(sorted(votes.keys())[0])
            else:
                chars.append(top)
        proto = "".join(chars)
        return proto or next(iter(forms.values()))

    def _generate_competitors(
        self,
        forms: dict[str, str],
        primary: str,
        known_proto: str | None,
    ) -> list[tuple[str, float, str]]:
        alts: list[tuple[str, float, str]] = [(primary, 0.72, "majority_vote")]
        # length-trimmed competitor
        if len(primary) > 2:
            alts.append((primary[:-1], 0.55, "trimmed_final"))
        # longest daughter as conservative
        longest = max(forms.values(), key=len)
        if longest != primary:
            alts.append((longest, 0.48, "conservative_daughter"))
        # shortest as eroded hypothesis
        shortest = min(forms.values(), key=len)
        if shortest not in {primary, longest}:
            alts.append((shortest, 0.35, "eroded"))
        if known_proto:
            alts.insert(0, (known_proto.lstrip("*"), 0.88, "scholarly_prior"))
        # dedupe by form keeping best base confidence
        best: dict[str, tuple[float, str]] = {}
        for form, conf, label in alts:
            if form not in best or conf > best[form][0]:
                best[form] = (conf, label)
        return [(f, c, lab) for f, (c, lab) in best.items()]

    def _infer_sound_changes(
        self,
        proto: str,
        forms: dict[str, str],
        *,
        directionality: str,
    ) -> list[dict[str, Any]]:
        seq: list[dict[str, Any]] = []
        ptoks = tokenize(proto)
        for lang, form in sorted(forms.items()):
            dtoks = tokenize(form)
            path, cost = weighted_align(ptoks, dtoks)
            for cell in path:
                if cell.op == "eq":
                    continue
                rule = {
                    "branch": lang,
                    "from": cell.a.symbol if cell.a else "∅",
                    "to": cell.b.symbol if cell.b else "∅",
                    "op": cell.op,
                    "cost": round(cell.cost, 4),
                    "direction": directionality,
                }
                # annotate known branch transforms
                for src, dst, name in BRANCH_TRANSFORMS.get(lang, []):
                    if cell.a and cell.b and cell.a.symbol == src and cell.b.symbol == dst:
                        rule["named_transform"] = name
                seq.append(rule)
            seq.append(
                {
                    "branch": lang,
                    "summary": "align_cost",
                    "cost": round(cost, 4),
                    "direction": directionality,
                }
            )
        return seq

    def _score_regularity(
        self,
        proto: str,
        forms: dict[str, str],
        seq: list[dict[str, Any]],
        flags_by_lang: dict[str, list[str]],
        corr_sets: list[CorrespondenceSet],
    ) -> tuple[float, float, list[str], list[str]]:
        named = sum(1 for s in seq if "named_transform" in s)
        ops = [s for s in seq if s.get("op")]
        irregular_ops = sum(1 for s in ops if s.get("op") in {"ins", "del"} and s.get("cost", 0) > 1.0)
        recurring = sum(1 for cs in corr_sets if cs.count >= self.min_correspondence_count)
        reg = 0.45 + 0.1 * min(named, 3) + 0.05 * min(recurring, 4)
        reg = min(1.0, reg)
        exc = irregular_ops * self.irregularity_penalty * 0.15
        conflicts: list[str] = []
        hyp_flags: list[str] = []
        for lang, flags in flags_by_lang.items():
            for fl in flags:
                hyp_flags.append(f"{lang}:{fl}")
                if fl in {"borrowed", "analogy", "disputed", "uncertain", "irregular"}:
                    conflicts.append(f"{lang} flagged {fl}")
                    if fl == "borrowed":
                        exc += self.borrowing_penalty
                    elif fl == "analogy":
                        exc += self.analogy_penalty
                    else:
                        exc += self.irregularity_penalty * 0.5
        # accidental similarity: high align cost with few recurring corrs
        avg_cost = 0.0
        cost_n = 0
        for s in seq:
            if s.get("summary") == "align_cost":
                avg_cost += float(s["cost"])
                cost_n += 1
        if cost_n:
            avg_cost /= cost_n
        if avg_cost > 3.0 and recurring < 2:
            conflicts.append("possible_accidental_similarity")
            hyp_flags.append("accidental_similarity_risk")
            exc += 0.2
        return reg, exc, conflicts, hyp_flags

    def _flag_penalties(self, flags_by_lang: dict[str, list[str]]) -> float:
        pen = 0.0
        for flags in flags_by_lang.values():
            for fl in flags:
                if fl == "borrowed":
                    pen += self.borrowing_penalty
                elif fl == "analogy":
                    pen += self.analogy_penalty
                elif fl in {"disputed", "uncertain", "irregular", "unattested"}:
                    pen += self.irregularity_penalty * 0.4
        return pen

    def _leave_one_out(self, forms: dict[str, str], proto: str) -> dict[str, Any]:
        """Withhold one language; check whether proto still predicts a plausible form."""
        if len(forms) < 3:
            return {"applicable": False, "recovered": False}
        # withhold the longest form language
        withhold_lang = max(forms.keys(), key=lambda k: len(forms[k]))
        remaining = {k: v for k, v in forms.items() if k != withhold_lang}
        # re-vote proto from remaining
        alt = self._majority_vote_proto(remaining, [])
        withheld = forms[withhold_lang]
        # recovery: shared character overlap / edit proximity
        pt, wt = tokenize(alt), tokenize(withheld)
        path, cost = weighted_align(pt, wt)
        max_len = max(len(pt), len(wt), 1)
        similarity = 1.0 - (cost / (max_len * 1.1))
        recovered = similarity >= 0.45 or tokens_to_str(pt)[:2] == tokens_to_str(wt)[:2]
        return {
            "applicable": True,
            "withheld_language": withhold_lang,
            "withheld_form": withheld,
            "predicted_from_remainder": alt,
            "similarity": round(similarity, 4),
            "recovered": recovered,
            "alignment_cost": round(cost, 4),
            "reference_proto": proto,
        }
