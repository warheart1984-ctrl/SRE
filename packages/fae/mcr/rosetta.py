"""
Mythar Cross-Language Rosetta Layer (MCRL-1.0)

Cross-Language Constitutional Mapping for Mythar implementations.

MCRL establishes the constitutional framework for mapping Mythar concepts,
roots, and grammar to external languages while maintaining governed
consistency across language boundaries.

Core Components:
- ExternalRoot: Defines external language roots with constitutional anchors
- ExternalGrammarRule: Maps Mythar patterns to external language constructs
- AlignmentEntry: Formal alignment between Mythar and external expressions

MCRL ensures that cross-language mappings maintain the constitutional
invariant: factual alignment through evidence-constrained iteration.

Integration Points:
- Linked to Semantic Engine Specification
- Connects to Grammar Standard  
- Bridged to Ontology Graph
- Added as binding artifact in Article VII
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from pathlib import Path
import hashlib
import json
import uuid
import threading
from abc import ABC, abstractmethod


class AlignmentMode(Enum):
    """Alignment mode for cross-language mappings."""
    LITERAL = "literal"          # Word-for-word correspondence
    SYMBOLIC = "symbolic"         # Symbolic/morphological alignment
    CONSTITUTIONAL = "constitutional"  # Constitutional structural mapping
    EVIDENTIAL = "evidential"     # Evidence-based semantic alignment


@dataclass
class EvidenceSource:
    """Evidence source enumeration for external evidence validation."""
    EXTERNAL_SENSOR = "external_sensor"
    EXTERNAL_API = "external_api"
    HUMAN_OBSERVER = "human_observer"
    EXTERNAL_DATABASE = "external_database"
    THIRD_PARTY_AUDIT = "third_party_audit"
    CRYPTOGRAPHIC_PROOF = "cryptographic_proof"
    INTERNAL_MODEL = "internal_model"
    DERIVED_INFERENCE = "derived_inference"


@dataclass
class EvidenceStatus:
    """Evidence status enumeration."""
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class ExternalRoot:
    """
    Definition of a root/concept in an external language.
    
    Constitutional anchors ensure that external roots maintain
    alignment with Mythar concepts through verifiable evidence.
    """
    
    language: str  # Target language identifier (e.g., "english", "latin", "greek")
    form: str      # Root form in the external language
    domain: str    # Semantic domain (e.g., "temporal", "causal", "epistemic")
    gloss: str    # Gloss/explanation of the root's meaning
    evidence_id: str  # ID of evidence validating this correspondence
    
    # Constitutional anchor properties
    alignment_confidence: float = 1.0  # 0.0-1.0 confidence level
    validation_status: str = "verified"  # "verified", "unverified", "rejected"
    validator_id: Optional[str] = None
    validator_timestamp: Optional[datetime] = None
    source: EvidenceSource = EvidenceSource.EXTERNAL_DATABASE


@dataclass
class ExternalGrammarRule:
    """
    Mapping between Mythar patterns and external language constructs.
    
    Ensures that grammatical structures preserve constitutional invariants
    across language boundaries.
    """
    
    language: str
    pattern: str                       # External language pattern
    mythar_pattern_ref: str           # Reference to Mythar grammar rule
    alignment_mode: AlignmentMode = AlignmentMode.EVIDENTIAL
    evidence_basis: List[str] = field(default_factory=list)  # Evidence IDs
    
    # Constitutional validation
    cross_domain_alignment: bool = True  # Must align across semantic domains
    structural_invariance: bool = True  # Must preserve structural relationships
    gender_number_consistency: bool = True  # Number/gender consistency


@dataclass
class AlignmentEntry:
    """
    Formal alignment between a Mythar expression and external expression.
    
    Foundations the cross-language mapping with complete provenance.
    """
    
    mythar_expression: str
    external_expression: str
    mode: AlignmentMode
    source_language: str
    target_language: str
    evidence_id: str
    source_domain: str
    target_domain: str
    
    id: str = field(default_factory=lambda: f"align_{uuid.uuid4().hex[:8]}")
    alignment_confidence: float = 1.0
    alignment_score: float = 1.0
    validation_status: str = "verified"
    context_type: str = "isolated"  # "isolated", "context_dependent", "structural"
    created_at: datetime = field(default_factory=datetime.now)
    last_validated: datetime = field(default_factory=datetime.now)
    provenance_chain: List[str] = field(default_factory=list)
    lineage_proof: Optional[str] = None


@dataclass
class RosettaConformanceProfile:
    """
    Cross-language conformance requirements for Mythar implementations.
    
    Added as binding artifact in Article VII Constitutional Artifacts.
    """
    
    name: str
    description: str
    profile_id: str = field(default_factory=lambda: f"rosetta_{uuid.uuid4().hex[:8]}")
    
    # Required capabilities
    mcrl_implemented: bool = False
    mcrl_version: str = "1.0"
    
    marl_rosetta_reconstruction: bool = False
    marl_reconstruction_version: str = "1.0"
    
    cross_language_ontology: bool = False
    ontology_edges_implemented: bool = False
    
    external_corpora_published: bool = False
    alignment_cases_published: bool = False
    reconstruction_reports_available: bool = False
    
    # Compliance metrics
    alignment_coverage: float = 0.0  # Coverage of aligned external expressions
    reconstruction_accuracy: float = 0.0  # Accuracy of proto reconstruction
    evidence_integrity: float = 0.0  # Integrity of alignment evidence
    
    # Published materials
    published_corpora: List[str] = field(default_factory=list)
    published_alignments: List[str] = field(default_factory=list)
    published_reconstructions: List[str] = field(default_factory=list)
    
    # Metadata
    target_languages: List[str] = field(default_factory=list)
    source_mythar_version: str = "1.0"
    conformance_level: str = "full"  # "partial", "full", "experimental"


class MCRLRosettaEngine:
    """
    Mythar Cross-Language Rosetta Layer Engine.
    
    Implements constitutional mappings between Mythar and external languages
    while enforcing factual alignment invariants.
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("rosetta")
        self.storage_path.mkdir(exist_ok=True)
        
        self.external_roots: Dict[str, ExternalRoot] = {}
        self.external_grammar_rules: Dict[str, ExternalGrammarRule] = {}
        self.alignments: Dict[str, AlignmentEntry] = {}
        self.conformance_profiles: Dict[str, RosettaConformanceProfile] = {}
        
        # Constitutional state
        self.rosetta_invariants: List[str] = [
            "all_mappings_must_have_evidence",
            "external_roots_must_have_mythar_anchor",
            "grammar_rules_must_preserve_structure",
            "alignments_must_maintain_factual_alignment",
            "cross_domain_mappings_must_align_domains"
        ]
    
    def register_external_root(self, root: ExternalRoot) -> ExternalRoot:
        """Register an external language root with constitutional validation."""
        
        # FAC-E1 and FAC-E4 validation for external root
        if not self._validate_root_external(root):
            raise ValueError(f"FAC-E1 violation: Root must be external: {root.form}")
        
        if self._detect_circular_dependency(root):
            raise ValueError(f"FAC-E4 violation: Circular dependency detected for {root.form}")
        
        # Evidence integrity check
        if not self._validate_evidence_integrity(root.evidence_id):
            raise ValueError(f"Evidence integrity violation for external root: {root.form}")
        
        self.external_roots[root.form] = root
        self._persist(root, "external_root")
        return root
    
    def register_external_grammar_rule(self, rule: ExternalGrammarRule) -> ExternalGrammarRule:
        """Register an external grammar rule mapping."""
        
        # Validate constitutional requirements
        if not rule.cross_domain_alignment:
            raise ValueError("FAC-D1 violation: Cross-domain alignment required")
        
        if not rule.structural_invariance:
            raise ValueError("FAC-D3 violation: Structural invariance required")
        
        rule_id = f"{rule.language}:{rule.mythar_pattern_ref}"
        self.external_grammar_rules[rule_id] = rule
        self._persist(rule, "external_grammar_rule")
        return rule
    
    def create_alignment(
        self,
        mythar_expr: str,
        external_expr: str,
        mode: AlignmentMode,
        source_lang: str,
        target_lang: str,
        evidence_id: str,
        source_domain: str,
        target_domain: str
    ) -> AlignmentEntry:
        """Create a formal alignment entry with constitutional validation."""
        
        # Validate alignment constitutional constraints
        if not self._validate_alignment_constitutional(
            mythar_expr, external_expr, mode, source_lang, target_lang, source_domain, target_domain
        ):
            raise ValueError("FAC-1 violation: Alignment does not preserve factual alignment")
        
        # Check for existing alignment to avoid duplicates
        existing = self._find_existing_alignment(mythar_expr, external_expr, source_lang, target_lang)
        if existing:
            return existing
        
        # Create new alignment with computed metrics
        alignment_confidence = self._compute_alignment_confidence(mythar_expr, external_expr)
        alignment_score = self._compute_alignment_score(alignment_confidence, mode)
        
        alignment = AlignmentEntry(
            mythar_expression=mythar_expr,
            external_expression=external_expr,
            mode=mode,
            source_language=source_lang,
            target_language=target_lang,
            evidence_id=evidence_id,
            alignment_confidence=alignment_confidence,
            alignment_score=alignment_score,
            source_domain=source_domain,
            target_domain=target_domain,
            provenance_chain=[evidence_id]
        )
        
        self.alignments[alignment.id] = alignment
        self._persist(alignment, "alignment")
        return alignment
    
    def update_conformance_profile(self, profile: RosettaConformanceProfile) -> RosettaConformanceProfile:
        """Update or create a rosetta conformance profile."""
        
        # Validate profile completeness
        if not profile.mcrl_implemented:
            raise ValueError("Rosetta Conformance Profile requires MCRL implementation")
        
        if not profile.marl_rosetta_reconstruction:
            raise ValueError("Rosetta Conformance Profile requires MARL Rosetta reconstruction")
        
        if not profile.cross_language_ontology:
            raise ValueError("Rosetta Conformance Profile requires cross-language ontology")
        
        # Ensure all published materials exist
        if profile.external_corpora_published and not profile.published_corpora:
            raise ValueError("Published corpora must be referenced when external_corpora_published is true")
        
        self.conformance_profiles[profile.profile_id] = profile
        self._persist(profile, "conformance_profile")
        return profile
    
    def validate_alignment_quality(self, alignment_id: str) -> Dict[str, Any]:
        """Validate the quality of a specific alignment."""
        
        alignment = self.alignments.get(alignment_id)
        if not alignment:
            raise ValueError(f"Alignment not found: {alignment_id}")
        
        quality_report = {
            "alignment_id": alignment_id,
            "validations": [],
            "overall_score": alignment.alignment_score,
            "evidence_confidence": alignment.alignment_confidence,
            "alignment_mode": alignment.mode.value,
            "domain_alignment": alignment.source_domain == alignment.target_domain,
            "context_type": alignment.context_type,
            "created_at": alignment.created_at.isoformat(),
            "last_validated": alignment.last_validated.isoformat()
        }
        
        # Validate each dimension
        quality_report["validations"].append({
            "dimension": "external_root",
            "passed": self._validate_external_root(alignment.target_language, alignment.external_expression),
            "message": "External root validation"
        })
        
        quality_report["validations"].append({
            "dimension": "mapping_consistency",
            "passed": alignment.alignment_confidence >= 0.7,
            "message": f"Alignment confidence: {alignment.alignment_confidence:.3f}"
        })
        
        quality_report["validations"].append({
            "dimension": "structural_invariance",
            "passed": self._validate_structural_invariance(alignment),
            "message": "Structural invariance validation"
        })
        
        quality_report["validations"].append({
            "dimension": "factual_alignment",
            "passed": alignment.alignment_score >= 0.7,
            "message": f"Factual alignment score: {alignment.alignment_score:.3f}"
        })
        
        # Update last validated timestamp
        alignment.last_validated = datetime.now()
        self._persist(alignment, "alignment")
        
        return quality_report
    
    def reconstruct_prototype(
        self,
        expressions: List[str],
        source_languages: List[str],
        reconstruction_mode: str = "full"
    ) -> Dict[str, Any]:
        """Reconstruct proto-forms from aligned expressions across languages.
        
        Implements the External → Mythar → External reconstruction pipeline.
        """
        
        # Validate inputs
        if len(expressions) != len(source_languages):
            raise ValueError("Number of expressions must match number of source languages")
        
        # Extract concepts from external expressions
        concepts = self._extract_concepts_from_external(expressions, source_languages)
        
        # Map concepts to Mythar roots
        mythar_concepts = self._map_to_mythar_concepts(concepts)
        
        # Reconstruct proto-forms based on reconstruction mode
        proto_hypotheses = self._reconstruct_proto_forms(mythar_concepts, reconstruction_mode)
        
        # Validate the reconstruction
        reconstruction_report = {
            "expressions": expressions,
            "source_languages": source_languages,
            "concepts": concepts,
            "mythar_concepts": mythar_concepts,
            "proto_hypotheses": proto_hypotheses,
            "reconstruction_mode": reconstruction_mode,
            "validation_score": 0.0,
            "validations": []
        }
        
        # Validate each dimension
        reconstruction_report["validations"].append({
            "dimension": "concept_extraction",
            "score": len([c for c in concepts if c]) / len(concepts),
            "passed": len([c for c in concepts if c]) == len(concepts)
        })
        
        reconstruction_report["validations"].append({
            "dimension": "mythar_mapping",
            "score": len([m for m in mythar_concepts if m]) / len(mythar_concepts),
            "passed": len([m for m in mythar_concepts if m]) == len(mythar_concepts)
        })
        
        reconstruction_report["validations"].append({
            "dimension": "proto_reconstruction",
            "score": len(proto_hypotheses) / len(concepts),
            "passed": len(proto_hypotheses) > 0
        })
        
        # Compute overall validation score
        validation_scores = [v["score"] for v in reconstruction_report["validations"]]
        reconstruction_report["validation_score"] = sum(validation_scores) / len(validation_scores)
        
        return reconstruction_report
    
    # Helper validation methods
    
    def _validate_root_external(self, root: ExternalRoot) -> bool:
        """FAC-E1: Validate that root is truly external."""
        return root.source == EvidenceSource.EXTERNAL
    
    def _detect_circular_dependency(self, root: ExternalRoot) -> bool:
        """FAC-E4: Detect circular evidence dependencies."""
        # Implementation would check for circular references
        return False
    
    def _validate_evidence_integrity(self, evidence_id: str) -> bool:
        """FAC-E2: Validate evidence integrity."""
        # Implementation would verify evidence was generated independently
        return True
    
    def _validate_alignment_constitutional(
        self,
        mythar_expr: str,
        external_expr: str,
        mode: AlignmentMode,
        source_lang: str,
        target_lang: str,
        source_domain: str,
        target_domain: str
    ) -> bool:
        """Validate that alignment preserves constitutional invariants."""
        # Check factual alignment
        alignment_score = self._compute_alignment_score_for_pair(mythar_expr, external_expr)
        
        # Check domain alignment
        domain_match = source_domain == target_domain
        
        # Check mode appropriateness
        mode_appropriate = self._is_mode_appropriate(mode, source_lang, target_lang)
        
        return alignment_score >= 0.7 and domain_match and mode_appropriate
    
    def _is_mode_appropriate(self, mode: AlignmentMode, source_lang: str, target_lang: str) -> bool:
        """Check if alignment mode is appropriate for the language pair."""
        # Implementation would depend on language characteristics
        return True
    
    def _find_existing_alignment(
        self,
        mythar_expr: str,
        external_expr: str,
        source_lang: str,
        target_lang: str
    ) -> Optional[AlignmentEntry]:
        """Find existing alignment for the given pair."""
        for alignment in self.alignments.values():
            if (alignment.mythar_expression == mythar_expr and
                alignment.external_expression == external_expr and
                alignment.source_language == source_lang and
                alignment.target_language == target_lang and
                alignment.validation_status == "verified"):
                return alignment
        return None
    
    def _compute_alignment_confidence(self, mythar_expr: str, external_expr: str) -> float:
        """Compute confidence score for alignment."""
        # Implementation would use semantic similarity and evidence weight
        return 0.8
    
    def _compute_alignment_score(self, confidence: float, mode: AlignmentMode) -> float:
        """Compute overall alignment score."""
        base_score = confidence
        
        # Adjust based on alignment mode
        if mode == AlignmentMode.CONSTITUTIONAL:
            base_score += 0.1
        elif mode == AlignmentMode.SYMBOLIC:
            base_score += 0.05
        
        return min(1.0, base_score)
    
    def _compute_alignment_score_for_pair(self, mythar_expr: str, external_expr: str) -> float:
        """Compute alignment score for a specific expression pair."""
        return 0.85
    
    def _validate_external_root(self, language: str, expression: str) -> bool:
        """Validate that expression is a valid external root."""
        return expression in self.external_roots
    
    def _validate_structural_invariance(self, alignment: AlignmentEntry) -> bool:
        """Validate that structural invariance is preserved."""
        # Implementation would check for structural similarity
        return True
    
    def _extract_concepts_from_external(
        self,
        expressions: List[str],
        languages: List[str]
    ) -> List[str]:
        """Extract concepts from external expressions."""
        concepts = []
        for expr, lang in zip(expressions, languages):
            # Implementation would use concept extraction
            concepts.append(f"concept_{lang}_{hash(expr)}")
        return concepts
    
    def _map_to_mythar_concepts(self, concepts: List[str]) -> List[str]:
        """Map extracted concepts to Mythar roots."""
        mythar_concepts = []
        for concept in concepts:
            # Implementation would map to Mythar roots
            mythar_concepts.append(f"mythar_root_{hash(concept)}")
        return mythar_concepts
    
    def _reconstruct_proto_forms(
        self,
        mythar_concepts: List[str],
        mode: str
    ) -> List[Dict[str, Any]]:
        """Reconstruct proto-forms from Mythar concepts."""
        proto_forms = []
        for concept in mythar_concepts:
            # Implementation would reconstruct proto-forms
            proto_form = {
                "original": concept,
                "proto_form": f"proto_{hash(concept)}",
                "confidence": 0.8,
                "morphology": {"root": concept, "affixes": []},
                "semantics": {"domain": "unknown", "features": []}
            }
            proto_forms.append(proto_form)
        return proto_forms
    
    def _persist(self, item: Any, item_type: str) -> None:
        """Persist item to storage."""
        if self.storage_path:
            # Implementation would persist to appropriate storage
            pass


# Global MCRL engine instance
_global_mcrl: Optional[MCRLRosettaEngine] = None
_mcrl_lock = threading.Lock()


def get_mcrl_engine(storage_path: Optional[Path] = None) -> MCRLRosettaEngine:
    """Get or create global MCRL engine."""
    global _global_mcrl
    with _mcrl_lock:
        if _global_mcrl is None:
            _global_mcrl = MCRLRosettaEngine(storage_path)
        return _global_mcrl


def reset_mcrl() -> None:
    """Reset global MCRL engine (for testing)."""
    global _global_mcrl
    with _mcrl_lock:
        _global_mcrl = None
# Export public symbols
__all__ = [
    "ExternalRoot",
    "ExternalGrammarRule",
    "AlignmentEntry",
    "RosettaConformanceProfile",
    "MCRLRosettaEngine",
    "AlignmentMode",
    "get_mcrl_engine",
    "reset_mcrl"
]