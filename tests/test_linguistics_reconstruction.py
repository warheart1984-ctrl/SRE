"""Integration tests for linguistics reconstruction pipeline — features, tokenization, correspondence engine, sound change."""

from __future__ import annotations

import unittest

from sre.ai.sound_change import (
    SoundChangeApplier,
    SoundChangeRule,
)
from sre.linguistics.correspondence_engine import CorrespondenceEngine
from sre.linguistics.features import FEATURES, feature_distance, segment
from sre.linguistics.tokenization import normalize_orthography, tokenize


class TestFeatureInventory(unittest.TestCase):
    def test_expanded_inventory_size(self) -> None:
        self.assertGreaterEqual(len(FEATURES), 80)

    def test_aspirated_stops_present(self) -> None:
        for asp in ("pʰ", "bʰ", "tʰ", "dʰ", "kʰ", "gʰ", "kʷʰ", "gʷʰ"):
            self.assertIn(asp, FEATURES, f"missing {asp}")

    def test_palatal_and_uvular_present(self) -> None:
        for seg in ("c", "ɟ", "ɲ", "ç", "q", "ɢ", "χ", "ʁ"):
            self.assertIn(seg, FEATURES, f"missing {seg}")

    def test_vowel_quadrant_coverage(self) -> None:
        for v in ("i", "e", "a", "o", "u", "y", "ø", "ə", "ɛ", "ɔ"):
            self.assertIn(v, FEATURES, f"missing vowel {v}")

    def test_long_vowels_present(self) -> None:
        for lv in ("aː", "eː", "iː", "oː", "uː"):
            self.assertIn(lv, FEATURES, f"missing long vowel {lv}")

    def test_legacy_aliases(self) -> None:
        for legacy, long in (("ā", "aː"), ("ē", "eː"), ("ī", "iː"), ("ō", "oː"), ("ū", "uː")):
            s_legacy = segment(legacy)
            s_long = segment(long)
            self.assertEqual(s_legacy.symbol, long)
            self.assertEqual(s_legacy.features, s_long.features)

    def test_feature_distance_identical(self) -> None:
        self.assertEqual(feature_distance(segment("p"), segment("p")), 0.0)

    def test_feature_distance_similar(self) -> None:
        d = feature_distance(segment("p"), segment("b"))
        self.assertGreater(d, 0.0)
        self.assertLess(d, 1.0)

    def test_feature_distance_dissimilar(self) -> None:
        d = feature_distance(segment("p"), segment("a"))
        self.assertGreater(d, 0.8)

    def test_segment_properties(self) -> None:
        s = segment("p")
        self.assertTrue(s.is_consonant)
        self.assertFalse(s.is_vowel)
        v = segment("a")
        self.assertTrue(v.is_vowel)
        self.assertFalse(v.is_consonant)


class TestTokenization(unittest.TestCase):
    def test_aspirated_digraph(self) -> None:
        toks = tokenize("pʰaː")
        self.assertEqual(len(toks), 2)
        self.assertEqual(toks[0].symbol, "pʰ")

    def test_labiovelar_digraph(self) -> None:
        toks = tokenize("kʷa")
        self.assertEqual(len(toks), 2)
        self.assertEqual(toks[0].symbol, "kʷ")

    def test_affricate_digraph(self) -> None:
        toks = tokenize("tʃa")
        self.assertEqual(len(toks), 2)
        self.assertEqual(toks[0].symbol, "tʃ")

    def test_long_vowel_digraph(self) -> None:
        toks = tokenize("aː")
        self.assertEqual(len(toks), 1)
        self.assertEqual(toks[0].symbol, "aː")

    def test_normalize_strips_asterisk(self) -> None:
        self.assertEqual(normalize_orthography("*pater"), "pater")

    def test_normalize_strips_hyphen(self) -> None:
        self.assertEqual(normalize_orthography("ped-"), "ped")

    def test_normalize_legacy_macron(self) -> None:
        self.assertEqual(normalize_orthography("ā"), "aː")

    def test_normalize_acute_as_length(self) -> None:
        self.assertEqual(normalize_orthography("á"), "aː")

    def test_digraphs_sorted_by_length(self) -> None:
        toks = tokenize("kʷʰa")
        self.assertEqual(len(toks), 2)
        self.assertEqual(toks[0].symbol, "kʷʰ")

    def test_pie_laryngeal_normalization(self) -> None:
        self.assertEqual(normalize_orthography("h₂"), "h")


class TestCorrespondenceEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = CorrespondenceEngine()

    def test_requires_at_least_two_languages(self) -> None:
        result = self.engine.reconstruct_set({"lat": "pater"})
        self.assertEqual(result, [])

    def test_pie_pater_cognates(self) -> None:
        forms = {
            "lat": "pater",
            "grc": "pater",
            "skt": "pitar",
            "got": "fadar",
            "ang": "fæder",
            "non": "faðir",
        }
        hyps = self.engine.reconstruct_set(forms)
        self.assertGreaterEqual(len(hyps), 1)
        best = hyps[0]
        self.assertGreater(best.confidence, 0.3)

    def test_pie_mater_cognates(self) -> None:
        forms = {
            "lat": "mater",
            "grc": "meter",
            "ang": "mōdor",
            "skt": "matar",
            "cu": "mati",
        }
        hyps = self.engine.reconstruct_set(forms)
        self.assertGreaterEqual(len(hyps), 1)

    def test_pie_numerals(self) -> None:
        forms = {
            "lat": "septem",
            "grc": "hepta",
            "skt": "sapta",
            "got": "sibun",
            "ang": "seofon",
        }
        hyps = self.engine.reconstruct_set(forms)
        self.assertGreaterEqual(len(hyps), 1)
        self.assertGreater(hyps[0].confidence, 0.0)

    def test_sound_change_sequence_includes_named(self) -> None:
        forms = {"lat": "pater", "grc": "pater", "skt": "pitar"}
        hyps = self.engine.reconstruct_set(forms)
        seq = hyps[0].sound_change_sequence
        named = [s for s in seq if "named_transform" in s]
        self.assertGreaterEqual(len(named), 1)

    def test_scholar_prior_boosts_confidence(self) -> None:
        forms = {"lat": "pater", "grc": "pater", "skt": "pitar", "got": "fadar"}
        no_prior = self.engine.reconstruct_set(forms)[0]
        with_prior = self.engine.reconstruct_set(forms, known_proto="pater")[0]
        self.assertGreaterEqual(with_prior.confidence, no_prior.confidence)

    def test_leave_one_out_applicable_with_three_plus(self) -> None:
        forms = {"lat": "pater", "grc": "pater", "skt": "pitar"}
        hyps = self.engine.reconstruct_set(forms)
        loo = hyps[0].leave_one_out
        self.assertTrue(loo.get("applicable"))

    def test_two_languages_no_loo(self) -> None:
        forms = {"lat": "pater", "grc": "pater"}
        hyps = self.engine.reconstruct_set(forms)
        self.assertFalse(hyps[0].leave_one_out["applicable"])

    def test_correspondence_sets_discovered(self) -> None:
        forms = {"lat": "pater", "grc": "pater", "skt": "pitar"}
        hyps = self.engine.reconstruct_set(forms)
        self.assertGreaterEqual(len(hyps[0].correspondence_sets), 1)

    def test_conflicting_flags_affect_confidence(self) -> None:
        forms = {"lat": "pater", "grc": "pater"}
        no_flags = self.engine.reconstruct_set(forms)[0]
        with_flags = self.engine.reconstruct_set(forms, flags_by_lang={"lat": ["borrowed"]})[0]
        self.assertGreaterEqual(no_flags.confidence, with_flags.confidence)

    def test_competing_hypotheses_generated(self) -> None:
        forms = {"lat": "pater", "grc": "pater", "skt": "pitar"}
        hyps = self.engine.reconstruct_set(forms)
        self.assertGreaterEqual(len(hyps[0].competing_hypotheses), 1)

    def test_fallthrough_short_forms(self) -> None:
        forms = {"lat": "ma", "grc": "me"}
        hyps = self.engine.reconstruct_set(forms)
        self.assertGreaterEqual(len(hyps), 1)


class TestSoundChangeApplier(unittest.TestCase):
    def test_apply_simple_substitution(self) -> None:
        rules = [SoundChangeRule("p", "f", name="grimm_p")]
        applier = SoundChangeApplier(rules)
        result = applier.apply("pater")
        self.assertEqual(result, "fater")

    def test_apply_context_sensitive(self) -> None:
        rules = [
            SoundChangeRule("t", "ts", right_ctx="a", name="high_german_t"),
        ]
        applier = SoundChangeApplier(rules)
        result = applier.apply("tata")
        self.assertEqual(result, "tsatsa")

    def test_from_branch_transforms(self) -> None:
        transforms = [
            ("p", "f", "grimm_p"),
            ("t", "þ", "grimm_t"),
            ("k", "h", "grimm_k"),
        ]
        applier = SoundChangeApplier.from_branch_transforms(transforms)
        result = applier.apply("pater")
        self.assertEqual(result, "faþer")

    def test_apply_to_languages(self) -> None:
        transforms = {
            "got": [("p", "f", "grimm_p"), ("t", "þ", "grimm_t")],
            "lat": [("p", "p", "retain"), ("t", "t", "retain")],
        }
        applier = SoundChangeApplier()
        predicted = applier.apply_to_languages("pater", transforms)
        self.assertEqual(predicted["lat"], "pater")
        self.assertEqual(predicted["got"], "faþer")

    def test_score_prediction_perfect(self) -> None:
        rules = [SoundChangeRule("p", "p", name="retain")]
        applier = SoundChangeApplier()
        score = applier.score_prediction("pater", "pater", rules)
        self.assertTrue(score["perfect_match"])
        self.assertGreaterEqual(score["similarity"], 0.99)

    def test_score_prediction_partial(self) -> None:
        rules = [SoundChangeRule("p", "f", name="grimm")]
        applier = SoundChangeApplier()
        score = applier.score_prediction("pater", "fader", rules)
        self.assertFalse(score["perfect_match"])


class TestRealPIEReconstruction(unittest.TestCase):
    """End-to-end reconstruction of well-known PIE etyma."""

    def setUp(self) -> None:
        self.engine = CorrespondenceEngine()

    def test_reconstruct_pie_numerals(self) -> None:
        cases = [
            ({"lat": "duo", "grc": "duo", "skt": "dva", "got": "twai"}, "dwo"),
            ({"lat": "tres", "grc": "treis", "skt": "trayas", "ang": "þrie"}, "trei"),
            ({"lat": "quinque", "grc": "pente", "skt": "panca", "ang": "fif"}, "penkwe"),
        ]
        for forms, expected_root in cases:
            hyps = self.engine.reconstruct_set(forms)
            self.assertGreaterEqual(len(hyps), 1, f"failed for {forms}")
            self.assertGreater(hyps[0].confidence, 0.1, f"low confidence for {forms}: {hyps[0]}")

    def test_grimms_law_detected(self) -> None:
        forms = {
            "lat": "pater",
            "got": "fadar",
            "ang": "fæder",
            "non": "faðir",
        }
        hyps = self.engine.reconstruct_set(forms)
        seq = hyps[0].sound_change_sequence
        grimm_rules = [s for s in seq if s.get("named_transform", "").startswith("grimm")]
        self.assertGreaterEqual(
            len(grimm_rules),
            1,
            f"Grimm's law rules not detected in {seq}",
        )


if __name__ == "__main__":
    unittest.main()
