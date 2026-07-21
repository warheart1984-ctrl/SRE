"""Rule-based analyzer backend (default)."""

from __future__ import annotations

from typing import Any

from ..analysis_modules import CognateDetector, LexicalAnalyzer, PhonologicalAnalyzer
from .base import AnalysisBundle, AnalyzerBackend


class RuleAnalyzerBackend:
    """Wraps existing regex / stem / induction analyzers."""

    name = "rule"

    def __init__(self) -> None:
        self._lexical = LexicalAnalyzer()
        self._cognates = CognateDetector()
        self._phonology = PhonologicalAnalyzer(cognate_detector=self._cognates)

    def analyze(self, evidence_list: list[Any]) -> AnalysisBundle:
        return AnalysisBundle(
            lexical_clusters=self._lexical.analyze(evidence_list),
            phonological_shifts=self._phonology.analyze(evidence_list),
            cognate_groups=self._cognates.detect(evidence_list),
            backend=self.name,
            metadata={"strategy": "regex_stems_and_induction"},
        )


# Protocol structural check
_: AnalyzerBackend = RuleAnalyzerBackend()
