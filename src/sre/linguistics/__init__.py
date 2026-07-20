"""Independently replaceable linguistic search engine (no Dantomax imports)."""

from .correspondence_engine import CorrespondenceEngine, ProtoHypothesis
from .lineage import format_human_lineage

__all__ = [
    "CorrespondenceEngine",
    "ProtoHypothesis",
    "format_human_lineage",
]
