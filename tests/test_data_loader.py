"""Tests for data loading utilities."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sre.data import load_ancestor_hints, load_json_data


class TestLoadAncestorHints(unittest.TestCase):
    def test_load_from_default_path(self) -> None:
        hints = load_ancestor_hints()
        self.assertGreaterEqual(len(hints), 30)
        self.assertIn("pater", hints)
        self.assertIn("mater", hints)
        self.assertIn("mah", hints)

    def test_load_from_custom_path(self) -> None:
        data = {"foo": "Proto-Foo *FOO-"}
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "hints.json"
            p.write_text(json.dumps(data), encoding="utf-8")
            hints = load_ancestor_hints(p)
        self.assertEqual(hints["foo"], "Proto-Foo *FOO-")

    def test_load_missing_file(self) -> None:
        hints = load_ancestor_hints("/nonexistent/path.json")
        self.assertEqual(hints, {})


class TestLoadJsonData(unittest.TestCase):
    def test_load_existing(self) -> None:
        data = load_json_data("ancestor_hints.json")
        self.assertIsInstance(data, dict)
        self.assertIn("pater", data)

    def test_load_missing(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_json_data("nonexistent_file.json")


if __name__ == "__main__":
    unittest.main()
