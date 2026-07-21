"""Optional ML analyzer backend — provider-injected or built-in ngram model."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from .base import AnalysisBundle, AnalyzerBackend


class MlBackendUnavailable(RuntimeError):
    """Raised when ML mode is selected but no provider can be resolved."""


@runtime_checkable
class MlAnalyzerProvider(Protocol):
    """
    Injected ML provider. Must return the same shape as other backends and
    MUST attach ``evidence_ids`` on every output row (FAC-E1).
    """

    def analyze(self, evidence_list: list[Any]) -> AnalysisBundle: ...


class MlAnalyzerBackend:
    """
    ML path. Uses an injected provider or a built-in one from the factory
    (default: character n-gram TF-IDF cosine model).

    Drive-G-1: without a resolvable provider this fails loudly.
    """

    name = "ml"

    def __init__(self, provider: MlAnalyzerProvider | None = None) -> None:
        self._provider = provider

    def analyze(self, evidence_list: list[Any]) -> AnalysisBundle:
        if self._provider is None:
            raise MlBackendUnavailable(
                "analyzer_backend=ml requires a provider. "
                "Use SRE_ML_PROVIDER=ngram (built-in), or pass "
                "ml_provider=<MlAnalyzerProvider> / config ml_provider_name=ngram."
            )
        bundle = self._provider.analyze(evidence_list)
        if not isinstance(bundle, AnalysisBundle):
            raise TypeError("MlAnalyzerProvider.analyze must return AnalysisBundle")
        return AnalysisBundle(
            lexical_clusters=list(bundle.lexical_clusters),
            phonological_shifts=list(bundle.phonological_shifts),
            cognate_groups=list(bundle.cognate_groups),
            backend=self.name,
            metadata={
                **dict(bundle.metadata or {}),
                "provider_class": type(self._provider).__name__,
                "provider": (bundle.metadata or {}).get("provider")
                or type(self._provider).__name__,
            },
        )


_: AnalyzerBackend = MlAnalyzerBackend()
