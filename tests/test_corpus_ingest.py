"""Corpus ingestion pipeline tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sre.corpus.ingest import ingest_csv, ingest_file, ingest_jsonl, ingest_records
from sre.evidence.registry import EvidenceRegistry


class TestCorpusIngest(unittest.TestCase):
    def test_ingest_records_inline(self) -> None:
        registry = EvidenceRegistry()
        summary = ingest_records(
            registry,
            [
                {
                    "evidence_id": "evid_ingest_001",
                    "form": "aqua",
                    "gloss": "water",
                    "source_reference": "Latin sample",
                    "language_code": "la",
                }
            ],
        )
        self.assertEqual(summary["accepted"], 1)
        ev = registry.get_evidence("evid_ingest_001")
        self.assertIsNotNone(ev)

    def test_ingest_jsonl_file(self) -> None:
        registry = EvidenceRegistry()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.jsonl"
            path.write_text(
                json.dumps(
                    {
                        "evidence_id": "evid_jsonl_001",
                        "form": "pater",
                        "gloss": "father",
                        "source_reference": "IE mini",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            rows = ingest_jsonl(registry, path)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].evidence_id, "evid_jsonl_001")

    def test_ingest_csv_file(self) -> None:
        registry = EvidenceRegistry()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.csv"
            path.write_text(
                "evidence_id,form,gloss,source_reference,evidence_type\n"
                "evid_csv_001,mater,mother,IE mini,lexical_item\n",
                encoding="utf-8",
            )
            rows = ingest_csv(registry, path, language_code="la")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].evidence_id, "evid_csv_001")

    def test_ingest_file_autodetect_jsonl(self) -> None:
        registry = EvidenceRegistry()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "auto.jsonl"
            path.write_text(
                json.dumps(
                    {
                        "evidence_id": "evid_auto_001",
                        "text": "demo",
                        "source_reference": "auto",
                    }
                ),
                encoding="utf-8",
            )
            summary = ingest_file(registry, path)
            self.assertEqual(summary["ingested"], 1)


if __name__ == "__main__":
    unittest.main()
