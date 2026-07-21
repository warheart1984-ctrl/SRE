"""Simulation engine: generate synthetic proto-languages, evolve them, and
evaluate how accurately the CorrespondenceEngine reconstructs the proto."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from ..linguistics.correspondence_engine import CorrespondenceEngine
from ..linguistics.features import FEATURES
from ..linguistics.tokenization import tokenize
from .metrics import segment_accuracy, sound_change_precision_recall


@dataclass
class SimulatedSoundChange:
    """A sound change applied during simulation."""

    from_seg: str
    to_seg: str
    probability: float = 1.0  # 1.0 = categorical, <1.0 = sporadic
    min_depth: int = 0  # minimum time steps before this change can apply
    shared_branch: str | None = None  # if set, only daughters in this branch get it


class RandomProtoGenerator:
    """Generate random proto-forms from the IPA inventory."""

    def __init__(
        self,
        min_length: int = 3,
        max_length: int = 8,
        seed: int | None = None,
    ) -> None:
        self.min_length = min_length
        self.max_length = max_length
        self._rng = random.Random(seed)
        # Weight common sounds higher
        self._segments = sorted(FEATURES.keys())
        self._weights = [
            3.0 if s in "aeiouptkmnls" else 1.5 if s in "bdgʃʒtdɾ" else 0.5 for s in self._segments
        ]

    def generate(self) -> str:
        """Generate a random proto-form string."""
        length = self._rng.randint(self.min_length, self.max_length)
        chars: list[str] = []
        for _ in range(length):
            seg = self._rng.choices(self._segments, weights=self._weights, k=1)[0]
            chars.append(seg)
        return "".join(chars)


@dataclass
class ReconstructionTrial:
    """Result of a single simulation + reconstruction trial."""

    true_proto: str
    reconstructed_proto: str
    daughter_forms: dict[str, str]
    applied_changes: list[tuple[str, str, str]]  # (branch, from, to)
    inferred_changes: list[dict]
    metrics: dict[str, float] = field(default_factory=dict)
    hypotheses: list[Any] = field(default_factory=list)


@dataclass
class SimulationReport:
    """Aggregate results across many trials."""

    trials: list[ReconstructionTrial] = field(default_factory=list)
    language_count: int = 3
    time_depth: int = 3
    shared_change_ratio: float = 0.3

    @property
    def avg_edit_accuracy(self) -> float:
        if not self.trials:
            return 0.0
        return sum(t.metrics.get("edit_accuracy", 0) for t in self.trials) / len(self.trials)

    @property
    def avg_feature_weighted(self) -> float:
        if not self.trials:
            return 0.0
        return sum(t.metrics.get("feature_weighted_accuracy", 0) for t in self.trials) / len(
            self.trials
        )

    @property
    def avg_change_f1(self) -> float:
        if not self.trials:
            return 0.0
        return sum(t.metrics.get("change_f1", 0) for t in self.trials) / len(self.trials)

    def summary(self) -> dict[str, Any]:
        return {
            "num_trials": len(self.trials),
            "language_count": self.language_count,
            "time_depth": self.time_depth,
            "shared_change_ratio": self.shared_change_ratio,
            "avg_edit_accuracy": round(self.avg_edit_accuracy, 4),
            "avg_feature_weighted_accuracy": round(self.avg_feature_weighted, 4),
            "avg_change_f1": round(self.avg_change_f1, 4),
        }


def _random_changes(
    rng: random.Random,
    count: int,
) -> list[SimulatedSoundChange]:
    """Generate a list of random simulated sound changes."""
    common_substitutions = [
        ("p", "f"),
        ("b", "β"),
        ("t", "θ"),
        ("d", "ð"),
        ("k", "x"),
        ("g", "ɣ"),
        ("a", "e"),
        ("e", "i"),
        ("o", "u"),
        ("i", "e"),
        ("u", "o"),
        ("a", "o"),
        ("p", "b"),
        ("t", "d"),
        ("k", "g"),
        ("s", "h"),
        ("n", "m"),
        ("r", "l"),
        ("l", "r"),
        ("m", "n"),
        ("b", "v"),
        ("d", "ɾ"),
        ("g", "j"),
        ("k", "tʃ"),
        ("g", "dʒ"),
        ("t", "ts"),
        ("d", "dz"),
        ("pʰ", "f"),
        ("tʰ", "θ"),
    ]
    changes: list[SimulatedSoundChange] = []
    seen_pairs = set()
    for _ in range(count):
        pair = rng.choice(common_substitutions)
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        prob = rng.choice([1.0, 1.0, 1.0, 0.5, 0.3])
        min_depth = rng.randint(0, 2)
        changes.append(
            SimulatedSoundChange(
                from_seg=pair[0],
                to_seg=pair[1],
                probability=prob,
                min_depth=min_depth,
            )
        )
    return changes


def _evolve(
    proto: str,
    changes: list[SimulatedSoundChange],
    time_depth: int,
    rng: random.Random,
) -> str:
    """Apply sound changes to a proto-form over *time_depth* steps."""
    result = proto
    for step in range(time_depth):
        chars = list(tokenize(result))
        new_chars: list[str] = []
        for seg in chars:
            applied = False
            for sc in changes:
                if sc.min_depth > step:
                    continue
                if seg.symbol == sc.from_seg and (
                    sc.probability >= 1.0 or rng.random() < sc.probability
                ):
                    new_chars.append(sc.to_seg)
                    applied = True
                    break
            if not applied:
                new_chars.append(seg.symbol)
        result = "".join(new_chars)
    return result


def run_trial(
    *,
    language_count: int = 3,
    time_depth: int = 3,
    shared_change_ratio: float = 0.3,
    proto_form: str | None = None,
    lang_names: list[str] | None = None,
    num_changes: int = 6,
    seed: int | None = None,
    engine: CorrespondenceEngine | None = None,
) -> ReconstructionTrial:
    """Run a single simulation trial.

    1. Generate or accept a proto-form
    2. Create *language_count* daughter languages with some shared + some
       independent sound changes
    3. Apply changes over *time_depth* iterations
    4. Run the CorrespondenceEngine to reconstruct the proto
    5. Compare true vs reconstructed proto
    """
    rng = random.Random(seed)
    gen = RandomProtoGenerator(seed=rng.randint(0, 2**31))
    true_proto = proto_form or gen.generate()

    if lang_names is None:
        # Use short branch codes like LAT, GOT, etc.
        base = ["ALA", "BET", "GAM", "DEL", "EPO", "ZET", "ETA", "THE"]
        lang_names = base[:language_count]

    # Generate shared (subgroup) changes and independent changes
    all_changes = _random_changes(rng, num_changes)
    shared_count = max(1, int(num_changes * shared_change_ratio))
    shared = all_changes[:shared_count]
    independent_sets: list[list[SimulatedSoundChange]] = []
    remaining = all_changes[shared_count:]
    for _ in range(language_count):
        indy = list(shared)  # each language gets shared changes
        # Add some independent changes
        extra = rng.sample(
            remaining, min(rng.randint(0, max(1, len(remaining) // 2)), len(remaining))
        )
        indy.extend(extra)
        independent_sets.append(indy)

    # Evolve each language
    daughter_forms: dict[str, str] = {}
    applied_changes: list[tuple[str, str, str]] = []
    for i, lang in enumerate(lang_names):
        form = _evolve(true_proto, independent_sets[i], time_depth, rng)
        daughter_forms[lang] = form
        for sc in independent_sets[i]:
            applied_changes.append((lang, sc.from_seg, sc.to_seg))

    # Reconstruct
    eng = engine or CorrespondenceEngine()
    hyps = eng.reconstruct_set(daughter_forms)

    reconstructed = hyps[0].proto_form if hyps else ""

    # Metrics
    seg_metrics = segment_accuracy(true_proto, reconstructed)
    change_metrics = sound_change_precision_recall(
        [(sc.from_seg, sc.to_seg) for _, sc_from, sc_to in applied_changes],
        hyps[0].sound_change_sequence if hyps else [],
    )

    metrics = {**seg_metrics, **change_metrics}

    return ReconstructionTrial(
        true_proto=true_proto,
        reconstructed_proto=reconstructed,
        daughter_forms=daughter_forms,
        applied_changes=list(set(applied_changes)),
        inferred_changes=hyps[0].sound_change_sequence if hyps else [],
        metrics=metrics,
        hypotheses=hyps,
    )


def run_battery(
    num_trials: int = 20,
    *,
    language_counts: list[int] | None = None,
    time_depths: list[int] | None = None,
    seed: int | None = None,
) -> dict[str, SimulationReport]:
    """Run a battery of trials across different configurations.

    Returns {config_key: SimulationReport} for comparison.
    """
    if language_counts is None:
        language_counts = [2, 3, 5, 8]
    if time_depths is None:
        time_depths = [1, 3, 5]

    base_seed = seed or 42
    results: dict[str, SimulationReport] = {}

    for lc in language_counts:
        for td in time_depths:
            report = SimulationReport(
                language_count=lc,
                time_depth=td,
                shared_change_ratio=0.3,
            )
            for t in range(num_trials):
                trial = run_trial(
                    language_count=lc,
                    time_depth=td,
                    seed=base_seed + t * 100 + lc * 10 + td,
                )
                report.trials.append(trial)
            key = f"L{lc}_T{td}"
            results[key] = report

    return results
