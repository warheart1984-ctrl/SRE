"""Pluggable analyzer backends — FAC-E1 anchoring preserved."""

from __future__ import annotations

import unittest
from datetime import UTC, datetime

from sre.ai.backends import (
    AnalysisBundle,
    CharacterNgramMlProvider,
    MlAnalyzerBackend,
    MlBackendUnavailable,
    RuleAnalyzerBackend,
    StatisticalAnalyzerBackend,
    create_analyzer_backend,
    create_ml_provider,
    enforce_evidence_anchors,
)
from sre.ai.hlrm_agent import HLRMAIAgent
from sre.corpus.loader import seed_registry_from_corpus
from sre.evidence.models import EvidenceType, LinguisticEvidence
from sre.evidence.registry import EvidenceRegistry


def _ev(eid: str, form: str, gloss: str) -> LinguisticEvidence:
    return LinguisticEvidence(
        evidence_id=eid,
        evidence_type=EvidenceType.LEXICAL_ITEM,
        source_reference="backend-test-corpus",
        content={
            "form": form,
            "gloss": gloss,
            "language_code": "test",
            "period": "archaic",
        },
        created_at=datetime.now(UTC),
        submitted_by="tester",
        sha256_hash="a" * 64,
        provenance_chain=[],
        constitutional_tags=["FAC-E"],
    )


class TestAnalyzerBackends(unittest.TestCase):
    def setUp(self) -> None:
        self.evidence = [
            _ev("e1", "pater", "father"),
            _ev("e2", "padre", "father"),
            _ev("e3", "mater", "mother"),
        ]

    def test_rule_backend_anchors(self) -> None:
        bundle = RuleAnalyzerBackend().analyze(self.evidence)
        self.assertEqual(bundle.backend, "rule")
        self.assertTrue(any(c.get("evidence_ids") for c in bundle.lexical_clusters))

    def test_statistical_backend_anchors(self) -> None:
        bundle = StatisticalAnalyzerBackend().analyze(self.evidence)
        self.assertEqual(bundle.backend, "statistical")
        for group in bundle.cognate_groups:
            self.assertTrue(group.get("evidence_ids"))

    def test_enforce_drops_unanchored(self) -> None:
        dirty = AnalysisBundle(
            lexical_clusters=[
                {"cluster_id": "ok", "evidence_ids": ["e1"], "root": "pater"},
                {"cluster_id": "bad", "evidence_ids": [], "root": "x"},
                {"cluster_id": "ghost", "evidence_ids": ["missing"], "root": "y"},
            ],
            backend="test",
        )
        clean = enforce_evidence_anchors(dirty, known_evidence_ids={"e1", "e2"})
        self.assertEqual(len(clean.lexical_clusters), 1)
        self.assertEqual(clean.lexical_clusters[0]["cluster_id"], "ok")

    def test_bare_ml_backend_without_provider_fails(self) -> None:
        with self.assertRaises(MlBackendUnavailable):
            MlAnalyzerBackend().analyze(self.evidence)

    def test_ml_disabled_provider_fails(self) -> None:
        with self.assertRaises(MlBackendUnavailable):
            create_ml_provider("none")
        with self.assertRaises(MlBackendUnavailable):
            HLRMAIAgent(config={"analyzer_backend": "ml", "ml_provider_name": "none"})

    def test_builtin_ngram_ml_provider(self) -> None:
        provider = CharacterNgramMlProvider(similarity_threshold=0.2)
        provider.fit(self.evidence)
        bundle = provider.analyze(self.evidence)
        self.assertEqual(bundle.metadata.get("model"), "character_ngram_tfidf_cosine")
        self.assertTrue(bundle.lexical_clusters)
        for cluster in bundle.lexical_clusters:
            self.assertTrue(cluster.get("evidence_ids"))

        agent = HLRMAIAgent(config={"analyzer_backend": "ml"})
        analysis = agent.analyze_evidence_patterns(self.evidence)
        self.assertEqual(analysis["analyzer_backend"], "ml")
        self.assertIn(
            analysis["metadata"].get("provider"),
            {"ngram", "CharacterNgramMlProvider"},
        )
        hyps = agent.predict_proto_forms(analysis)
        self.assertTrue(hyps["hypotheses"])
        self.assertTrue(all(h.get("evidence_links") for h in hyps["hypotheses"]))

    def test_ml_with_injected_provider(self) -> None:
        class FakeMl:
            def analyze(self, evidence_list):
                ids = [e.evidence_id for e in evidence_list]
                return AnalysisBundle(
                    lexical_clusters=[
                        {
                            "cluster_id": "ml:pater",
                            "root": "pater",
                            "evidence_ids": ids[:2],
                            "forms": ["pater", "padre"],
                        }
                    ],
                    cognate_groups=[
                        {
                            "group_id": "ml_cog",
                            "evidence_ids": ids[:2],
                            "members": [],
                        }
                    ],
                    backend="ml",
                )

        agent = HLRMAIAgent(
            config={"analyzer_backend": "ml"},
            ml_provider=FakeMl(),
        )
        analysis = agent.analyze_evidence_patterns(self.evidence)
        self.assertEqual(analysis["analyzer_backend"], "ml")
        hyps = agent.predict_proto_forms(analysis)
        self.assertTrue(hyps["hypotheses"])
        self.assertTrue(all(h.get("evidence_links") for h in hyps["hypotheses"]))

    def test_ml_on_ie_corpus(self) -> None:
        registry = EvidenceRegistry()
        seeded = seed_registry_from_corpus(
            registry,
            path="ie",
            evidence_ids=None,
        )
        # Keep batch modest if corpus is large
        sample = seeded[:40] if len(seeded) > 40 else seeded
        self.assertGreaterEqual(len(sample), 3)
        agent = HLRMAIAgent(config={"analyzer_backend": "ml", "ml_provider_name": "ngram"})
        analysis = agent.analyze_evidence_patterns(sample)
        self.assertEqual(analysis["analyzer_backend"], "ml")
        self.assertIn("vocab_size", analysis["metadata"])
        self.assertGreater(analysis["metadata"]["vocab_size"], 0)
        hyps = agent.predict_proto_forms(analysis)
        self.assertTrue(hyps["hypotheses"])
        known = {e.evidence_id for e in sample}
        for h in hyps["hypotheses"]:
            links = set(h["evidence_links"])
            self.assertTrue(links)
            self.assertTrue(links.issubset(known))

    def test_agent_rule_and_statistical(self) -> None:
        rule_agent = HLRMAIAgent(config={"analyzer_backend": "rule"})
        stat_agent = HLRMAIAgent(config={"analyzer_backend": "statistical"})
        rule = rule_agent.analyze_evidence_patterns(self.evidence)
        stat = stat_agent.analyze_evidence_patterns(self.evidence)
        self.assertEqual(rule["analyzer_backend"], "rule")
        self.assertEqual(stat["analyzer_backend"], "statistical")
        for analysis in (rule, stat):
            hyps = (rule_agent if analysis is rule else stat_agent).predict_proto_forms(analysis)
            self.assertTrue(hyps["hypotheses"])
            for h in hyps["hypotheses"]:
                self.assertTrue(h["evidence_links"])

    def test_predict_rejects_empty_anchors(self) -> None:
        agent = HLRMAIAgent()
        with self.assertRaises(ValueError) as ctx:
            agent.predict_proto_forms({"lexical_clusters": [], "cognate_groups": []})
        self.assertIn("AI-01", str(ctx.exception))

    def test_factory_unknown(self) -> None:
        with self.assertRaises(ValueError):
            create_analyzer_backend("nope")


if __name__ == "__main__":
    unittest.main()
