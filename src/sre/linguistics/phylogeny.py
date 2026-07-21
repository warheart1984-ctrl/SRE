"""Phylogenetic tree inference from correspondence data.

Provides:
- ``compute_distance_matrix`` — feature-weighted pairwise alignment distance
- ``upgma`` — UPGMA clustering → ``PhyloNode``
- ``neighbor_joining`` — Neighbor-Joining (no molecular clock assumption)
- ``to_newick`` — Newick-format serialisation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .alignment import weighted_align
from .features import feature_distance, segment
from .tokenization import tokenize


@dataclass
class PhyloNode:
    """Node in a phylogenetic tree (rooted, binary)."""

    name: str = ""
    children: list[PhyloNode] = field(default_factory=list)
    distance: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_leaf(self) -> bool:
        return not self.children

    @property
    def leaf_names(self) -> list[str]:
        if self.is_leaf:
            return [self.name]
        names: list[str] = []
        for c in self.children:
            names.extend(c.leaf_names)
        return names

    def to_newick(self, precision: int = 4) -> str:
        if self.is_leaf:
            return self.name
        children_str = ",".join(
            f"{c.to_newick(precision)}:{c.distance:.{precision}f}" for c in self.children
        )
        out = f"({children_str}){self.name}"
        return out

    def depth_first(self) -> list[PhyloNode]:
        nodes: list[PhyloNode] = [self]
        for c in self.children:
            nodes.extend(c.depth_first())
        return nodes


def compute_distance_matrix(
    forms: dict[str, str],
) -> dict[tuple[str, str], float]:
    """Feature-weighted pairwise distance matrix from aligned cognates.

    For each language pair, align their forms and compute a normalised
    feature distance per position.  Returns ``{(lang_a, lang_b): distance}``
    with ``0.0 ≤ distance ≤ 1.0``.
    """
    langs = sorted(forms.keys())
    tokenized = {lang: tokenize(f) for lang, f in forms.items()}
    dists: dict[tuple[str, str], float] = {}

    for i, la in enumerate(langs):
        for lb in langs[i + 1 :]:
            ta, tb = tokenized[la], tokenized[lb]
            path, _ = weighted_align(ta, tb)
            total_fd = 0.0
            aligned_pairs = 0
            for cell in path:
                if cell.a and cell.b:
                    sa, sb = segment(cell.a.symbol), segment(cell.b.symbol)
                    total_fd += feature_distance(sa, sb)
                    aligned_pairs += 1
                elif cell.a or cell.b:
                    # gap penalty
                    total_fd += 1.0
                    aligned_pairs += 1
            dist = total_fd / max(aligned_pairs, 1)
            dists[(la, lb)] = dist
            dists[(lb, la)] = dist

    for lang in langs:
        dists[(lang, lang)] = 0.0

    return dists


def compute_distance_matrix_from_alignments(
    alignments: dict[tuple[str, str], list[Any]],
) -> dict[tuple[str, str], float]:
    """Distance matrix from pre-computed alignments."""
    dists: dict[tuple[str, str], float] = {}
    for (la, lb), path in alignments.items():
        total_fd = 0.0
        aligned_pairs = 0
        for cell in path:
            if cell.a and cell.b:
                sa, sb = segment(cell.a.symbol), segment(cell.b.symbol)
                total_fd += feature_distance(sa, sb)
                aligned_pairs += 1
            elif cell.a or cell.b:
                total_fd += 1.0
                aligned_pairs += 1
        dist = total_fd / max(aligned_pairs, 1)
        dists[(la, lb)] = dist
        dists[(lb, la)] = dist
    return dists


def upgma(distances: dict[tuple[str, str], float]) -> PhyloNode:
    """UPGMA clustering → rooted ``PhyloNode``.

    *distances* should be a symmetric dict keyed by ``(a, b)``.
    Only the languages appearing in the keys are clustered.
    """
    # Collect active taxa
    taxa: set[str] = set()
    for a, b in distances:
        taxa.add(a)
        taxa.add(b)
    # Remap to mutable structures
    clusters: dict[str, PhyloNode] = {t: PhyloNode(name=t) for t in taxa}
    heights: dict[str, float] = {t: 0.0 for t in taxa}
    sizes: dict[str, int] = {t: 1 for t in taxa}
    active = set(taxa)

    def _d(a: str, b: str) -> float:
        return distances.get((a, b), distances.get((b, a), 1.0))

    while len(active) > 1:
        # Find closest pair
        best_pair: tuple[str, str] | None = None
        best_dist = float("inf")
        members = sorted(active)
        for i, a in enumerate(members):
            for b in members[i + 1 :]:
                d = _d(a, b)
                if d < best_dist:
                    best_dist = d
                    best_pair = (a, b)

        if best_pair is None:
            break  # disconnected graph

        a, b = best_pair
        new_name = f"({a}:{heights[a]},{b}:{heights[b]})"
        height = best_dist / 2.0
        internal = PhyloNode(
            name=best_pair[0][:3] + best_pair[1][:3],
            children=[clusters[a], clusters[b]],
            distance=height - heights[a],
        )
        clusters[a].distance = height - heights[a]
        clusters[b].distance = height - heights[b]
        clusters[new_name] = internal
        heights[new_name] = height
        sizes[new_name] = sizes[a] + sizes[b]

        # Update distances to new cluster (UPGMA average linkage)
        for other in active:
            if other in (a, b):
                continue
            d_ao = _d(a, other)
            d_bo = _d(b, other)
            sa, sb = sizes[a], sizes[b]
            d_new = (d_ao * sa + d_bo * sb) / (sa + sb)
            distances[(new_name, other)] = d_new
            distances[(other, new_name)] = d_new

        active.remove(a)
        active.remove(b)
        active.add(new_name)

    root_name = next(iter(active))
    root = clusters[root_name]
    root.name = ""
    return root


def build_phylogeny(forms: dict[str, str]) -> PhyloNode:
    """One-shot: distance matrix → UPGMA → root node."""
    dists = compute_distance_matrix(forms)
    return upgma(dists)


def neighbor_joining(distances: dict[tuple[str, str], float], **kwargs) -> PhyloNode:
    """Neighbor-Joining clustering → unrooted ``PhyloNode`` (rooted at midpoint).

    Unlike UPGMA, NJ does not assume a molecular clock.

    Parameters:
    -----------
    distances : dict
        Symmetric distance matrix {(a,b): dist}.
    **kwargs :
        leaf_attr: attribute name for leaf labels (default "name").
        internal_attr: attribute name for internal node labels (default "name").

    Returns:
    --------
    PhyloNode — rooted tree at the midpoint of the longest path.
    """
    leaf_attr = kwargs.get("leaf_attr", "name")
    internal_attr = kwargs.get("internal_attr", "name")

    # Collect active taxa
    taxa_set: set[str] = set()
    for a, b in distances:
        taxa_set.add(a)
        taxa_set.add(b)
    if len(taxa_set) < 2:
        return PhyloNode(**{leaf_attr: "empty", **{internal_attr: ""}})

    taxa = sorted(taxa_set)

    # Create leaf nodes with custom attribute names
    nodes: dict[str, PhyloNode] = {}
    for t in taxa:
        node = PhyloNode()
        setattr(node, leaf_attr, t)
        setattr(node, internal_attr, "")
        nodes[t] = node

    # Map node key to PhyloNode for distance updates
    node_map = nodes.copy()

    # Current distances
    dists = dict(distances)

    def _d(a: str, b: str) -> float:
        return dists.get((a, b), dists.get((b, a), 0.0))

    # Track nodes with a parent key for reconstruction
    active_nodes = sorted(taxa, key=lambda x: x[:3])  # alphabetical tie-break

    while len(active_nodes) > 2:
        # Compute Q matrix
        q, min_q_pair = _q_criterion(dists, active_nodes)
        a, b = min_q_pair

        # Compute branch lengths
        n = len(active_nodes)
        sum_a = sum(_d(a, k) for k in active_nodes if k != a)
        sum_b = sum(_d(b, k) for k in active_nodes if k != b)
        d_ab = _d(a, b)

        branch_a = 0.5 * d_ab + (sum_a - sum_b) / (2 * (n - 2))
        branch_b = d_ab - branch_a

        branch_a = max(branch_a, 0.0)
        branch_b = max(branch_b, 0.0)

        # Create new internal node
        internal = PhyloNode()
        setattr(internal, leaf_attr, "")
        setattr(internal, internal_attr, f"{a[:3]}{b[:3]}")
        internal.children = [node_map[a], node_map[b]]
        for child in internal.children:
            child.distance = branch_a if child.name == a else branch_b

        # Update distances to new node
        new_key = f"({a}:{branch_a:.6f},{b}:{branch_b:.6f})"
        node_map[new_key] = internal
        active_nodes.remove(a)
        active_nodes.remove(b)
        active_nodes.append(new_key)

        # Update distance matrix
        for k in node_map:
            if k not in (a, b, new_key):
                d_ak = _d(a, k)
                d_bk = _d(b, k)
                d_new = 0.5 * (d_ak + d_bk - d_ab)
                dists[(new_key, k)] = max(d_new, 0.0)
                dists[(k, new_key)] = max(d_new, 0.0)

    # Final join of last two taxa
    a, b = active_nodes
    d_ab = _d(a, b)
    branch_a = branch_b = d_ab / 2.0

    internal = PhyloNode()
    setattr(internal, leaf_attr, "")
    setattr(internal, internal_attr, f"{a[:3]}{b[:3]}")
    internal.children = [node_map[a], node_map[b]]
    for child in internal.children:
        child.distance = branch_a if child.name == a else branch_b

    # Root at midpoint
    root = _midpoint_root(internal)
    root.name = ""
    return root


def _q_criterion(
    dists: dict[tuple[str, str], float], taxa: list[str]
) -> tuple[dict[tuple[str, str], float], tuple[str, str]]:
    """Compute NJ Q-matrix: Q(i,j) = (n-2)*d(i,j) - sum_k d(i,k) - sum_k d(j,k).

    Returns Q matrix and pair minimizing Q (tie-break: min distance).
    """
    n = len(taxa)
    if n < 3:
        return {}, (taxa[0], taxa[1])

    # Precompute row sums
    row_sum = {}
    for t in taxa:
        row_sum[t] = sum(dists.get((t, o), dists.get((o, t), 0.0)) for o in taxa if o != t)

    q = {}
    for i, a in enumerate(taxa):
        for b in taxa[i + 1 :]:
            d_ab = dists.get((a, b), dists.get((b, a), 0.0))
            q[(a, b)] = (n - 2) * d_ab - row_sum[a] - row_sum[b]
            q[(b, a)] = q[(a, b)]

    min_q = min(q.values())
    candidates = [pair for pair, val in q.items() if abs(val - min_q) < 1e-10]
    if len(candidates) == 1:
        return q, candidates[0]

    # Tie-break: minimal distance
    return q, min(candidates, key=lambda p: dists.get(p, dists.get((p[1], p[0]), 0.0)))


def _midpoint_root(node: PhyloNode) -> PhyloNode:
    """Root an unrooted tree at its midpoint (longest path center)."""
    leaves = [n for n in node.depth_first() if n.is_leaf]

    if len(leaves) < 2:
        return node

    # Find diameter: longest path between any two leaves
    max_dist = -1.0
    endpoints = (None, None)
    for i, l1 in enumerate(leaves):
        for l2 in leaves[i + 1 :]:
            path = _path_between_leaves(node, l1.name, l2.name)
            if path:
                dist = sum(n.distance for n in path if n != path[0])
                if dist > max_dist:
                    max_dist = dist
                    endpoints = (l1, l2)

    if endpoints[0] is None:
        return node

    # Find midpoint along path
    path = _path_between_leaves(node, endpoints[0].name, endpoints[1].name)
    if not path:
        return node

    total = sum(n.distance for n in path if n != path[0])
    halfway = total / 2.0
    accum = 0.0
    for i, n in enumerate(path):
        if i == len(path) - 1:
            break
        accum += n.distance
        if accum >= halfway:
            # Split edge between path[i] and path[i+1]
            parent = path[i]
            child = path[i + 1]
            new_root = PhyloNode(name="midpoint", children=[parent, child], distance=0.0)
            overshoot = accum - halfway
            parent.distance = halfway
            child.distance = parent.distance + child.distance - overshoot
            return new_root
    return node


def _path_between_leaves(node: PhyloNode, leaf1: str, leaf2: str) -> list[PhyloNode] | None:
    """Find path between two leaf nodes."""
    def _find_path(current: PhyloNode, target: str, path: list[PhyloNode]) -> list[PhyloNode] | None:
        if current.name == target:
            return path + [current]
        for child in current.children:
            result = _find_path(child, target, path + [current])
            if result:
                return result
        return None

    return _find_path(node, leaf1, []) or _find_path(node, leaf2, [])


def build_phylogeny_nj(forms: dict[str, str]) -> PhyloNode:
    """One-shot: distance matrix → Neighbor-Joining → root node."""
    dists = compute_distance_matrix(forms)
    return neighbor_joining(dists)