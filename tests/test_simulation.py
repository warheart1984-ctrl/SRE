"""Tests for the simulation engine."""

from __future__ import annotations

import pytest

from sre.simulation import ReconstructionTrial, run_battery, run_trial
from sre.simulation.engine import RandomProtoGenerator
from sre.simulation.metrics import segment_accuracy, sound_change_precision_recall


class TestRandomProtoGenerator:
    def test_generates_string(self) -> None:
        gen = RandomProtoGenerator(min_length=3, max_length=8, seed=42)
        proto = gen.generate()
        assert isinstance(proto, str)
        # Count IPA tokens, not Unicode codepoints
        from sre.linguistics.tokenization import tokenize

        toks = tokenize(proto)
        assert 3 <= len(toks) <= 8

    def test_reproducible_seed(self) -> None:
        g1 = RandomProtoGenerator(seed=99)
        g2 = RandomProtoGenerator(seed=99)
        assert g1.generate() == g2.generate()

    def test_different_seeds(self) -> None:
        g1 = RandomProtoGenerator(seed=1)
        g2 = RandomProtoGenerator(seed=2)
        assert g1.generate() != g2.generate()


class TestRunTrial:
    def test_basic_trial(self) -> None:
        trial = run_trial(
            language_count=3,
            time_depth=2,
            num_changes=4,
            seed=42,
        )
        assert isinstance(trial, ReconstructionTrial)
        assert len(trial.true_proto) > 0
        assert len(trial.daughter_forms) == 3
        assert len(trial.reconstructed_proto) > 0
        assert "edit_accuracy" in trial.metrics

    def test_known_proto(self) -> None:
        trial = run_trial(
            proto_form="pater",
            language_count=2,
            time_depth=1,
            num_changes=2,
            seed=42,
        )
        assert trial.true_proto == "pater"

    def test_single_language(self) -> None:
        trial = run_trial(
            language_count=1,
            time_depth=1,
            num_changes=0,
            seed=42,
        )
        # With 1 language the engine can't do comparative reconstruction,
        # but the trial should still complete with metrics
        assert len(trial.daughter_forms) == 1
        assert "edit_accuracy" in trial.metrics


class TestSegmentAccuracy:
    def test_identical(self) -> None:
        m = segment_accuracy("pater", "pater")
        assert m["edit_accuracy"] == 1.0
        assert m["f1"] == 1.0

    def test_completely_different(self) -> None:
        m = segment_accuracy("abc", "xyz")
        assert m["edit_accuracy"] < 1.0
        assert m["precision"] == 0.0
        assert m["recall"] == 0.0

    def test_partial_overlap(self) -> None:
        m = segment_accuracy("pater", "fadar")
        assert 0.0 < m["edit_accuracy"] < 1.0

    def test_empty(self) -> None:
        m = segment_accuracy("", "")
        assert m["edit_accuracy"] == 1.0


class TestChangeMetrics:
    def test_exact_match(self) -> None:
        m = sound_change_precision_recall(
            [("p", "f"), ("t", "θ")],
            [{"from": "p", "to": "f"}, {"from": "t", "to": "θ"}],
        )
        assert m["change_precision"] == 1.0
        assert m["change_recall"] == 1.0
        assert m["change_f1"] == 1.0

    def test_no_match(self) -> None:
        m = sound_change_precision_recall(
            [("p", "f")],
            [{"from": "k", "to": "g"}],
        )
        assert m["change_precision"] == 0.0
        assert m["change_recall"] == 0.0
        assert m["change_f1"] == 0.0

    def test_partial(self) -> None:
        m = sound_change_precision_recall(
            [("p", "f"), ("t", "θ")],
            [{"from": "p", "to": "f"}],
        )
        assert m["change_precision"] == 1.0
        assert m["change_recall"] == 0.5
        assert m["change_f1"] == pytest.approx(2 / 3, abs=1e-3)


class TestRunBattery:
    def test_battery_produces_reports(self) -> None:
        results = run_battery(
            num_trials=3,
            language_counts=[2, 3],
            time_depths=[1, 2],
            seed=42,
        )
        assert len(results) == 4  # 2 × 2
        for _key, report in results.items():
            assert len(report.trials) == 3
            assert "avg_edit_accuracy" in dir(report)

    def test_summary_structure(self) -> None:
        results = run_battery(num_trials=2, language_counts=[2], time_depths=[1], seed=42)
        summary = results["L2_T1"].summary()
        assert summary["num_trials"] == 2
        assert summary["language_count"] == 2
        assert "avg_edit_accuracy" in summary
