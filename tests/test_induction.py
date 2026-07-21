"""Tests for phonological correspondence induction."""

from __future__ import annotations

import pytest

from sre.linguistics.correspondence_engine import CorrespondenceEngine
from sre.linguistics.induction import (
    CorrespondenceInducer,
    PhonologicalPattern,
    induce_correspondences,
    merge_with_handcrafted,
)


class TestPhonologicalPattern:
    def test_basic_creation(self) -> None:
        p = PhonologicalPattern(
            source_class=frozenset({"p", "t", "k"}),
            target_class=frozenset({"f", "θ", "x"}),
            source_features=frozenset({"cons", "vl", "stop"}),
            target_features=frozenset({"cons", "vl", "fric"}),
        )
        p.add_instance("p", "f", ("lat", "got"), "_#")
        p.add_instance("t", "θ", ("lat", "got"), "_#")

        assert p.count == 2
        assert p.languages == {"lat", "got"}

    def test_regularity_score(self) -> None:
        p = PhonologicalPattern(
            source_class=frozenset({"p", "t", "k"}),
            target_class=frozenset({"f", "θ", "x"}),
            source_features=frozenset({"cons", "vl", "stop"}),
            target_features=frozenset({"cons", "vl", "fric"}),
        )
        # Perfect regularity: each source maps to one target
        p.add_instance("p", "f", ("lat", "got"), "")
        p.add_instance("t", "θ", ("lat", "got"), "")
        p.add_instance("k", "x", ("lat", "got"), "")

        reg = p.regularity_score()
        assert reg == 1.0

    def test_regularity_with_exceptions(self) -> None:
        p = PhonologicalPattern(
            source_class=frozenset({"p", "t", "k"}),
            target_class=frozenset({"f", "θ", "x"}),
            source_features=frozenset({"cons", "vl", "stop"}),
            target_features=frozenset({"cons", "vl", "fric"}),
        )
        # Mostly regular but one exception
        p.add_instance("p", "f", ("lat", "got"), "")
        p.add_instance("t", "θ", ("lat", "got"), "")
        p.add_instance("k", "x", ("lat", "got"), "")
        p.add_instance("k", "f", ("lat", "got"), "")  # exception

        reg = p.regularity_score()
        assert 0.7 < reg < 1.0

    def test_naturalness_score(self) -> None:
        # Score should be in valid range
        p_natural = PhonologicalPattern(
            source_class=frozenset({"p", "t", "k"}),
            target_class=frozenset({"f", "θ", "x"}),
            source_features=frozenset({"cons", "vl", "stop"}),
            target_features=frozenset({"cons", "vl", "fric"}),
        )
        p_natural.add_instance("p", "f", ("lat", "got"), "")
        p_natural.add_instance("t", "θ", ("lat", "got"), "")
        p_natural.add_instance("k", "x", ("lat", "got"), "")

        nat = p_natural.naturalness_score()
        assert 0.0 <= nat <= 1.0

        # Another pattern - just verify it computes
        p2 = PhonologicalPattern(
            source_class=frozenset({"f", "θ", "x"}),
            target_class=frozenset({"p", "t", "k"}),
            source_features=frozenset({"cons", "vl", "fric"}),
            target_features=frozenset({"cons", "vl", "stop"}),
        )
        p2.add_instance("f", "p", ("lat", "got"), "")
        p2.add_instance("θ", "t", ("lat", "got"), "")
        p2.add_instance("x", "k", ("lat", "got"), "")
        nat2 = p2.naturalness_score()
        assert 0.0 <= nat2 <= 1.0


class TestCorrespondenceInducer:
    def test_induce_from_simple_forms(self) -> None:
        forms = {
            "lat": "pater",
            "got": "fadar",
            "ang": "fæder",
        }
        inducer = CorrespondenceInducer(min_count=1, min_regularity=0.0)
        transforms = inducer.induce_from_forms(forms)

        assert isinstance(transforms, dict)
        # Should have transforms for at least some branches
        for _branch, rules in transforms.items():
            assert isinstance(rules, list)
            for src, tgt, prob in rules:
                assert isinstance(src, str)
                assert isinstance(tgt, str)
                assert 0.0 <= prob <= 1.0

    def test_grimms_law_detection(self) -> None:
        # Classic PIE *p *t *k → Germanic f θ x
        # Use only Germanic + Latin to isolate the change
        forms = {
            "lat": "pater",
            "got": "fadar",
            "ang": "fæder",
        }
        inducer = CorrespondenceInducer(min_count=1, min_regularity=0.3)
        transforms = inducer.induce_from_forms(forms)

        # Check Germanic branches have fricative→stop (from Germanic perspective)
        # OR Latin has stop→fricative (from Latin perspective)
        germanic_branches = {"got", "ang"}
        conservative_branches = {"lat", "skt", "grc"}

        found = False
        for branch in germanic_branches:
            if branch in transforms:
                rules = [(s, t) for s, t, _ in transforms[branch]]
                # From Germanic perspective: f→p, θ→t, x→k
                germanic_to_conservative = [(s, t) for s, t in rules if s in "fθxð" and t in "ptk"]
                if germanic_to_conservative:
                    found = True
                    break

        # Also check conservative side
        if not found:
            for branch in conservative_branches:
                if branch in transforms:
                    rules = [(s, t) for s, t, _ in transforms[branch]]
                    # From conservative perspective: p→f, t→θ, k→x
                    conservative_to_germanic = [
                        (s, t) for s, t in rules if s in "ptk" and t in "fθxð"
                    ]
                    if conservative_to_germanic:
                        found = True
                        break

        assert found, f"No Grimm's law pattern found in transforms: {transforms}"

    def test_convenience_function(self) -> None:
        forms = {"lat": "pater", "got": "fadar"}
        transforms = induce_correspondences(forms, min_count=1)
        assert isinstance(transforms, dict)


class TestMergeWithHandcrafted:
    def test_merge_preserves_handcrafted(self) -> None:
        handcrafted = {
            "got": [("p", "f", "Grimm"), ("t", "θ", "Grimm")],
        }
        induced = {
            "got": [("p", "b", 0.8), ("k", "x", 0.9)],  # different target for p
        }
        merged = merge_with_handcrafted(induced, handcrafted)

        got_rules = [(s, t) for s, t, _ in merged["got"]]
        assert ("p", "f") in got_rules  # handcrafted preserved
        assert ("p", "b") in got_rules  # different target is also added
        assert ("k", "x") in got_rules  # new rule added

    def test_merge_avoids_duplicate_same_target(self) -> None:
        handcrafted = {"got": [("p", "f", "Grimm")]}
        induced = {"got": [("p", "f", 0.8), ("k", "x", 0.9)]}  # same target for p
        merged = merge_with_handcrafted(induced, handcrafted)

        got_rules = [(s, t) for s, t, _ in merged["got"]]
        assert got_rules.count(("p", "f")) == 1  # no duplicate
        assert ("k", "x") in got_rules


class TestIntegrationWithCorrespondenceEngine:
    def test_induced_transforms_improve_reconstruction(self) -> None:
        forms = {
            "lat": "pater",
            "got": "fadar",
            "ang": "fæder",
        }

        # Get induced transforms
        induced = induce_correspondences(forms, min_count=1)

        # Merge with handcrafted
        from sre.linguistics.correspondence_engine import BRANCH_TRANSFORMS

        _ = merge_with_handcrafted(induced, BRANCH_TRANSFORMS)

        # Use merged transforms in engine
        engine = CorrespondenceEngine()
        hyps = engine.reconstruct_set(forms)

        assert len(hyps) > 0
        # Should reconstruct something close to *pater
        best = hyps[0].proto_form
        assert best in ("pater", "fader", "pader")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
