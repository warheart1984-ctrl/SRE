"""Factory for analyzer backends."""

from __future__ import annotations

import os
from typing import Any

from .base import AnalyzerBackend
from .ml import MlAnalyzerBackend, MlAnalyzerProvider
from .rule import RuleAnalyzerBackend
from .statistical import StatisticalAnalyzerBackend

BACKEND_NAMES = frozenset({"rule", "statistical", "ml"})


def resolve_backend_name(config: dict[str, Any] | None = None) -> str:
    cfg = config or {}
    raw = (
        (
            str(cfg.get("analyzer_backend") or "")
            or os.environ.get("SRE_ANALYZER_BACKEND", "")
            or "rule"
        )
        .strip()
        .lower()
    )
    if raw not in BACKEND_NAMES:
        raise ValueError(
            f"unknown analyzer_backend: {raw!r}; expected one of {sorted(BACKEND_NAMES)}"
        )
    return raw


def create_analyzer_backend(
    name: str | None = None,
    *,
    config: dict[str, Any] | None = None,
    ml_provider: MlAnalyzerProvider | None = None,
) -> AnalyzerBackend:
    """
    Build an analyzer backend.

    Selection order: explicit ``name`` → ``config['analyzer_backend']`` →
    ``SRE_ANALYZER_BACKEND`` → ``rule``.

    For ``ml``: uses injected ``ml_provider``, else ``create_ml_provider``
    (default built-in ``ngram``).
    """
    cfg = dict(config or {})
    backend_name = name or resolve_backend_name(cfg)
    if backend_name == "rule":
        return RuleAnalyzerBackend()
    if backend_name == "statistical":
        min_score = float(cfg.get("statistical_min_pair_score") or 0.35)
        return StatisticalAnalyzerBackend(min_pair_score=min_score)
    if backend_name == "ml":
        provider = ml_provider if ml_provider is not None else cfg.get("ml_provider")
        if provider is None:
            from .providers import create_ml_provider

            provider = create_ml_provider(config=cfg)
        return MlAnalyzerBackend(provider=provider)
    raise ValueError(f"unknown analyzer_backend: {backend_name!r}")
