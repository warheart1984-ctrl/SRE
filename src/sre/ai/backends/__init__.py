"""Analyzer backend package."""

from .base import AnalysisBundle, AnalyzerBackend, enforce_evidence_anchors, evidence_id_set
from .factory import BACKEND_NAMES, create_analyzer_backend, resolve_backend_name
from .ml import MlAnalyzerBackend, MlAnalyzerProvider, MlBackendUnavailable
from .providers import CharacterNgramMlProvider, LlmAnalyzerProvider, create_ml_provider
from .rule import RuleAnalyzerBackend
from .statistical import StatisticalAnalyzerBackend

__all__ = [
    "BACKEND_NAMES",
    "AnalysisBundle",
    "AnalyzerBackend",
    "CharacterNgramMlProvider",
    "LlmAnalyzerProvider",
    "MlAnalyzerBackend",
    "MlAnalyzerProvider",
    "MlBackendUnavailable",
    "RuleAnalyzerBackend",
    "StatisticalAnalyzerBackend",
    "create_analyzer_backend",
    "create_ml_provider",
    "enforce_evidence_anchors",
    "evidence_id_set",
    "resolve_backend_name",
]
