"""Built-in ML providers for the ``ml`` analyzer backend."""

from __future__ import annotations

import os
from typing import Any

from ..ml import MlAnalyzerProvider, MlBackendUnavailable
from .llm import LLM_PRESETS, LlmAnalyzerProvider, resolve_llm_settings
from .ngram_ml import CharacterNgramMlProvider

PROVIDER_NAMES = frozenset({"ngram", "llm"})


def create_ml_provider(
    name: str | None = None,
    *,
    config: dict[str, Any] | None = None,
) -> MlAnalyzerProvider:
    """
    Resolve a built-in ML provider.

    ``name`` / ``config['ml_provider_name']`` / ``SRE_ML_PROVIDER`` (default: ``ngram``).
    """
    cfg = config or {}
    raw = (
        (name or "")
        or str(cfg.get("ml_provider_name") or "")
        or os.environ.get("SRE_ML_PROVIDER", "ngram")
    ).strip().lower()
    if not raw or raw in {"none", "off", "disabled"}:
        raise MlBackendUnavailable(
            "No ML provider configured. Set SRE_ML_PROVIDER=ngram|llm or pass "
            "an injected ml_provider=..."
        )
    if raw == "ngram":
        return CharacterNgramMlProvider(
            n_min=int(cfg.get("ml_ngram_min") or 2),
            n_max=int(cfg.get("ml_ngram_max") or 3),
            similarity_threshold=float(cfg.get("ml_similarity_threshold") or 0.25),
        )
    if raw == "llm":
        return LlmAnalyzerProvider(
            url=cfg.get("llm_url") or None,
            api_key=cfg.get("llm_api_key") if "llm_api_key" in cfg else None,
            model=cfg.get("llm_model") or None,
            preset=cfg.get("llm_preset") or None,
            timeout_s=float(cfg.get("llm_timeout_s") or 120.0),
            temperature=float(cfg.get("llm_temperature") or 0.0),
            json_mode=bool(cfg.get("llm_json_mode", True)),
            fallback_phonology=bool(cfg.get("llm_fallback_phonology", True)),
        )
    raise MlBackendUnavailable(
        f"unknown ML provider: {raw!r}; built-in providers: {sorted(PROVIDER_NAMES)}"
    )


__all__ = [
    "PROVIDER_NAMES",
    "CharacterNgramMlProvider",
    "LlmAnalyzerProvider",
    "LLM_PRESETS",
    "create_ml_provider",
    "resolve_llm_settings",
]
