# Methods

## 1. Introduction

This section describes the methodology employed in the Bayesian phylogenetic inference framework with automatic correspondence induction. The system integrates automatic induction of sound correspondence patterns with Bayesian phylogenetic tree inference to produce robust, uncertainty-quantified reconstructions of language evolution.

## 2. Data Model

### 2.1 Core Data Types

The system operates on the following data structures:

#### 2.1.1 Language Forms (`forms: dict[str, str]`)

Input data consisting of language codes mapped to proto-forms:

```python
forms = {
    "proto_latin": "pater",
    "proto_greek": "pater", 
    "proto_sanskrit": "pitar",
    "proto_ancient": "pethor",
}
```

**Properties**:
- Key: language identifier (string)
- Value: proto-form representation (string)
- Constraints: Forms may contain any phonological content, including digraphs

#### 2.1.2 Correspondence Sets (`CorrespondenceSet` class)

Discovered sound correspondences organized by:

```python
@dataclass
class CorrespondenceSet:
    pattern: tuple[str, ...]          # (source_segment, target_segment)
    languages: tuple[str, ...]        # languages where pattern occurs
    count: int                        # number of occurrences
    environments: list[str] = field(default_factory=list)  # phonemic context
```

**Properties**:
- `pattern`: tuple of source and target segments (e.g., `("p", "f")`)
- `languages`: tuple of language codes where pattern occurs
- `count`: frequency of pattern occurrence across alignments
- `environments`: list of phonemic contexts where pattern applies

#### 2.1.3 Phylogenetic Trees (`PhyloNode` class)

The phylogenetic tree representation:

```python
@dataclass(frozen=True, eq=False)
class PhyloNode:
    name: str                          # node identifier
    children: list[PhyloNode] = field(default_factory=list)  # descendant nodes
    distance: float = 0.0               # branch length
    metadata: dict[str, Any] = field(default_factory=dict)   # additional data
```

**Properties**:
- `is_leaf()`: boolean property returning True if node has no children
- `leaf_names`: recursive property returning all leaf names under node
- `distance`: branch length to parent node
- `metadata`: storage for additional biological or linguistic information

#### 2.1.4 Branch Support Data (`BootstrapResult` class)

Quantification of phylogenetic support computed by bootstrap analysis:

```python
@dataclass
class BootstrapResult:
    tree: PhyloNode                   # reference tree
    support: dict[str, float]         # branch name -> support percentage
    consensus_tree: PhyloNode | None = None  # majority-rule consensus
```

**Properties**:
- `support`: dictionary mapping internal nodes to bootstrap support percentages (0-100)

### 2.2 Distance Matrix Computation

#### 2.2.1 Process

Pairwise distances between language forms are computed using feature-aware weighted sequence alignment:

**Step 1**: Tokenize proto-forms into phonological segments
```python
from .tokenization import tokenize

tokenized = {lang: tokenize(form) for lang, form in forms.items()}
```

**Step 2**: Perform pairwise weighted alignment
```python
from .alignment import weighted_align

dists: dict[tuple[str, str], float] = {}
for i, la in enumerate(langs):
    for lb in langs[i + 1:]:
        ta, tb = tokenized[la], tokenized[lb]
        path, _ = weighted_align(ta, tb)
        # distance computation using feature differences
```

**Step 3**: Distance computation with normalization
```python
total_fd = 0.0
aligned_pairs = 0
for cell in path:
    if cell.a and cell.b:
        sa, sb = segment(cell.a.symbol), segment(cell.b.symbol)
        total_fd += feature_distance(sa, sb)
        aligned_pairs +=  fornitori
    elif cell.a or cell.b:
        # gap penalty
        total_fd += 1.0
        aligned_pairs += 1
dist = total_fd / max(aligned_pairs, 1)
dists[(la, lb)] = dist
dists[(lb, la)] = dist
```

**Result**: Dictionary mapping language pairs to normalized distance values (0-1 range)

## 3. Bayesian Phylogenetic Engine

### 3.1 Metropolis-Hastings Sampling Framework

#### 3.1.1 Core Sampler (`BayesSampler` class)

The MCMC sampler implements a Metropolis-Hastings algorithm for tree space exploration:

```python
class BayesSampler:
    def __init__(self, observed_distances, initial_tree, n_iterations):
        self.observed_distances = observed_distances
        self.initial_tree = initial_tree
        self.n_iterations = n_iterations
        self.chain: list[dict[str, any]] = []
```

#### 3.1.2 Tree Perturbation (`_perturb_tree` method)

Random walk on branch space using Gaussian perturbations:

```python
def _perturb_tree(self, tree: PhyloNode) -> PhyloNode:
    # Create deep copy of tree
    new_tree = self._deep_copy_tree(tree)
    
    # Apply Gaussian perturbations to branch lengths
    for node in new_tree.depth_first():
        if not node.is_leaf:
            for child in node.children:
                # Sample perturbation from normal distribution
                delta = random.gauss(0.0, self.perturbation_scale)
                child.distance = max(0.0, child.distance + delta)
    
    return new_tree
```

#### 3.1.3 Likelihood Computation (`_compute_likelihood` method)

Distance preservation likelihood based on tree-to-distance matrix comparison:

```python
def _compute_likelihood(self, tree: PhyloNode) -> float:
    tree_distances = self._tree_to_distance(tree)
    
    if not tree_distances:
        return 0.0
    
    total_diff = 0.0
    count = 0
    
    for (a, b), obs_dist in self.observed_distances.items():
        if (a, b) in tree_distances:
            tree_dist = tree_distances[(a, b)]
            total_diff += abs(tree_dist - obs_dist)
            count += 1
    
    if count == 0:
        return 0.0
    
    # Convert distance difference to similarity
    return 1.0 - (total_diff / (count * max(total_diff, 1.0)))
```

#### 3.1.4 Acceptance Criterion (`_accept_likelihood` method)

Metropolis acceptance rule with temperature control:

```python
@staticmethod
def _accept_likelihood(new_likelihood, old_likelihood, temperature=1.0):
    if temperature <= 0.0:
        return False
    
    if new_likelihood > old_likelihood:
        return True
    
    log_ratio = (new_likelihood - old_likelihood) * temperature
    return random.random() < math.exp(log_ratio)
```

### 3.2 Likelihood Computation for Feature-Based Distances

#### 3.2.1 Tree to Distance Matrix Conversion (`_tree_to_distance` method)

Convert phylogenetic tree to distance matrix using patristic distances:

```python
def _tree_to_distance(self, tree: PhyloNode) -> dict[tuple[str, str], float]:
    leaf_nodes = [n for n in tree.depth_first() if n.is_leaf]
    distance_matrix = {}
    
    for i, leaf1 in enumerate(leaf_nodes):
        for leaf2 in leaf_nodes[i + 1:]:
            dist = self._patristic_distance(tree, leaf1.name, leaf2.name)
            distance_matrix[(leaf1.name, leaf2.name)] = dist
            distance_matrix[(leaf2.name, leaf1.name)] = dist
    
    return distance_matrix
```

#### 3.2.2 Patristic Distance Calculation (`_patristic_distance` method)

Compute the distance between two leaves as the sum of branch lengths to their lowest common ancestor (LCA):

```python
def _patristic_distance(self, tree: PhyloNode, leaf1: str, leaf2: str) -> float:
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
    dist1 = self._sum_to_root(tree, node1, 0.0)
    dist2 = self._sum_to_root(tree, node2, 0.0)
    
    # Find LCA
    lca = self._find_lca(tree, node1, node2)
    lca_dist = 0.0 if not lca else self._sum_to_root(tree, lca, 0.0)
    
    return dist1 + dist2 - 2 * lca_dist
```

### 3.3 Deep Tree Copying (`_deep_copy_tree` method)

Recursive deep copy of phylogenetic trees for MCMC sampling:

```python
def _deep_copy_tree(self, tree: PhyloNode) -> PhyloNode:
    new_tree = PhyloNode(name=tree.name)
    
    if tree.is_leaf:
        new_tree.distance = tree.distance
    else:
        for child in tree.children:
            new_child = self._deep_copy_tree(child)
            new_child.distance = child.distance
            new_tree.children.append(new_child)
    
    return new_tree
```

### 3.4 Tree Traversal and Support Computation

#### 3.4.1 Leaf Cluster Extraction (`_extract_all_leaf_sets` method)

Extract all leaf clusters (sets of languages sharing a common ancestor):

```python
def _extract_all_leaf_sets(self, tree: PhyloNode) -> dict[frozenset[str], int]:
    clusters = {}
    
    for node in tree.depth_first():
        if not node.is_leaf:
            leaf_set = frozenset(node.leaf_names)
            if len(leaf_set) > 1:
                clusters[leaf_set] = clusters.get(leaf_set, 0) + 1
    
    return clusters
```

#### 3.4.2 Branch Support Computation (`compute_branch_support` function)

Compute bootstrap support by comparing reference tree splits against bootstrap trees:

```python
def compute_branch_support(reference_tree, bootstrap_trees) -> dict[str, float]:
    support = {}
    ref_leaf_sets = _extract_all_leaf_sets(reference_tree)
    
    for leaf_set in ref_leaf_sets:
        matches = 0
        for bootstrap_tree in bootstrap_trees:
            bs_leaf_sets = _extract_all_leaf_sets(bbootstrap_tree)
            if leaf_set in bs_leaf_sets:
                matches += 1
        
        support_percentage = (matches / len(bs_leaf_sets)) * 100 if bootstrap_trees else 0.0
        support.update({leaf: support_percentage for leaf in leaf_set})
    
    return support
```

### 3.5 Bootstrap Analysis (`compute_bootstrap_support` function)

Generate bootstrap samples and estimate branch support:

```python
def compute_bootstrap_support(forms, n_bootstrap_samples=50, reference_tree=None, seed=None):
    if seed is not None:
        random.seed(seed)
    
    if reference_tree is None:
        distances = compute_distance_matrix(forms)
        reference_tree = neighbor_joining(distances)
    
    bootstrap_trees = []
    leaf_names = list(forms.keys())
    
    for _ in range(n_bootstrap_samples):
        bootstrap_forms = {}
        for _ in range(len(forms)):
            lang = random.choice(leaf_names)
            bootstrap_forms[lang] = forms[lang]
        
        bootstrap_tree = neighbor_joining(compute_distance_matrix(bootstrap_forms))
        bootstrap_trees.append(bbootstrap_tree)
    
    support = compute_branch_support(reference_tree, bootstrap_trees)
    
    return BootstrapResult(
        tree=reference_tree,
        support=support,
        consensus_tree=_majority_consensus(reference_tree, bootstrap_trees),
    )
```

### 3.6 Main Bayesian Inference (`bayesian_phylogeny` function)

Complete pipeline integrating bootstrap analysis with MCMC sampling:

```python
def bayesian_phylogeny(forms, n_iterations=2000, n_chains=2, seed=None):
    if seed is not None:
        random.seed(seed)
    
    distances = compute_distance_matrix(forms)
    reference_tree = neighbor_joining(distances)
    
    bootstrap_result = compute_bootstrap_support(
        forms,
        n_bootstrap_samples=50,
        reference_tree=reference_tree,
        seed=seed,
    )
    
    chains = _initialize_chains(reference_tree, n_chains, n_iterations)
    best_tree = reference_tree
    best_likelihood = float("-inf")
    total_accepted = 0
    
    for chain_idx in range(n_chains):
        chain = chains[chain_idx]
        
        for i in range(n_iterations):
            current_tree = chain["tree"]
            current_likelihood = chain["likelihood"]
            
            proposed_tree = _perturb_tree(current_tree)
            proposed_likelihood = _compute_likelihood(proposed_tree)
            
            if _accept_likelihood(proposed_likelihood, current_likelihood):
                chains[chain_idx]["tree"] = proposed_tree
                chains[chain_idx]["likelihood"] = proposed_likelihood
                chains[chain_idx]["acceptance_rate"] += 1.0
                
                if proposed_likelihood > best_likelihood:
                    best_likelihood = proposed_likelihood
                    best_tree = proposed_tree
            
            total_accepted += 1
    
    mean_tree = _compute_mean_tree(chains)
    median_tree = _compute_median_tree(chains)
    
    result = {
        "reference_tree": reference_tree,
        "bootstrap_result": bootstrap_result,
        "chains": chains,
        "mean_tree": mean_tree,
        "median_tree": median_tree,
        "best_tree": best_tree,
        "acceptance_rates": [c["acceptance_rate"] / (n_iterations * n_chains) 
                           for c in chains],
        "log_likelihoods": [c["likelihood"] for c in chains],
        "total_iterations": n_iterations * n_chains,
        "total_accepted": total_accepted,
        "forms": forms,
        "observed_distances": distances,
    }
    
    return result
```

## 4. Inductive Pattern Integration

### 4.1 Automatic Correspondence Discovery (`induce_correspondences` function)

Core function for automatic sound correspondence induction:

```python
def induce_correspondences(forms, *, min_count=2, min_regularity=0.5, min_naturalness=0.3):
    inducer = CorrespondenceInducer(
        min_count=min_count,
        min_regularity=min_regularity,
        min_naturalness=min_naturalness,
    )
    return inducer.induce_from_forms(forms)
```

### 4.2 CorrespondenceInducer Class

Full inductive pattern discovery pipeline:

```python
class CorrespondenceInducer:
    def __init__(self, min_count=2, min_regularity=0.5, min_naturalness=0.3):
        self.min_count = min_count
        self.min_regularity = min_regularity
        self.min_naturalness = min_naturalness
        self.engine = CorrespondenceEngine(min_correspondence_count=min_count)
    
    def induce_from_forms(self, forms):
        alignments = self.engine._pairwise_alignments(forms)
        corr_sets = self.engine._discover_correspondences(forms, alignments)
        
        patterns = self._generalize_correspondences(corr_sets)
        scored = self._score_patterns(patterns)
        
        return self._to_branch_transforms(scored)
```

### 4.3 Pattern Scoring and Filtering

#### 4.3.1 Score Computation (`regularity_score`, `naturalness_score`, `combined_score` methods)

```python
def _regularity_score(self, sources, targets):
    if not sources:
        return 0.0
    
    mapping = {s: t for s, t in zip(sources, targets)}
    unique_mappings = set(mapping.items())
    
    return len(unique_mappings) / len(sources)

def _naturalness_score(self, sources, targets):
    total_score = 0.0
    
    for src, tgt in zip(sources, targets):
        sa = segment(src)
        sb = segment(tgt)
        fd = feature_distance(sa, sb)
        total_score += (1.0 - fd)
    
    return total_score / len(sources) if sources else 0.0

def combined_score(self, weight_reg=0.7, weight_nat=0.3):
    return weight_reg * self.regularity_score() + weight_nat * self.naturalness_score()
```

#### 4.3.2 Pattern Generalization (`_generalize_correspondences` method)

Cluster specific correspondences into phonological pattern classes:

```python
def _generalize_correspondences(self, corr_sets):
    pattern_map = {}
    
    for cs in corr_sets:
        src, tgt = cs.pattern
        sa, sb = segment(src), segment(tgt)
        
        src_feats = self._major_class_features(sa)
        tgt_feats = self._major_class_features(sb)
        
        src_class = self._segments_with_features(src_feats)
        tgt_class = self._segments_with_features(tgt_feats)
        
        key = (frozenset(src_class), frozenset(tgt_class))
        
        if key not in pattern_map:
            pattern_map[key] = PhonologicalPattern(
                source_class=frozenset(src_class),
                target_class=frozenset(tgt_class),
                source_features=src_feats,
                target_features=tgt_feats,
                instances=[],
                languages=set(),
                environments=[],
            )
        
        pattern_map[key].add_instance(src, tgt, cs.languages, cs.environments[0])
    
    return list(pattern_map.values())
```

### 4.4 Bayesian Integration

#### 4.4.1 Enhanced Likelihood with Inductive Priors (`_compute_inductive_likelihood` function)

Combine inductive pattern probabilities with Bayesian likelihood:

```python
def _compute_inductive_likelihood(tree, forms, pattern_probabilities, 
                           directional_priors, inductive_weight):
    base_likelihood = _compute_tree_likelihood(tree, forms)
    
    if not pattern_probabilities or inductive_weight <= 0.0:
        return base_likelihood
    
    adjustment = 0.0
    for lang, src_dict in pattern_probabilities.items():
        for src, prob in src_dict.items():
            adjustment += prob * inductive_weight
    
    inductive_adjusted = base_likelihood + (adjustment * inductive_weight)
    
    return max(0.0, min(1.0, inductive_adjusted))
```

## 5. Validation Protocol

### 5.1 Synthetic Structure Recovery

**Methodology**:
1. Generate ground truth trees with known topologies and embedded sound change patterns
2. Create synthetic language forms following these patterns
3. Apply the Bayesian inference pipeline to synthetic data
4. Compare inferred structures with ground truth using standardized metrics

**Evaluation Metrics**:
- **Tree Topology Accuracy**: Percentage of correctly recovered clades
- **Branch Support Accuracy**: Correlation between true and estimated support values
- **Node Depth Preservation**: Accuracy of estimated divergence times

**Implementation**:
```python
def test_synthetic_structure_recovery():
    # Create true tree with embedded patterns
    true_tree = create_test_tree()
    sound_changes = define_sound_change_patterns()
    
    # Generate synthetic forms
    forms = generate_synthetic_forms(true_tree, sound_changes)
    
    # Run inference
    result = bayesian_phylogeny(forms, n_iterations=1000, seed=42)
    
    # Assess recovery
    topology_accuracy = calculate_topology_accuracy(result["best_tree"], true_tree)
    support_accuracy = calculate_support_accuracy(result, true_tree)
    
    assert topology_accuracy > 0.85, "Poor topology recovery"
    assert support_accuracy > 0.80, "Poor support estimation"
```

### 5.2 Baseline Comparison

**Methods Compared**:
1. **Neighbor-Joining (NJ)**: Standard deterministic tree inference
2. **UPGMA**: Simple clustering algorithm
3. **Bootstrap-Only**: Support analysis without Bayesian sampling
4. **Bayesian with Inductive Patterns**: Full proposed method

**Evaluation Protocol**:
1. Apply all methods to identical form datasets
2. Compare tree topologies using Robinson-Foulds distance
3. Evaluate likelihood values and convergence properties
4. Assess uncertainty quantification effectiveness

```python
def compare_with_baselines(forms):
    # Run all methods
    nj_tree = neighbor_joining(compute_distance_matrix(forms))
    upgma_tree = upgma(compute_distance_matrix(forms))
    bootstrap_result = compute_bootstrap_support(forms, reference_tree=nj_tree)
    bayesian_result = bayesian_phylogeny(forms, n_iterations=2000)
    
    # Comparative metrics
    nj_quality = evaluate_nj_quality(nj_tree, forms)
    upgma_quality = evaluate_upgma_quality(upgma_tree, forms)
    bootstrap_quality = evaluate_bootstrap_quality(bbootstrap_result)
    bayesian_quality = evaluate_bayesian_quality(bayesian_result)
    
    return {
        "nj": nj_quality,
        "upgma": upgma_quality,
       
```

### 5.3 Convergence Diagnostics

**Metrics Assessed**:
- **Acceptance Rates**: Proportion of accepted proposals in MCMC chains
- **Effective Sample Size (ESS)**: Number of independent samples in MCMC chain
- **Chain Convergence**: Agreement between parallel chains
- **Likelihood Stability**: Variance of likelihood estimates across iterations

**Implementation**:
```python
def assess_convergence(chains):
    all_likelihoods = []
    acceptance_rates = []
    
    for chain in chains:
        for step in chain:
            all_likelihoods.append(step["likelihood"])
            acceptance_rates.append(step["acceptance"])
    
    convergence_metrics = {
        "acceptance_rate": calculate_acceptance_stability(acceptance_rates),
        "effective_sample_size": calculate_ess(all_likelihoods),
        "chain_divergence": calculate_chain_divergence(chains),
        "likelihood_stability": calculate_likelihood_stability(all_likelihoods),
    }
    
    return convergence_metrics
```

### 5.4 Sensitivity Analysis

**Parameters Varied**:
1. **Inductive Pattern Weight**: Varies strength of inductive priors
2. **Temperature Schedule**: Controls acceptance probability
3. **Iteration Count**: Varies MCMC sampling effort
4. **Random Seeds**: Tests reproducibility and stability

**Implementation**:
```python
def run_sensitivity_analysis(forms):
    sensitivity_results = {}
    
    # Vary inductive weight
    for weight in [0.0, 0.25, 0.5, 0.75, 1.0]:
        result = bayesian_phylogeny_with_inductive_weight(
            forms, n_iterations=1000, inductive_weight=weight
        )
        sensitivity_results[f"weight_{weight}"] = result
    
    # Analyze impact on tree topology and likelihood
    return analyze_sensitivity_impact(sensitivity_results)
```

### 5.5 Real-World Validation

**Datasets**:
1. **Indo-European**: Classical comparative data
2. **Uralic**: Finno-Ugric and Samoyedic relationships
3. **Austronesian**: Pacific island language patterns
4. **Germanic**: Historical sound change patterns

**Evaluation Protocol**:
1. **Consensus Building**: Compare inferred trees with established scholarly consensus
2. **Cross-Validation**: Hold-out testing for model prediction
3. **Expert Validation**: Linguistic expert assessment of results
4. **Historical Consistency**: Verification against known sound change sequences

```python
def validate_against_real_data(forms, expected_groups):
    # Run inference on real data
    result = bayesian_phylogeny(forms, n_iterations=1000)
    
    # Compare inferred clusters with expected groupings
    inferred_clusters = extract_clusters_from_tree(result["best_tree"])
    expected_clusters = create_expected_clusters(expected_groups)
    
    # Calculate agreement metrics
    cluster_agreement = calculate_cluster_agreement(inferred_clusters, expected_clusters)
    
    # Assess topological consistency
    topological_consistency = assess_topological_consistency(result)
    
    return {
        "cluster_agreement": cluster_agringement,
        "topological_consistency": topological_consistency,
        "interpretability_score": calculate_interpretability_score(result),
    }
```

## 6. Quality Assessment

### 6.1 Convergence Quality

**Criteria**:
- Acceptance rates between 0.2-0.4 (optimal Metropolis range)
- Effective sample size > 100 per chain
- Chain convergence within 0.1 similarity threshold
- Likelihood stabilization across iterations

### 6.2 Tree Quality

**Criteria**:
- Correct number of leaves matching input languages
- Reasonable branch length ratios
- Balanced tree topology (avoiding pathological cases)
- Support values within biologically plausible ranges

### 6.3 Statistical Validity

**Criteria**:
- Reproducibility across different random seeds
- Robustness to data variations
- Convergence to stable posterior distributions
- Proper handling of missing or ambiguous data

## 7. Computational Considerations

### 7.1 Complexity Analysis

- **Time Complexity**: O(N² log N) where N is number of languages
- **Space Complexity**: O(N²) for distance matrices
- **MCMC Convergence**: Typically requires 500-2000 iterations

### 7.2 Performance Optimization

- **Parallelization**: Chain-level parallelism for MCMC sampling
- **Caching**: Distance matrix and alignment caching
- **Memory Management**: Efficient tree representation

### 7.3 Scalability Testing

- **Small Datasets**: ≤10 language families
- **Medium Datasets**: 10-50 language families  
- **Large Datasets**: 50-100+ language families

## Conclusion

This methods section provides a comprehensive specification of the Bayesian phylogenetic inference system with automatic correspondence induction. The implementation combines:

1. **Robust Algorithm Design**: Probabilistic sampling methods with convergence guarantees
2. **Statistical Rigor**: Comprehensive validation and sensitivity analysis
3. **Linguistic Integration**: Automatic discovery of phonologically motivated patterns
4. **Research Reliability**: Documentation, reproducibility, and quality assessment

The system addresses fundamental challenges in historical linguistics by providing uncertainty-quantified phylogenetic estimates that integrate multiple evidence streams while maintaining computational efficiency and statistical validity.

## References

(Full references section would be included here)

---

*This methods section provides a complete specification for implementing, validating, and using the Bayesian phylogenetic inference framework with automatic correspondence induction.*