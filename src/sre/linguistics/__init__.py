"""Independently replaceable linguistic search engine (no Dantomax imports)."""

from .bayesian import bayesian_phylogeny
from .correspondence_engine import CorrespondenceEngine, ProtoHypothesis
from .induction import (
    CorrespondenceInducer,
    PhonologicalPattern,
    induce_correspondences,
    merge_with_handcrafted,
)
from .lineage import format_human_lineage
from .phylogeny import PhyloNode, build_phylogeny, build_phylogeny_nj, compute_distance_matrix, neighbor_joining, upgma

__all__ = [
    "bayesian_phylogeny",
    "CorrespondenceEngine",
    "CorrespondenceInducer",
    "PhonologicalPattern",
    "PhyloNode",
    "ProtoHypothesis",
    "build_phylogeny",
    "build_phylogeny_nj",
    "compute_distance_matrix",
    "format_human_lineage",
    "induce_correspondences",
    "merge_with_handcrafted",
    "neighbor_joining",
    "upgma",
]