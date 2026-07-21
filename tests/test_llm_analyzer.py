"""LLM analyzer provider tests (mocked OpenAI-compatible HTTP)."""

from __future__ import annotations

import json
import threading
import unittest
from datetime import UTC, datetime
from http.server import HTTPServer

from sre.ai.backends.providers.llm import LlmAnalyzerProvider, resolve_llm_settings
from sre.ai.backends.providers.llm_mock import MockLlmHandler
from sre.ai.hlrm_agent import HLRMAIAgent
from sre.evidence.models import EvidenceType, LinguisticEvidence


def _ev(eid: str, form: str, gloss: str) -> LinguisticEvidence:
    return LinguisticEvidence(
        evidence_id=eid,
        evidence_type=EvidenceType.LEXICAL_ITEM,
        source_reference="llm-test-corpus",
        content={
            "form": form,
            "gloss": gloss,
            "language_code": "la",
            "period": "classical",
        },
        created_at=datetime.now(UTC),
        submitted_by="tester",
        sha256_hash="b" * 64,
        provenance_chain=[],
        constitutional_tags=["FAC-E"],
    )


class TestLlmAnalyzerProvider(unittest.TestCase):
    def setUp(self) -> None:
        self.evidence = [
            _ev("e1", "pater", "father"),
            _ev("e2", "padre", "father"),
            _ev("e3", "mater", "mother"),
        ]

    def test_requires_url_or_preset(self) -> None:
        with self.assertRaises(ValueError):
            LlmAnalyzerProvider(url="", preset="")

    def test_ollama_preset_defaults(self) -> None:
        url, key, model = resolve_llm_settings(preset="ollama")
        self.assertIn("11434", url)
        self.assertEqual(key, "ollama")
        self.assertEqual(model, "llama3.2:3b")
        provider = LlmAnalyzerProvider(preset="ollama")
        self.assertEqual(provider.model, "llama3.2:3b")

    def test_unknown_preset(self) -> None:
        with self.assertRaises(ValueError):
            resolve_llm_settings(preset="not-a-real-preset")

    def test_soft_fails_on_bad_json(self) -> None:
        def fake_post(url, headers, body, timeout_s):  # noqa: ARG001
            return json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": '{"lexical_clusters": [{"x": 1,}], "cognate_groups": []}',
                            }
                        }
                    ]
                }
            ).encode()

        provider = LlmAnalyzerProvider(
            url="http://llm.test/v1/chat/completions",
            model="tiny",
            http_post=fake_post,
        )
        bundle = provider.analyze(self.evidence)
        self.assertEqual(bundle.metadata.get("provider"), "llm")
        # Trailing comma is repaired; if parse still fails, ngram fallback anchors evidence.
        if bundle.metadata.get("analysis_fallback") == "ngram":
            self.assertTrue(
                bundle.lexical_clusters or bundle.cognate_groups,
                "ngram fallback should produce anchored rows",
            )
        else:
            self.assertIsInstance(bundle.lexical_clusters, list)

    def test_mocked_http_post_anchored(self) -> None:
        def fake_post(url, headers, body, timeout_s):  # noqa: ARG001
            req = json.loads(body.decode())
            self.assertEqual(req["model"], "test-model")
            analysis = {
                "lexical_clusters": [
                    {
                        "cluster_id": "llm:father",
                        "root": "pater",
                        "domain": "father",
                        "forms": ["pater", "padre"],
                        "evidence_ids": ["e1", "e2"],
                    },
                    {
                        "cluster_id": "llm:ghost",
                        "root": "zzz",
                        "forms": ["invented"],
                        "evidence_ids": ["not_real"],
                    },
                ],
                "cognate_groups": [
                    {
                        "group_id": "cog_father",
                        "evidence_ids": ["e1", "e2"],
                        "members": [
                            {"form": "pater", "evidence_id": "e1"},
                            {"form": "padre", "evidence_id": "e2"},
                        ],
                    }
                ],
                "phonological_shifts": [],
            }
            return json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": json.dumps(analysis),
                            }
                        }
                    ]
                }
            ).encode()

        provider = LlmAnalyzerProvider(
            url="http://llm.test/v1/chat/completions",
            model="test-model",
            api_key="secret",
            http_post=fake_post,
        )
        bundle = provider.analyze(self.evidence)
        ids = {c["cluster_id"] for c in bundle.lexical_clusters}
        self.assertIn("llm:father", ids)
        self.assertNotIn("llm:ghost", ids)  # FAC-E1 dropped invented ID
        self.assertTrue(all(c.get("evidence_ids") for c in bundle.lexical_clusters))

        agent = HLRMAIAgent(
            config={"analyzer_backend": "ml"},
            ml_provider=provider,
        )
        analysis = agent.analyze_evidence_patterns(self.evidence)
        hyps = agent.predict_proto_forms(analysis)
        self.assertTrue(hyps["hypotheses"])
        known = {"e1", "e2", "e3"}
        for h in hyps["hypotheses"]:
            self.assertTrue(set(h["evidence_links"]).issubset(known))

    def test_live_mock_server(self) -> None:
        server = HTTPServer(("127.0.0.1", 0), MockLlmHandler)
        host, port = server.server_address[:2]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://{host}:{port}/v1/chat/completions"
            provider = LlmAnalyzerProvider(url=url, model="sre-mock-llm", api_key=None)
            agent = HLRMAIAgent(
                config={"analyzer_backend": "ml", "ml_provider_name": "llm"},
                ml_provider=provider,
            )
            analysis = agent.analyze_evidence_patterns(self.evidence)
            self.assertEqual(analysis["metadata"].get("provider"), "llm")
            hyps = agent.predict_proto_forms(analysis)
            self.assertTrue(hyps["hypotheses"])
            for h in hyps["hypotheses"]:
                self.assertTrue(h["evidence_links"])
        finally:
            server.shutdown()


if __name__ == "__main__":
    unittest.main()
