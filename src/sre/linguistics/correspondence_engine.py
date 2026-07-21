"""Correspondence-driven sound-change search (linguistics-only; no Dantomax)."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any

from .alignment import AlignCell, weighted_align
from .features import feature_distance, segment
from .tokenization import tokenize, tokens_to_str


@dataclass
class CorrespondenceSet:
    pattern: tuple[str, ...]
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
# Format: (proto_segment, daughter_segment, rule_name)
BRANCH_TRANSFORMS: dict[str, list[tuple[str, str, str]]] = {
    # Italic / Latin
    "lat": [
        ("p", "p", "retain"),
        ("b", "b", "retain"),
        ("t", "t", "retain"),
        ("d", "d", "retain"),
        ("k", "k", "retain"),
        ("g", "g", "retain"),
        ("kʷ", "kw", "labiovelar_retain"),
        ("bʰ", "f", "italic_aspirate"),
        ("dʰ", "f", "italic_aspirate"),
        ("gʰ", "h", "italic_gh"),
        ("s", "s", "retain"),
        ("m", "m", "retain"),
        ("n", "n", "retain"),
        ("r", "r", "retain"),
        ("l", "l", "retain"),
        ("j", "j", "retain"),
    ],
    # Greek
    "grc": [
        ("p", "p", "retain"),
        ("b", "b", "retain"),
        ("t", "t", "retain"),
        ("d", "d", "retain"),
        ("k", "k", "retain"),
        ("g", "g", "retain"),
        ("kʷ", "p", "greek_labiovelar_p"),
        ("gʷ", "b", "greek_labiovelar_b"),
        ("bʰ", "pʰ", "greek_aspirate"),
        ("dʰ", "tʰ", "greek_aspirate"),
        ("gʰ", "kʰ", "greek_aspirate"),
        ("s", "h", "greek_s_aspiration"),
        ("m", "m", "retain"),
        ("n", "n", "retain"),
    ],
    # Sanskrit
    "skt": [
        ("p", "p", "retain"),
        ("b", "b", "retain"),
        ("t", "t", "retain"),
        ("d", "d", "retain"),
        ("k", "k", "retain"),
        ("g", "g", "retain"),
        ("kʷ", "k", "indo_iranian_kw_k"),
        ("gʷ", "g", "indo_iranian_gw_g"),
        ("bʰ", "bʰ", "retain_aspirate"),
        ("dʰ", "dʰ", "retain_aspirate"),
        ("gʰ", "gʰ", "retain_aspirate"),
        ("e", "a", "indo_iranian_a"),
        ("o", "a", "indo_iranian_a"),
        ("s", "s", "retain"),
        ("m", "m", "retain"),
        ("n", "n", "retain"),
        ("l", "r", "skt_l_r"),
        ("r", "r", "retain"),
    ],
    # Gothic (Germanic)
    "got": [
        ("p", "f", "grimm_p"),
        ("t", "þ", "grimm_t"),
        ("k", "h", "grimm_k"),
        ("b", "p", "grimm_b"),
        ("d", "t", "grimm_d"),
        ("g", "k", "grimm_g"),
        ("bʰ", "b", "grimm_aspirate"),
        ("dʰ", "d", "grimm_aspirate"),
        ("gʰ", "g", "grimm_aspirate"),
        ("s", "s", "retain"),
        ("m", "m", "retain"),
        ("n", "n", "retain"),
        ("r", "r", "retain"),
        ("l", "l", "retain"),
    ],
    # Old English (Germanic)
    "ang": [
        ("p", "f", "grimm_p"),
        ("t", "þ", "grimm_t"),
        ("k", "h", "grimm_k"),
        ("b", "p", "grimm_b"),
        ("d", "t", "grimm_d"),
        ("g", "k", "grimm_g"),
        ("bʰ", "b", "grimm_aspirate"),
        ("dʰ", "d", "grimm_aspirate"),
        ("gʰ", "g", "grimm_aspirate"),
        ("s", "s", "retain"),
    ],
    # Old Norse
    "non": [
        ("p", "f", "grimm_p"),
        ("t", "þ", "grimm_t"),
        ("k", "h", "grimm_k"),
        ("b", "p", "grimm_b"),
        ("d", "t", "grimm_d"),
        ("g", "k", "grimm_g"),
        ("bʰ", "b", "grimm_aspirate"),
        ("dʰ", "d", "grimm_aspirate"),
        ("gʰ", "g", "grimm_aspirate"),
        ("s", "s", "retain"),
    ],
    # Old High German
    "goh": [
        ("p", "pf", "high_german_p"),
        ("t", "ts", "high_german_t"),
        ("k", "k", "retain"),
        ("b", "p", "grimm_b"),
        ("d", "t", "grimm_d"),
        ("g", "k", "grimm_g"),
        ("bʰ", "b", "grimm_aspirate"),
        ("dʰ", "d", "grimm_aspirate"),
        ("gʰ", "g", "grimm_aspirate"),
        ("þ", "d", "high_german_þ"),
    ],
    # Old Irish (Celtic)
    "sga": [
        ("p", "", "celtic_p_loss"),
        ("b", "b", "retain"),
        ("t", "t", "retain"),
        ("d", "d", "retain"),
        ("k", "k", "retain"),
        ("g", "g", "retain"),
        ("kʷ", "k", "celtic_kw_k"),
        ("gʷ", "g", "celtic_gw_g"),
        ("bʰ", "b", "celtic_aspirate"),
        ("dʰ", "d", "celtic_aspirate"),
        ("gʰ", "g", "celtic_aspirate"),
        ("s", "s", "retain"),
        ("m", "m", "retain"),
        ("n", "n", "retain"),
    ],
    # Old Church Slavonic
    "cu": [
        ("p", "p", "retain"),
        ("b", "b", "retain"),
        ("t", "t", "retain"),
        ("d", "d", "retain"),
        ("k", "k", "retain"),
        ("g", "g", "retain"),
        ("kʷ", "k", "slavic_kw_k"),
        ("gʷ", "g", "slavic_gw_g"),
        ("bʰ", "b", "slavic_aspirate"),
        ("dʰ", "d", "slavic_aspirate"),
        ("gʰ", "g", "slavic_aspirate"),
        ("s", "s", "retain"),
        ("m", "m", "retain"),
        ("n", "n", "retain"),
    ],
    # Lithuanian
    "lit": [
        ("p", "p", "retain"),
        ("b", "b", "retain"),
        ("t", "t", "retain"),
        ("d", "d", "retain"),
        ("k", "k", "retain"),
        ("g", "g", "retain"),
        ("kʷ", "k", "baltic_kw_k"),
        ("gʷ", "g", "baltic_gw_g"),
        ("bʰ", "b", "baltic_aspirate"),
        ("dʰ", "d", "baltic_aspirate"),
        ("gʰ", "g", "baltic_aspirate"),
        ("s", "s", "retain"),
        ("m", "m", "retain"),
        ("n", "n", "retain"),
    ],
    # Hittite (Anatolian)
    "hit": [
        ("p", "p", "retain"),
        ("b", "p", "hittite_devoice"),
        ("t", "t", "retain"),
        ("d", "t", "hittite_devoice"),
        ("k", "k", "retain"),
        ("g", "k", "hittite_devoice"),
        ("kʷ", "ku", "hittite_kw"),
        ("gʷ", "ku", "hittite_gw"),
        ("h", "ḫ", "anatolian_h"),
        ("e", "e", "retain"),
        ("s", "s", "retain"),
        ("m", "m", "retain"),
        ("n", "n", "retain"),
    ],
    # Tocharian B
    "txb": [
        ("p", "p", "retain"),
        ("b", "p", "tocharian_devoice"),
        ("t", "t", "retain"),
        ("d", "t", "tocharian_devoice"),
        ("k", "k", "retain"),
        ("g", "k", "tocharian_devoice"),
        ("s", "s", "retain"),
        ("m", "m", "retain"),
        ("n", "n", "retain"),
        ("r", "r", "retain"),
        ("l", "l", "retain"),
    ],
    # Armenian
    "hxm": [
        ("p", "h", "armenian_p_h"),
        ("b", "p", "armenian_b_p"),
        ("bʰ", "b", "armenian_aspirate"),
        ("t", "tʻ", "armenian_t"),
        ("d", "t", "armenian_d_t"),
        ("dʰ", "d", "armenian_aspirate"),
        ("k", "kʻ", "armenian_k"),
        ("g", "k", "armenian_g_k"),
        ("gʰ", "g", "armenian_aspirate"),
    ],
    # Albanian
    "alb": [
        ("bʰ", "b", "albanian_aspirate"),
        ("dʰ", "d", "albanian_aspirate"),
        ("gʰ", "g", "albanian_aspirate"),
        ("kʷ", "s", "albanian_kw_s"),
        ("gʷ", "z", "albanian_gw_z"),
        ("s", "gj", "albanian_palatalization"),
    ],
    # Avestan (Iranian)
    "ave": [
        ("e", "a", "indo_iranian_a"),
        ("o", "a", "indo_iranian_a"),
        ("s", "h", "iranian_s_h"),
        ("bʰ", "b", "iranian_aspirate"),
        ("dʰ", "d", "iranian_aspirate"),
        ("gʰ", "g", "iranian_aspirate"),
    ],
    # Oscan (Sabellic)
    "osc": [
        ("kʷ", "p", "sabellic_kw_p"),
        ("gʷ", "b", "sabellic_gw_b"),
        ("bʰ", "f", "italic_aspirate"),
        ("dʰ", "f", "italic_aspirate"),
    ],
}

# Naturalness weights for sound changes — less natural = higher cost
# Used to prefer more phonetically natural reconstructions
_NATURALNESS: dict[str, float] = {
    # Lentition (natural)
    "grimm_p": 0.8,
    "grimm_t": 0.8,
    "grimm_k": 0.8,
    "greek_aspirate": 0.9,
    "italic_aspirate": 0.85,
    # Merger (natural)
    "indo_iranian_a": 0.9,
    "celtic_p_loss": 0.7,
    "hittite_devoice": 0.85,
    "tocharian_devoice": 0.85,
    # Retention (neutral)
    "retain": 1.0,
    # Unconditioned split (less natural — marks possible issue)
    "albanian_kw_s": 0.6,
    "albanian_gw_z": 0.6,
    "armenian_p_h": 0.7,
    "high_german_p": 0.75,
    # Conditioned (natural with environment)
    "greek_s_aspiration": 0.85,
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

        Uses the comparative method:
          1. Pairwise alignments between all daughter languages
          2. Discover recurring correspondence sets
          3. Reconstruct each proto-segment from correspondence evidence
          4. Infer sound changes from proto → each daughter
          5. Score regularity and rank alternatives
        """
        attestation_ids = attestation_ids or {}
        flags_by_lang = flags_by_lang or {}
        langs = sorted(forms.keys())
        if len(langs) < 2:
            return []

        alignments = self._pairwise_alignments(forms)
        corr_sets = self._discover_correspondences(forms, alignments)
        primary = self._reconstruct_from_correspondences(forms, corr_sets)
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
                    base_conf * reg
                    - exc
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
                        for cs in corr_sets[:15]
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

    def _pairwise_alignments(self, forms: dict[str, str]) -> dict[tuple[str, str], list[AlignCell]]:
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
        for (la, sa, lb, sb), cnt in pair_counts.most_common(50):
            if cnt < self.min_correspondence_count and sa != sb:
                continue
            pattern = (sa, sb) if la <= lb else (sb, sa)
            sets.append(
                CorrespondenceSet(
                    pattern=pattern,
                    languages=tuple(sorted([la, lb])),
                    count=cnt,
                    environments=envs[(la, sa, lb, sb)],
                )
            )
        return sets

    def _reconstruct_from_correspondences(
        self,
        forms: dict[str, str],
        corr_sets: list[CorrespondenceSet],
    ) -> str:
        """
        Reconstruct a proto-form using the comparative method.

        For each aligned position, collect what each daughter language has.
        Use correspondence patterns to vote on the most likely proto-segment,
        preferring segments that can *explain* other segments via known
        sound changes (directionality principle).
        """
        tokenized = {lang: tokenize(f) for lang, f in forms.items()}
        max_len = max(len(t) for t in tokenized.values())
        langs = sorted(forms.keys())

        pos_to_sym: dict[tuple[str, int], str] = {}
        for lang, toks in tokenized.items():
            for i, tok in enumerate(toks):
                pos_to_sym[(lang, i)] = tok.symbol

        # Precompute a lookup of known sound changes: (source_segment, target_language) → [target_segments]
        # This lets us check: "if proto had X, would it naturally give Y in language Z?"
        known_changes: dict[str, dict[str, list[str]]] = {}
        for lang in langs:
            changes = BRANCH_TRANSFORMS.get(lang, [])
            for src, dst, _name in changes:
                known_changes.setdefault(src, {}).setdefault(lang, []).append(dst)

        proto_chars: list[str] = []
        for pos in range(max_len):
            column: dict[str, str] = {}
            for lang in langs:
                sym = pos_to_sym.get((lang, pos))
                if sym:
                    column[lang] = sym

            if not column:
                continue

            if len(column) < 2:
                proto_chars.append(list(column.values())[0])
                continue

            candidates: Counter[str] = Counter()

            for lang_a, sym_a in column.items():
                for lang_b, sym_b in column.items():
                    if lang_a >= lang_b:
                        continue

                    match_weight = 0.0
                    for cs in corr_sets:
                        if cs.languages == tuple(sorted([lang_a, lang_b])) and cs.pattern == (
                            sym_a,
                            sym_b,
                        ):
                            match_weight += min(
                                cs.count / max(self.min_correspondence_count, 1), 3.0
                            )

                    if match_weight == 0:
                        sa = segment(sym_a)
                        sb = segment(sym_b)
                        fd = feature_distance(sa, sb)
                        match_weight = max(0.0, 1.0 - fd)

                    candidates[sym_a] += match_weight
                    candidates[sym_b] += match_weight

            if not candidates:
                proto_chars.append(Counter(column.values()).most_common(1)[0][0])
                continue

            best_sym, best_score = candidates.most_common(1)[0]

            # Directionality refinement: if the best candidate is NOT the
            # source of a known sound change for other languages in this
            # column, but another candidate IS, prefer the source candidate.
            candidate_list = [s for s, _ in candidates.most_common(3)]
            if len(candidate_list) >= 2:
                # Score each candidate by how well it explains other segments
                explain_scores: dict[str, float] = {}
                for cand in candidate_list:
                    score = 0.0
                    for lang, actual_sym in column.items():
                        if actual_sym == cand:
                            score += 0.2  # identity match bonus
                        else:
                            # Can cand → actual_sym via known changes?
                            known = known_changes.get(cand, {}).get(lang, [])
                            if actual_sym in known:
                                score += 0.5  # known directional change
                    explain_scores[cand] = score

                best_explain = max(explain_scores, key=explain_scores.get)
                if explain_scores[best_explain] > explain_scores.get(best_sym, 0):
                    best_sym = best_explain

            # Tie-breaking
            if len(candidates) >= 2:
                second_score = candidates.most_common(2)[1][1]
                if best_score < second_score * 1.2:
                    freq = Counter(column.values())
                    best_sym = freq.most_common(1)[0][0]

            proto_chars.append(best_sym)

        return "".join(proto_chars) or next(iter(forms.values()))

    def _majority_vote_proto(
        self, forms: dict[str, str], corr_sets: list[CorrespondenceSet]
    ) -> str:
        """Simpler per-position majority vote (fallback / baseline)."""
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
            if n >= max(1, len(tokenized) // 2):
                chars.append(top)
            elif len(votes) >= 2 and votes.most_common(2)[0][1] == votes.most_common(2)[1][1]:
                chars.append(sorted(votes.keys())[0])
            else:
                chars.append(top)
        return "".join(chars) or next(iter(forms.values()))

    def _generate_competitors(
        self,
        forms: dict[str, str],
        primary: str,
        known_proto: str | None,
    ) -> list[tuple[str, float, str]]:
        alts: list[tuple[str, float, str]] = [(primary, 0.75, "comparative_reconstruction")]
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
        # majority vote baseline
        tokenized = {lang: tokenize(f) for lang, f in forms.items()}
        max_len = max(len(t) for t in tokenized.values())
        chars: list[str] = []
        for i in range(max_len):
            votes: Counter[str] = Counter()
            for toks in tokenized.values():
                if i < len(toks):
                    votes[toks[i].symbol] += 1
            if votes:
                chars.append(votes.most_common(1)[0][0])
        majority = "".join(chars)
        if majority and majority != primary and len(majority) >= 2:
            alts.append((majority, 0.5, "position_majority"))
        if known_proto:
            alts.insert(0, (known_proto.lstrip("*"), 0.88, "scholarly_prior"))
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
                for src, dst, name in BRANCH_TRANSFORMS.get(lang, []):
                    if cell.a and cell.b and cell.a.symbol == src and cell.b.symbol == dst:
                        rule["named_transform"] = name
                        rule["naturalness"] = _NATURALNESS.get(name, 0.5)
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
        naturalness_sum = sum(s.get("naturalness", 0.5) for s in seq if "named_transform" in s)
        ops = [s for s in seq if s.get("op")]
        irregular_ops = sum(
            1 for s in ops if s.get("op") in {"ins", "del"} and s.get("cost", 0) > 1.0
        )
        recurring = sum(1 for cs in corr_sets if cs.count >= self.min_correspondence_count)

        # Regularity base: starts at 0.4, increased by named transforms and correspondences
        reg = 0.4
        if named > 0:
            reg += 0.15 * min(named / max(len(forms), 1), 1.0)
            reg += 0.1 * min(naturalness_sum / (named or 1), 0.3)
        reg += 0.05 * min(recurring, 6)
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

        # Accidental similarity detection
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
        withhold_lang = max(forms.keys(), key=lambda k: len(forms[k]))
        remaining = {k: v for k, v in forms.items() if k != withhold_lang}
        alt = self._reconstruct_from_correspondences(remaining, [])
        withheld = forms[withhold_lang]
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
