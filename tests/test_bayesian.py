"""Tests for Bayesian phylogenetic inference."""

from __future__ import annotations

import pytest

from sre.linguistics.bayesian import BayesSampler
from sre.linguistics.bayesian import bayesian_phylogeny
from sre.linguistics.phylogeny import PhyloNode, compute_distance_matrix


class TestBayesSampler:
    def test_initialization(self) -> None:
        forms = {'lat': 'pater', 'got': 'fadar'}
        distances = compute_distance_matrix(forms)

        sampler = BayesSampler(distances, PhyloNode(name="root"), n_iterations=10)
        assert sampler.observed_distances == distances

    def test_perturb_tree(self) -> None:
        from sre.linguistics.phylogeny import PhyloNode

        leaf = PhyloNode(name="lat")
        internal = PhyloNode(name="", children=[leaf])
        tree = PhyloNode(name="root", children=[internal])

        sampler = BayesSampler({}, tree, n_iterations=1)
        new_tree = sampler._perturb_tree(tree)

        # Tree should be copied
        assert new_tree.name == tree.name
        assert len(new_tree.children) == len(tree.children)

    def test_compute_likelihood(self) -> None:
        from sre.linguistics.phylogeny import PhyloNode

        leaf1 = PhyloNode(name="lat")
        leaf2 = PhyloNode(name="got")
        internal = PhyloNode(name="", children=[leaf1, leaf2])
        tree = PhyloNode(name="root", children=[internal])

        forms = {'lat': 'pater', 'got': 'fadar'}
        sampler = BayesSampler(
            {("lat", "got"): 0.5, ("got", "lat"): 0.5},
            tree,
            n_iterations=1,
        )
        likelihood = sampler._compute_likelihood(tree)
        assert isinstance(likelihood, float)

    def test_accept(self) -> None:
        # Better likelihood should always be accepted
        assert BayesSampler._accept(0.8, 0.5, 1.0) is True

        # Worse likelihood may be accepted depending on random chance
        # We can't test deterministic acceptance
        pass


def test_bayesian_phylogeny_basic() -> None:
    forms = {'lat': 'pater', 'got': 'fadar', 'ang': 'fæder'}
    result = bayesian_phylogeny(forms, n_iterations=10, seed=42)

    assert "best_tree" in result
    assert "log_likelihoods" in result
    assert "acceptance_rates" in result
    assert "forms" in result

    assert result["forms"] == forms
    assert 0.0 <= result["acceptance_rates"][0] <= 1.0
    assert isinstance(result["log_likelihoods"][0], float)
    assert result["best_tree"] is not None


def test_bayesian_phylogeny_with_seed() -> None:
    forms = {'lat': 'pater', 'got': 'fadar'}

    result1 = bayesian_phylogeny(forms, n_iterations=10, seed=42)
    result2 = bayesian_phylogeny(forms, n_iterations=10, seed=42)

    # With same seed, results should be identical
    # (implementation detail)
    assert result1["log_likelihoods"][0] == result2["log_likelihoods"][0]
    assert result1["acceptance_rates"][0] == result2["acceptance_rates"][0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])