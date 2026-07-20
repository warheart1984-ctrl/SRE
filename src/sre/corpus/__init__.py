"""Corpus loading utilities for FRA / IE vertical slices."""

from .loader import (
    CORPUS_CATALOG,
    DEFAULT_CORPUS,
    IE_CORPUS,
    MYTHAR_LEXICON,
    corpus_item_to_evidence_data,
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
    "list_evidence_ids",
    "load_corpus",
    "resolve_corpus_path",
    "seed_registry_from_corpus",
]
