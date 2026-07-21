"""FAE constitutional substrate bridge for SRE.

SRE keeps domain types (LinguisticEvidence, CEL, ChronologicalReconstruction).
FAE supplies the generic FAC/FRA substrate (EvidenceRegistry, FRACycle, drift,
validation, CSR, MCRL Rosetta). This package is the explicit import boundary.

Evidence: ``import fae`` and ``from sre.substrate import ...`` succeed after
``pip install -e .``; linguistic EvidenceRegistry APIs are unchanged.
"""

from __future__ import annotations

from fae import (
    AlignmentCheck,
    ConstitutionalStateRecord,
    CycleContext,
    CycleLog,
    CycleValidationReport,
    DriftDetectionEngine,
    DriftEvent,
    DriftSeverity,
    DriftThresholds,
    DriftType,
    Evidence,
    EvidenceSource,
    EvidenceStatus,
    FACInvariantViolation,
    FAEConfig,
    FRACycle,
    FRACycleError,
    FRACycleStage,
    FactualAlignmentEngine,
    ProvenanceMetadata,
    StageResult,
    ValidationMetricsEngine,
    ValidationResult,
    create_fae,
    quick_cycle,
    reset_fae,
)
from fae.api import (
    ComponentCertification,
    ComponentStatus,
    EvidenceRegistry as FAEEvidenceRegistry,
    FACGovernanceHooks,
    FACPolicy,
    GovernedFRACycle,
)
from fae.evidence.registry import get_registry as get_fae_registry
from fae.evidence.registry import reset_registry as reset_fae_registry
from fae.mcr.rosetta import (
    AlignmentEntry,
    AlignmentMode,
    ExternalGrammarRule,
    ExternalRoot,
    MCRLRosettaEngine as FAEMCRLRosettaEngine,
    RosettaConformanceProfile,
    get_mcrl_engine,
    reset_mcrl,
)

from .bridge import mirror_linguistic_evidence_to_fae
from .fra_composition import ComposedReconstructionResult, FRAComposedReconstruction, RecursiveCompositionResult
from .fra_stage_runner import (
    FAE_TO_SRE_STAGE_GROUPS,
    SRE_TO_FAE_STAGE_MAP,
    SREFRAPipelineRunner,
    SREGovernedFRACycle,
    build_sre_governed_fra_cycle,
)
from .mcrl_composition import ComposedRosettaEngine

__all__ = [
    "AlignmentCheck",
    "AlignmentEntry",
    "AlignmentMode",
    "ComponentCertification",
    "ComponentStatus",
    "ConstitutionalStateRecord",
    "CycleContext",
    "CycleLog",
    "CycleValidationReport",
    "DriftDetectionEngine",
    "DriftEvent",
    "DriftSeverity",
    "DriftThresholds",
    "DriftType",
    "Evidence",
    "EvidenceSource",
    "EvidenceStatus",
    "ExternalGrammarRule",
    "ExternalRoot",
    "FACGovernanceHooks",
    "FACInvariantViolation",
    "FACPolicy",
    "FAEConfig",
    "FAEEvidenceRegistry",
    "FAEMCRLRosettaEngine",
    "FRACycle",
    "FRACycleError",
    "FRACycleStage",
    "FactualAlignmentEngine",
    "GovernedFRACycle",
    "ProvenanceMetadata",
    "RosettaConformanceProfile",
    "StageResult",
    "ValidationMetricsEngine",
    "ValidationResult",
    "create_fae",
    "get_fae_registry",
    "get_mcrl_engine",
    "mirror_linguistic_evidence_to_fae",
    "quick_cycle",
    "reset_fae",
    "reset_fae_registry",
    "reset_mcrl",
    "ComposedReconstructionResult",
    "ComposedRosettaEngine",
    "FAE_TO_SRE_STAGE_GROUPS",
    "FRAComposedReconstruction",
    "RecursiveCompositionResult",
    "SRE_TO_FAE_STAGE_MAP",
    "SREFRAPipelineRunner",
    "SREGovernedFRACycle",
    "build_sre_governed_fra_cycle",
]
