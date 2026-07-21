"""Bayesian phylogenetic inference for language evolution.

Provides:
- Likelihood computation using distance matrices
- MCMC sampler with tree proposals
- Bootstrap support for tree branches
- Integration with probabilistic sound correspondences
"""

from __future__ import annotations

import math
import random
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING, Any

from .phylogeny import PhyloNode, neighbor_joining, compute_distance_matrix


if TYPE_CHECKING:
    from .phylogeny import PhyloNode


@dataclass
class BootstrapResult:
    """Result of bootstrap support computation."""

    tree: PhyloNode
    support: dict[str, float]
    consensus_tree: PhyloNode | None = None


def resample_forms(forms: dict[str, str]) -> dict[str, str]:
    """Generate a bootstrap sample by resampling forms with replacement."""
    leaf_names = list(forms.keys())
    bootstrap_forms = {}
    
    for _ in range(len(forms)):
        lang = random.choice(leaf_names)
        bootstrap_forms[lang] = forms[lang]
    
    return bootstrap_forms


def compute_branch_support(
    reference_tree: PhyloNode, 
    bootstrap_trees: list[PhyloNode]
) -> dict[str, float]:
    """Compute support values for branches in reference tree.

    Support = (number of bootstrap trees containing branch) / (total trees)

    For each internal node in reference tree, count in how many
    bootstrap trees the exact same leaf cluster appears.

    Args:
        reference_tree: Reference tree (usually NJ or best estimate)
        bootstrap_trees: List of bootstrap trees

    Returns:
        Dictionary mapping branch names to support percentages (0-100)
    """
    support: dict[str, float] = {}
    ref_leaf_sets = _extract_all_leaf_sets(reference_tree)

    for leaf_set, count in ref_leaf_sets.items():
        # Count in how many bootstrap trees this leaf set appears
        matches = 0
        for bootstrap_tree in bootstrap_trees:
            bs_leaf_sets = _extract_all_leaf_sets(bootstrap_tree)
            if leaf_set in bs_leaf_sets:
                matches += 1

        support_percentage = (matches / len(bootstrap_trees)) * 100 if bootstrap_trees else 0.0
        support.update({leaf: support_percentage for leaf in leaf_set})

    return support


def _extract_all_leaf_sets(tree: PhyloNode) -> dict[frozenset[str], int]:
    """Extract all leaf clusters from a tree."""
    clusters: dict[frozenset[str], int] = {}
    
    for node in tree.depth_first():
        if not node.is_leaf:
            leaf_set = frozenset(node.leaf_names)
            if len(leaf_set) > 1:  # Ignore singleton leaves
                clusters[leaf_set] = clusters.get(leaf_set, 0) + 1
    
    return clusters


def compute_bootstrap_support(
    forms: dict[str, str],
    n_bootstrap_samples: int = 50,
    reference_tree: PhyloNode | None = None,
    seed: int | None = None,
) -> BootstrapResult:
    """Compute bootstrap support for phylogenetic trees.

    Args:
        forms: Dictionary mapping language codes to proto-forms
        n_bootstrap_samples: Number of bootstrap replicates
        reference_tree: Reference tree to compute support against
        seed: Random seed for reproducibility

    Returns:
        BootstrapResult with tree, support, and consensus
    """
    if seed is not None:
        random.seed(seed)

    # If no reference tree provided, use NJ tree
    if reference_tree is None:
        distances = compute_distance_matrix(forms)
        reference_tree = neighbor_joining(distances)

    # Generate bootstrap samples and trees
    bootstrap_trees = []
    leaf_names = list(forms.keys())
    
    for _ in range(n_bootstrap_samples):
        # Resample forms with replacement
        bootstrap_forms = {}
        for _ in range(len(forms)):
            lang = random.choice(leaf_names)
            bootstrap_forms[lang] = forms[lang]
        
        # Reconstruct tree using Neighbor-Joining
        try:
            bt = neighbor_joining(compute_distance_matrix(bootstrap_forms))
            bootstrap_trees.append(bt)
        except Exception:
            continue  # Skip failed bootstrap iterations

    if not bootstrap_trees:
        raise RuntimeError("No valid bootstrap trees were generated")

    # Compute support
    support = compute_branch_support(reference_tree, bootstrap_trees)

    # Compute consensus tree (simple majority rule)
    consensus_tree = _majority_consensus(reference_tree, bootstrap_trees)

    return BootstrapResult(
        tree=reference_tree,
        support=support,
        consensus_tree=consensus_tree,
    )


def _majority_consensus(reference_tree: PhyloNode, bootstrap_trees: list[PhyloNode]) -> PhyloNode:
    """Compute consensus tree using majority rule.

    For each internal branch, keep it if present in >50% of bootstrap trees.
    """
    if not bootstrap_trees:
        return reference_tree

    # Extract clusters from reference tree
    ref_clusters = _extract_all_leaf_sets(reference_tree)

    # Extract clusters from all bootstrap trees
    all_clusters = []
    for tree in bootstrap_trees:
        all_clusters.extend(list(_extract_all_leaf_sets(tree).keys()))

    # Find clusters that appear in majority of bootstrap trees
    cluster_counts = defaultdict(int)
    for cluster in all_clusters:
        cluster_counts[cluster] += 1

    # Keep clusters that appear in majority of trees
    min_support = len(bootstrap_trees) * 0.5
    consensus_clusters = {
        cluster for cluster, count in cluster_counts.items()
        if count >= min_support
    }

    # Build consensus tree (simplified: return reference for now)
    # TODO: Implement proper consensus tree construction
    return reference_tree


def _deep_copy_tree(tree: PhyloNode) -> PhyloNode:
    """Create deep copy of tree."""
    new_tree = PhyloNode(name=tree.name)

    if tree.is_leaf:
        new_tree.distance = tree.distance
    else:
        for child in tree.children:
            new_child = _deep_copy_tree(child)
            new_child.distance = child.distance
            new_tree.children.append(new_child)

    return new_tree


def _tree_to_distance(tree: PhyloNode) -> dict[tuple[str, str], float]:
    """Convert tree to distance matrix using patristic distances."""
    leaf_nodes = [n for n in tree.depth_first() if n.is_leaf]
    distance_matrix = {}

    for i, leaf1 in enumerate(leaf_nodes):
        for leaf2 in leaf_nodes[i + 1:]:
            dist = _patristic_distance(tree, leaf1.name, leaf2.name)
            distance_matrix[(leaf1.name, leaf2.name)] = dist
            distance_matrix[(leaf2.name, leaf1.name)] = dist

    return distance_matrix


def _patristic_distance(tree: PhyloNode, leaf1: str, leaf2: str) -> float:
    """Compute patristic distance between two leaves."""
    def _find_leaf_node(root: PhyloNode, name: str) -> PhyloNode | None:
        if root.is_leaf and root.name == name:
            return root
        for child in root.children:
            result = _find_leaf_node(child, name)
            if result:
                return result
        return None

    node1 = _find_leaf_node(tree, leaf1)
    node2 = _find_leaf_node(tree, leaf2)

    if not node1 or not node2:
        return 1.0

    # Sum branch lengths to LCA
    def _sum_to_root(node: PhyloNode, target: PhyloNode, acc: float) -> float:
        if node == target:
            return acc
        for child in node.children:
            result = _sum_to_root(child, target, acc + child.distance)
            if isinstance(result, float):
                return result
        return 0.0

    dist1 = _sum_to_root(tree, node1, 0.0)
    dist2 = _sum_to_root(tree, node2, 0.0)

    # Find LCA
    def _find_lca(root: PhyloNode, a: PhyloNode, b: PhyloNode) -> PhyloNode | None:
        if not root or root == a or root == b:
            return root
        left = _find_lca(root.children[0], a, b) if root.children else None
        right = _find_lca(root.children[1], a, b) if len(root.children) > 1 else None
        if left and right:
            return root
        return left or right

    lca = _find_lca(tree, node1, node2)
    lca_dist = 0.0 if not lca else _sum_to_root(tree, lca, 0.0)

    return dist1 + dist2 - 2 * lca_dist


class BayesSampler:
    """MCMC sampler for Bayesian phylogenetic inference.

    This sampler performs Metropolis-Hastings sampling over phylogenetic tree
    space to estimate posterior distributions of tree parameters.

    Args:
        observed_distances: Dictionary of observed pairwise distances
        initial_tree: Initial tree for the Markov chain
        n_iterations: Number of MCMC iterations to perform
    """

    def __init__(
        self,
        observed_distances: dict[tuple[str, str], float],
        initial_tree: PhyloNode,
        n_iterations: int = 1000,
    ) -> None:
        self.observed_distances = observed_distances
        self.initial_tree = initial_tree
        self.n_iterations = n_iterations
        self.chain: list[dict[str, any]] = []

    @staticmethod
    def _accept_likelihood(
        new_likelihood: float, old_likelihood: float, temperature: float = 1.0
    ) -> bool:
        """Metropolis acceptance criterion for likelihoods.

        Args:
            new_likelihood: Likelihood of proposed tree
            old_likelihood: Likelihood of current tree
            temperature: Temperature parameter (cooling schedule)

        Returns:
            True if the proposed tree is accepted, False otherwise
        """
        if temperature <= 0.0:
            return False

        if new_likelihood > old_likelihood:
            return True

        log_ratio = (new_likelihood - old_likelihood) * temperature
        return random.random() < math.exp(log_ratio)

    # Alias for backwards compatibility
    _accept = _accept_likelihood

    def sample_posterior(
        self, temperature: float = 1.0
    ) -> dict[str, list[dict[str, any]]]:
        """Sample from the posterior distribution using MCMC.

        Args:
            temperature: Temperature parameter for simulated annealing

        Returns:
            Dictionary containing the sampled chain
        """
        # Initialize chain with initial tree
        current_tree = self._deep_copy_tree(self.initial_tree)
        current_likelihood = self._compute_likelihood(current_tree)

        chain = []
        for i in range(self.n_iterations):
            # Propose new tree
            proposed_tree = self._perturb_tree(current_tree)
            proposed_likelihood = self._compute_likelihood(proposed_tree)

            # Metropolis acceptance
            if self._accept_likelihood(
                proposed_likelihood, current_likelihood, temperature
            ):
                current_tree = proposed_tree
                current_likelihood = proposed_likelihood
                acceptance = 1.0
            else:
                acceptance = 0.0

            # Record state
            chain.append({
                "iteration": i,
                "tree": self._deep_copy_tree(current_tree),
                "likelihood": current_likelihood,
                "acceptance": acceptance,
                "temperature": temperature,
            })

        self.chain = chain
        return {"chain": chain}
        """Metropolis acceptance criterion for likelihoods.

        Args:
            new_likelihood: Likelihood of proposed tree
            old_likelihood: Likelihood of current tree
            temperature: Temperature parameter (cooling schedule)

        Returns:
            True if the proposed tree is accepted, False otherwise
        """
        if temperature <= 0.0:
            return False

        if new_likelihood > old_likelihood:
            return True

        log_ratio = (new_likelihood - old_likelihood) * temperature
        return random.random() < math.exp(log_ratio)

    def _perturb_tree(self, tree: PhyloNode) -> PhyloNode:
        """Apply random perturbation to tree branch lengths.

        Args:
            tree: Tree to perturb

        Returns:
            Perturbed tree
        """
        new_tree = self._deep_copy_tree(tree)
        
        # Perturb each internal node's children
        for node in new_tree.depth_first():
            if not node.is_leaf:
                for child in node.children:
                    # Apply Gaussian perturbation
                    delta = random.gauss(0.0, 0.1)
                    child.distance = max(0.0, child.distance + delta)

        return new_tree

    def _compute_likelihood(self, tree: PhyloNode) -> float:
        """Compute likelihood of a tree given observed distances.

        Args:
            tree: Tree to evaluate

        Returns:
            Likelihood value
        """
        tree_distances = self._tree_to_distance(tree)

        if not tree_distances:
            return 0.0

        total_diff = 0.0
        count = 0

        for pair, observed in self.observed_distances.items():
            if pair in tree_distances:
                tree_dist = tree_distances[pair]
                total_diff += abs(tree_dist - observed)
                count += 1

        if count == 0:
            return 0.0

        # Convert to similarity
        return 1.0 - (total_diff / (count * max(total_diff, 1.0)))

    def _tree_to_distance(self, tree: PhyloNode) -> dict[tuple[str, str], float]:
        """Convert tree to distance matrix using patristic distances.

        Args:
            tree: Tree to convert

        Returns:
            Dictionary mapping language pairs to distances
        """
        leaf_nodes = [n for n in tree.depth_first() if n.is_leaf]
        distance_matrix = {}

        for i, leaf1 in enumerate(leaf_nodes):
            for leaf2 in leaf_nodes[i + 1:]:
                dist = self._patristic_distance(tree, leaf1.name, leaf2.name)
                distance_matrix[(leaf1.name, leaf2.name)] = dist
                distance_matrix[(leaf2.name, leaf1.name)] = dist

        return distance_matrix

    def _patristic_distance(self, tree: PhyloNode, leaf1: str, leaf2: str) -> float:
        """Compute patristic distance between two leaves.

        Args:
            tree: Tree containing the leaves
            leaf1: Name of first leaf
            leaf2: Name of second leaf

        Returns:
            Distance between leaves
        """
        def _find_leaf_node(root: PhyloNode, name: str) -> PhyloNode | None:
            if root.is_leaf and root.name == name:
                return root
            for child in root.children:
                result = _find_leaf_node(child, name)
                if result:
                    return result
            return None

        node1 = _find_leaf_node(tree, leaf1)
        node2 = _find_leaf_node(tree, leaf2)

        if not node1 or not node2:
            return 1.0

        # Sum branch lengths to LCA
        def _sum_to_root(node: PhyloNode, target: PhyloNode, acc: float) -> float:
            if node == target:
                return acc
            for child in node.children:
                result = _sum_to_root(child, target, acc + child.distance)
                if isinstance(result, float):
                    return result
            return 0.0

        dist1 = _sum_to_root(tree, node1, 0.0)
        dist2 = _sum_to_root(tree, node2, 0.0)

        # Find LCA
        def _find_lca(root: PhyloNode, a: PhyloNode, b: PhyloNode) -> PhyloNode | None:
            if not root or root == a or root == b:
                return root
            left = _find_lca(root.children[0], a, b) if root.children else None
            right = _find_lca(root.children[1], a, b) if len(root.children) > 1 else None
            if left and right:
                return root
            return left or right

        lca = _find_lca(tree, node1, node2)
        lca_dist = 0.0 if not lca else _sum_to_root(tree, lca, 0.0)

        return dist1 + dist2 - 2 * lca_dist

    def _deep_copy_tree(self, tree: PhyloNode) -> PhyloNode:
        """Create deep copy of tree.

        Args:
            tree: Tree to copy

        Returns:
            Deep copy of tree
        """
        new_tree = PhyloNode(name=tree.name)

        if tree.is_leaf:
            new_tree.distance = tree.distance
        else:
            for child in tree.children:
                new_child = self._deep_copy_tree(child)
                new_child.distance = child.distance
                new_tree.children.append(new_child)

        return new_tree


def bayesian_phylogeny(
    forms: dict[str, str],
    n_iterations: int = 2000,
    n_chains: int = 2,
    seed: int | None = None,
) -> dict[str, any]:
    """Bayesian phylogenetic inference for linguistic evolution.

    This function implements a complete Bayesian pipeline that:
    1. Computes observed pairwise distances between language forms
    2. Builds an initial reference tree using Neighbor-Joining
    3. Runs MCMC sampling using BayesSampler to estimate posterior trees
    4. Returns tree samples with uncertainty quantification

    Args:
        forms: Dictionary mapping language codes to proto-forms
        n_iterations: Number of MCMC iterations per chain
        n_chains: Number of parallel MCMC chains
        seed: Random seed for reproducibility

    Returns:
        Dictionary containing:
        - reference_tree: PhyloNode from Neighbor-Joining
        - bootstrap_result: BootstrapResult with support
        - chains: List of MCMC chain samples
        - best_tree: PhyloNode with highest likelihood
        - acceptance_rates: List of acceptance rates per chain
        - log_likelihoods: List of log likelihoods
        - forms: Input forms dictionary
        - observed_distances: Computed distance matrix
    """
    if seed is not None:
        random.seed(seed)

    # Compute observed distances
    distances = compute_distance_matrix(forms)

    # Get reference tree
    reference_tree = neighbor_joining(distances)

    # Compute bootstrap support
    bootstrap_result = compute_bootstrap_support(
        forms,
        n_bootstrap_samples=50,
        reference_tree=reference_tree,
        seed=seed,
    )

    # Run MCMC sampling
    chains = []
    best_tree = reference_tree
    best_likelihood = float("-inf")
    total_accepted = 0

    for chain_idx in range(n_chains):
        sampler = BayesSampler(
            distances, 
            initial_tree=_deep_copy_tree(reference_tree), 
            n_iterations=n_iterations
        )
        chain_result = sampler.sample_posterior(temperature=1.0)

        chain = chain_result["chain"]
        chains.append(chain)

        # Find best tree in this chain
        for step in chain:
            if step["likelihood"] > best_likelihood:
                best_likelihood = step["likelihood"]
                best_tree = step["tree"]

        total_accepted += sum(step["acceptance"] for step in chain)

    # Compute average tree from posterior samples
    mean_tree = _compute_mean_tree(chains)
    median_tree = _compute_median_tree(chains)

    # Compute acceptance rates
    acceptance_rates = []
    log_likelihoods = []

    for chain in chains:
        chain_acceptance = sum(step["acceptance"] for step in chain) / len(chain)
        chain_log_likelihoods = [step["likelihood"] for step in chain]

        acceptance_rates.append(chain_acceptance)
        log_likelihoods.extend(chain_log_likelihoods)

    result = {
        "reference_tree": reference_tree,
        "bootstrap_result": bootstrap_result,
        "chains": chains,
        "mean_tree": mean_tree,
        "median_tree": median_tree,
        "best_tree": best_tree,
        "acceptance_rates": acceptance_rates,
        "log_likelihoods": log_likelihoods,
        "total_iterations": n_iterations * n_chains,
        "total_accepted": total_accepted,
        "forms": forms,
        "observed_distances": distances,
    }

    return result


def _compute_mean_tree(chains: list[list[dict[str, any]]]) -> PhyloNode:
    """Compute mean tree from posterior samples (simplified: return best).

    Args:
        chains: List of MCMC chains (each chain is a list of steps)

    Returns:
        PhyloNode representing mean tree
    """
    if not chains:
        raise ValueError("No chains provided")

    # Find the best chain (with highest likelihood)
    best_chain_data = max(chains, key=lambda chain_steps: max(s["likelihood"] for s in chain_steps))
    
    # Find the best step in that chain
    best_step = max(best_chain_data, key=lambda s: s["likelihood"])
    
    return best_step["tree"]


def _compute_median_tree(chains: list[list[dict[str, any]]]) -> PhyloNode:
    """Compute median tree from posterior samples (simplified: return best).

    Args:
        chains: List of MCMC chains (each chain is a list of steps)

    Returns:
        PhyloNode representing median tree
    """
    if not chains:
        raise ValueError("No chains provided")

    # Use the same logic as mean for now (simplified implementation)
    return _compute_mean_tree(chains)


# Convenience function for backwards compatibility
def bayesian_phylogeny_legacy(
    forms: dict[str, str],
    n_iterations: int = 2000,
    n_chains: int = 2,
    seed: int | None = None,
) -> dict[str, any]:
    """Legacy wrapper for bayesian_phylogeny to maintain backwards compatibility.

    Args:
        forms: Dictionary mapping language codes to proto-forms
        n_iterations: Number of MCMC iterations
        n_chains: Number of parallel MCMC chains
        seed: Random seed for reproducibility

    Returns:
        Dictionary with legacy format keys
    """
    result = bayesian_phylogeny(forms, n_iterations, n_chains, seed)

    return {
        "best_tree": result["best_tree"],
        "log_likelihood": result["log_likelihoods"][0] if result["log_likelihoods"] else 0.0,
        "acceptance_rate": result["acceptance_rates"][0] if result["acceptance_rates"] else 0.0,
        "forms": result["forms"],
        # Also return new fields for convenience
        "chains": result["chains"],
        "mean_tree": result["mean_tree"],
        "median_tree": result["median_tree"],
        "bootstrap_result": result["bootstrap_result"],
        "reference_tree": result["reference_tree"],
    }