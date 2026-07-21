"""Corpus loading utilities for FRA / IE vertical slices."""

from .loader import (
    CORPUS_CATALOG,
    corpus_item_to_evidence_data,
    default_corpus_path,
    list_evidence_ids,
    load_corpus,
    resolve_corpus_path,
    seed_registry_from_corpus,
)

__all__ = [
    "CORPUS_CATALOG",
    "DEFAULT_CORPUS",
    "IE_CORPUS",
    "MYTHAR_LEXICON",
    "corpus_item_to_evidence_data",
    "default_corpus_path",
    "list_evidence_ids",
    "load_corpus",
    "resolve_corpus_path",
    "seed_registry_from_corpus",
]


def __getattr__(name: str):
    if name == "DEFAULT_CORPUS":
        return default_corpus_path()
    if name == "IE_CORPUS":
        return resolve_corpus_path("ie")
    if name == "MYTHAR_LEXICON":
        return resolve_corpus_path("mythar-lex")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
