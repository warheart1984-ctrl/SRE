"""Automatic sound correspondence induction.

Takes raw aligned cognate sets and generalizes segment-to-segment
correspondences into phonologically natural rule classes (e.g. p:f, t:θ, k:x
→ voiceless_stop → fricative).

Outputs probabilistic branch transforms replacing the hand-coded
BRANCH_TRANSFORMS dictionary.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field

from .correspondence_engine import CorrespondenceEngine, CorrespondenceSet
from .features import FEATURES, feature_distance, segment


@dataclass
class PhonologicalPattern:
    """A generalized phonological correspondence pattern."""

    source_class: frozenset[str]  # e.g. {"p", "t", "k"} — voiceless stops
    target_class: frozenset[str]  # e.g. {"f", "θ", "x"} — fricatives
    source_features: frozenset[str]  # defining features of source class
    target_features: frozenset[str]  # defining features of target class
    instances: list[tuple[str, str]] = field(default_factory=list)  # (src, tgt) pairs
    languages: set[str] = field(default_factory=set)
    environments: list[str] = field(default_factory=list)

    def add_instance(self, src: str, tgt: str, lang_pair: tuple[str, str], env: str) -> None:
        self.instances.append((src, tgt))
        self.languages.update(lang_pair)
        if env:
            self.environments.append(env)

    @property
    def count(self) -> int:
        return len(self.instances)

    def regularity_score(self) -> float:
        """How consistently does source class map to target class?"""
        if not self.instances:
            return 0.0
        # Fraction of source segments that map to the dominant target
        src_to_tgt: dict[str, Counter[str]] = defaultdict(Counter)
        for s, t in self.instances:
            src_to_tgt[s][t] += 1
        consistent = sum(max(v.values()) for v in src_to_tgt.values())
        return consistent / len(self.instances)

    def naturalness_score(self) -> float:
        """Phonetic naturalness of the change (lower feature distance = more natural)."""
        if not self.instances:
            return 0.0
        total = 0.0
        for s, t in self.instances:
            total += 1.0 - feature_distance(segment(s), segment(t))
        return total / len(self.instances)

    def combined_score(self, weight_reg: float = 0.7, weight_nat: float = 0.3) -> float:
        return weight_reg * self.regularity_score() + weight_nat * self.naturalness_score()


class CorrespondenceInducer:
    """Induce probabilistic sound correspondences from aligned cognate sets."""

    def __init__(
        self,
        min_count: int = 2,
        min_regularity: float = 0.5,
        min_naturalness: float = 0.3,
    ) -> None:
        self.min_count = min_count
        self.min_regularity = min_regularity
        self.min_naturalness = min_naturalness
        self.engine = CorrespondenceEngine(min_correspondence_count=min_count)

    def induce_from_forms(self, forms: dict[str, str]) -> dict[str, list[tuple[str, str, float]]]:
        """Run full induction pipeline on a cognate set."""
        # Get alignments and raw correspondences
        alignments = self.engine._pairwise_alignments(forms)
        corr_sets = self.engine._discover_correspondences(forms, alignments)

        # Generalize into phonological patterns
        patterns = self._generalize_correspondences(corr_sets)

        # Score and filter
        scored = self._score_patterns(patterns)

        # Convert to branch transforms
        return self._to_branch_transforms(scored)

    def _generalize_correspondences(
        self, corr_sets: list[CorrespondenceSet]
    ) -> list[PhonologicalPattern]:
        """Cluster segment correspondences by shared feature classes."""
        # Group by source feature class × target feature class
        pattern_map: dict[tuple[frozenset, frozenset], PhonologicalPattern] = {}

        for cs in corr_sets:
            src, tgt = cs.pattern
            sa, sb = segment(src), segment(tgt)

            # Define source class by its major class features
            src_feats = self._major_class_features(sa)
            tgt_feats = self._major_class_features(sb)

            src_class = self._segments_with_features(src_feats)
            tgt_class = self._segments_with_features(tgt_feats)

            key = (frozenset(src_class), frozenset(tgt_class))
            if key not in pattern_map:
                pattern_map[key] = PhonologicalPattern(
                    source_class=frozenset(src_class),
                    target_class=frozenset(tgt_class),
                    source_features=src_feats,
                    target_features=tgt_feats,
                )
            pattern_map[key].add_instance(
                src, tgt, cs.languages, cs.environments[0] if cs.environments else ""
            )

        # Keep only patterns with enough instances
        return [p for p in pattern_map.values() if p.count >= self.min_count]

    def _major_class_features(self, seg_obj) -> frozenset[str]:
        """Extract the major class features defining a segment's phonological category."""
        # seg_obj is a Segment with .features attribute (frozenset)
        feats = getattr(seg_obj, "features", seg_obj)
        major = {
            "cons",
            "voc",
            "sonorant",
            "obstruent",
            "stop",
            "fric",
            "affricate",
            "nasal",
            "approx",
            "labial",
            "dental",
            "alveolar",
            "postalveolar",
            "retroflex",
            "palatal",
            "velar",
            "uvular",
            "pharyngeal",
            "glottal",
            "vl",
            "vd",
            "aspirated",
        }
        return frozenset(f for f in feats if f in major)

    def _segments_with_features(self, feats: frozenset[str]) -> list[str]:
        """Find all segments matching a feature set."""
        return [s for s, f in FEATURES.items() if feats.issubset(f)]

    def _score_patterns(self, patterns: list[PhonologicalPattern]) -> list[PhonologicalPattern]:
        """Score and filter patterns by regularity and naturalness."""
        scored = []
        for p in patterns:
            reg = p.regularity_score()
            nat = p.naturalness_score()
            if reg >= self.min_regularity and nat >= self.min_naturalness:
                scored.append(p)
        scored.sort(key=lambda p: p.combined_score(), reverse=True)
        return scored

    def _to_branch_transforms(
        self, patterns: list[PhonologicalPattern]
    ) -> dict[str, list[tuple[str, str, float]]]:
        """Convert patterns to branch-specific probabilistic transforms."""
        # Group patterns by language pair
        branch_map: dict[str, list[tuple[str, str, float]]] = defaultdict(list)

        for p in patterns:
            for lang in p.languages:
                # Probability = combined_score * (count / max_count)
                prob = p.combined_score() * min(p.count / 10.0, 1.0)
                # Emit one rule per source segment in the class
                for src in p.source_class:
                    # Pick most common target for this source in this pattern
                    tgt_counts = Counter(t for s, t in p.instances if s == src)
                    if tgt_counts:
                        tgt = tgt_counts.most_common(1)[0][0]
                        branch_map[lang].append((src, tgt, round(prob, 3)))

        return dict(branch_map)


def induce_correspondences(
    forms: dict[str, str],
    *,
    min_count: int = 2,
    min_regularity: float = 0.5,
    min_naturalness: float = 0.3,
) -> dict[str, list[tuple[str, str, float]]]:
    """Convenience function: induce probabilistic branch transforms from forms."""
    inducer = CorrespondenceInducer(
        min_count=min_count,
        min_regularity=min_regularity,
        min_naturalness=min_naturalness,
    )
    return inducer.induce_from_forms(forms)


def merge_with_handcrafted(
    induced: dict[str, list[tuple[str, str, float]]],
    handcrafted: dict[str, list[tuple[str, str, str]]],
    *,
    induced_weight: float = 0.7,
) -> dict[str, list[tuple[str, str, float]]]:
    """Merge induced probabilistic transforms with hand-coded BRANCH_TRANSFORMS."""
    merged: dict[str, list[tuple[str, str, float]]] = defaultdict(list)

    # Add handcrafted with full weight
    for branch, rules in handcrafted.items():
        for src, tgt, _name in rules:
            merged[branch].append((src, tgt, 1.0))

    # Add induced with reduced weight (don't override handcrafted)
    for branch, rules in induced.items():
        for src, tgt, prob in rules:
            if not any(s == src and t == tgt for s, t, _ in merged[branch]):
                merged[branch].append((src, tgt, prob * induced_weight))

    return dict(merged)
