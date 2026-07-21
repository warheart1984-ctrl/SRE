"""FAE Public API - Main entry point for Factual Alignment Engine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TypeVar
from pathlib import Path

from fae.evidence.registry import (
    EvidenceRegistry,
    Evidence,
    ProvenanceMetadata,
    EvidenceSource,
    EvidenceStatus,
    get_registry,
    reset_registry
)
from fae.cycle.fra_cycle import (
    FRACycle,
    FRACycleStage,
    CycleContext,
    StageResult,
    FRACycleError,
    FACInvariantViolation
)
from fae.metrics.validation import (
    ValidationMetricsEngine,
    CycleValidationReport,
    ValidationResult
)
from fae.drift.detection import (
    DriftDetectionEngine,
    DriftEvent,
    DriftType,
    DriftSeverity,
    DriftThresholds
)
from fae.governance.hooks import (
    FACGovernanceHooks,
    GovernedFRACycle,
    create_governed_fra_cycle,
    FACPolicy,
    ComponentCertification,
    ComponentStatus
)
from fae.state.csr import (
    ConstitutionalStateRecord,
    CycleLog,
    get_csr,
    reset_csr,
    AlignmentCheck
)


T = TypeVar('T')


@dataclass
class FAEConfig:
    """Configuration for FAE module."""
    storage_path: Optional[Path] = None
    drift_thresholds: Optional[DriftThresholds] = None
    enable_governance: bool = True
    auto_validate: bool = True
    auto_drift_check: bool = True
    max_cycles: int = 100


class FactualAlignmentEngine:
    """
    Main entry point for the Factual Alignment Engine (FAE).
    
    Enforces the Factual Alignment Contract (FAC) across all recursive systems
    in Sovereign X OS. Ensures every FRA cycle is evidence-anchored, validated,
    logged, and governed.
    
    Usage:
        fae = FactualAlignmentEngine()
        
        # Register evidence
        fae.register_evidence(
            content={"temperature": 22.5},
            content_type="sensor_reading",
            provenance=ProvenanceMetadata(...),
            cycle_id="cycle_1",
            stage="observe"
        )
        
        # Run FRA cycle
        cycle = fae.create_cycle(
            observers={...},
            extractors={...},
            model_builder=...,
            reasoner=...,
            actors={...},
            measurers={...},
            comparator=...,
            updater=...,
            should_continue=...,
            initial_model={}
        )
        context = cycle.run()
        
        # Validate
        report = fae.validate_cycle(context.cycle_id)
        
        # Check drift
        drift_events = fae.check_drift(context.cycle_id)
    """
    
    def __init__(self, config: Optional[FAEConfig] = None):
        self.config = config or FAEConfig()
        
        # Initialize core components
        self.registry = get_registry(self.config.storage_path)
        self.csr = get_csr(self.config.storage_path)
        self.validation_engine = ValidationMetricsEngine(self.registry, self.csr)
        self.drift_engine = DriftDetectionEngine(
            self.registry,
            self.csr,
            self.config.drift_thresholds
        )
        
        # Governance hooks
        self.governance_hooks: Optional[FACGovernanceHooks] = None
        if self.config.enable_governance:
            self.governance_hooks = FACGovernanceHooks(
                component_id="fae_core"
            )
        
        # Active cycles
        self._active_cycles: Dict[str, FRACycle] = {}
        self._cycle_counter = 0
    
    # ========== Evidence Management ==========
    
    def register_evidence(
        self,
        content: Any,
        content_type: str,
        provenance: ProvenanceMetadata,
        cycle_id: str,
        stage: str,
        evidence_id: Optional[str] = None
    ) -> Evidence:
        """Register evidence in the registry (FAC-E1 through FAC-E4)."""
        return self.registry.register(
            content=content,
            content_type=content_type,
            provenance=provenance,
            cycle_id=cycle_id,
            stage=stage,
            evidence_id=evidence_id
        )
    
    def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        """Get evidence by ID."""
        return self.registry.get(evidence_id)
    
    def get_cycle_evidence(self, cycle_id: str) -> List[Evidence]:
        """Get all evidence for a cycle."""
        return self.registry.get_by_cycle(cycle_id)
    
    def get_stage_evidence(self, cycle_id: str, stage: str) -> List[Evidence]:
        """Get evidence for a specific stage in a cycle."""
        return self.registry.get_by_cycle_and_stage(cycle_id, stage)
    
    def verify_evidence_integrity(self, cycle_id: str) -> Dict[str, bool]:
        """Verify integrity of all evidence in a cycle."""
        return self.registry.verify_all(cycle_id)
    
    def get_unverified_evidence(self, cycle_id: str) -> List[Evidence]:
        """Get unverified evidence (FAC-E2 check)."""
        return self.registry.get_unverified(cycle_id)
    
    # ========== FRA Cycle Management ==========
    
    def create_cycle(
        self,
        observers: Dict[str, Callable[[], Any]],
        extractors: Dict[str, Callable[[Any], List[Dict[str, Any]]]],
        model_builder: Callable[[Any, List[Dict[str, Any]]], Any],
        reasoner: Callable[[Any], Dict[str, Any]],
        actors: Dict[str, Callable[[Dict[str, Any]], Any]],
        measurers: Dict[str, Callable[[], Any]],
        comparator: Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]],
        updater: Callable[[Any, Dict[str, Any]], Any],
        should_continue: Callable[[CycleContext], bool],
        initial_model: Any,
        cycle_id: Optional[str] = None,
        governed: bool = True
    ) -> FRACycle:
        """Create a new FRA cycle."""
        self._cycle_counter += 1
        cid = cycle_id or f"fra_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self._cycle_counter:04d}"
        
        if governed and self.config.enable_governance:
            cycle = create_governed_fra_cycle(
                component_id=cid,
                observers=observers,
                extractors=extractors,
                model_builder=model_builder,
                reasoner=reasoner,
                actors=actors,
                measurers=measurers,
                comparator=comparator,
                updater=updater,
                should_continue=should_continue,
                initial_model=initial_model,
                kernel=self.governance_hooks.kernel if self.governance_hooks else None
            )
        else:
            cycle = FRACycle(
                observers=observers,
                extractors=extractors,
                model_builder=model_builder,
                reasoner=reasoner,
                actors=actors,
                measurers=measurers,
                comparator=comparator,
                updater=updater,
                should_continue=should_continue,
                initial_model=initial_model,
                cycle_id=cid
            )
        
        self._active_cycles[cid] = cycle
        return cycle
    
    def run_cycle(self, cycle: FRACycle) -> CycleContext:
        """Execute a single FRA cycle with validation and drift checking."""
        cycle_id = cycle.cycle_id
        
        # Start CSR log
        self.csr.start_cycle(cycle_id, cycle.initial_model)
        
        try:
            # Run cycle
            context = cycle.run()
            
            # Auto-validate if enabled
            if self.config.auto_validate:
                self.validate_cycle(cycle_id)
            
            # Auto drift check if enabled
            if self.config.auto_drift_check:
                self.check_drift(cycle_id)
            
            return context
            
        except (FRACycleError, FACInvariantViolation):
            # Log failure
            self.csr.end_cycle(cycle_id, success=False, final_model=cycle.model_state)
            raise
    
    def run_recursive(self, cycle: FRACycle, max_cycles: Optional[int] = None) -> List[CycleContext]:
        """Run FRA cycles recursively."""
        max_c = max_cycles or self.config.max_cycles
        contexts = []
        
        for _ in range(max_c):
            context = self.run_cycle(cycle)
            contexts.append(context)
            
            # Check if should continue
            if not context.metadata.get("recurse", True):
                break
        
        return contexts
    
    # ========== Validation ==========
    
    def validate_cycle(self, cycle_id: str) -> CycleValidationReport:
        """Run all FAC-V1 through FAC-V5 validation tests."""
        return self.validation_engine.validate_cycle(cycle_id)
    
    def validate_all_cycles(self) -> Dict[str, CycleValidationReport]:
        """Validate all completed cycles."""
        return self.validation_engine.validate_all_cycles()
    
    def check_alignment(self, cycle_id: str) -> AlignmentCheck:
        """Check FAC-1 factual alignment invariant."""
        return self.csr.validate_factual_alignment(cycle_id)
    
    # ========== Drift Detection ==========
    
    def check_drift(self, cycle_id: str) -> List[DriftEvent]:
        """Run all FAC-D drift checks."""
        return self.drift_engine.check_cycle(cycle_id)
    
    def get_drift_summary(self, cycle_id: Optional[str] = None) -> Dict[str, Any]:
        """Get drift summary."""
        return self.drift_engine.get_drift_summary(cycle_id)
    
    def requires_constitutional_halt(self, cycle_id: str) -> bool:
        """Check if cycle requires constitutional halt."""
        summary = self.get_drift_summary(cycle_id)
        return summary.get("critical_count", 0) > 0
    
    # ========== Governance ==========
    
    def get_governance_hooks(self) -> Optional[FACGovernanceHooks]:
        """Get governance hooks for integration."""
        return self.governance_hooks
    
    def register_policy(self, policy: FACPolicy) -> None:
        """Register governance policy."""
        if self.governance_hooks and self.governance_hooks.kernel:
            self.governance_hooks.kernel.register_policy(policy)
    
    def request_certification(self, component_id: str, cycles: List[str]) -> ComponentCertification:
        """Request Factual Alignment Certificate."""
        if self.governance_hooks:
            return self.governance_hooks.request_certification(cycles)
        raise RuntimeError("Governance not enabled")
    
    # ========== Audit & Inspection ==========
    
    def get_cycle_log(self, cycle_id: str) -> Optional[CycleLog]:
        """Get complete cycle log."""
        return self.csr.get_cycle(cycle_id)
    
    def get_validation_report(self, cycle_id: str) -> Optional[CycleValidationReport]:
        """Get validation report for cycle."""
        return self.validation_engine.validate_cycle(cycle_id)
    
    def export_audit_trail(self, cycle_id: Optional[str] = None) -> Dict[str, Any]:
        """Export complete audit trail."""
        return self.csr.export_audit_trail(cycle_id)
    
    def get_active_cycles(self) -> Dict[str, FRACycle]:
        """Get currently active cycles."""
        return dict(self._active_cycles)
    
    def get_cycle_count(self) -> int:
        """Get total cycle count."""
        return self._cycle_counter
    
    # ========== Factory Methods ==========
    
    @staticmethod
    def create_provenance(
        source: EvidenceSource,
        source_id: str,
        acquisition_method: str,
        confidence: float = 1.0,
        validation_status: EvidenceStatus = EvidenceStatus.UNVERIFIED,
        validator_id: Optional[str] = None,
        dependencies: Optional[List[str]] = None
    ) -> ProvenanceMetadata:
        """Create provenance metadata with content hash."""
        # Create placeholder - actual hash computed at registration
        content_hash = "pending"
        
        return ProvenanceMetadata(
            source=source,
            source_id=source_id,
            timestamp=datetime.now(),
            acquisition_method=acquisition_method,
            confidence=confidence,
            validation_status=validation_status,
            validator_id=validator_id,
            validation_timestamp=datetime.now() if validation_status == EvidenceStatus.VERIFIED else None,
            content_hash=content_hash,
            dependencies=frozenset(dependencies or [])
        )
    
    @staticmethod
    def create_external_sensor_provenance(
        sensor_id: str,
        method: str,
        confidence: float = 1.0
    ) -> ProvenanceMetadata:
        """Create provenance for external sensor (FAC-E1 compliant)."""
        return FactualAlignmentEngine.create_provenance(
            source=EvidenceSource.EXTERNAL_SENSOR,
            source_id=sensor_id,
            acquisition_method=method,
            confidence=confidence
        )
    
    @staticmethod
    def create_audit_provenance(
        auditor_id: str,
        method: str,
        confidence: float = 1.0
    ) -> ProvenanceMetadata:
        """Create provenance for third-party audit (FAC-E1/E2 compliant)."""
        return FactualAlignmentEngine.create_provenance(
            source=EvidenceSource.THIRD_PARTY_AUDIT,
            source_id=auditor_id,
            acquisition_method=method,
            confidence=confidence,
            validation_status=EvidenceStatus.VERIFIED,
            validator_id=auditor_id
        )


# Convenience functions for quick usage

def create_fae(config: Optional[FAEConfig] = None) -> FactualAlignmentEngine:
    """Create FAE instance."""
    return FactualAlignmentEngine(config)


def quick_cycle(
    observers: Dict[str, Callable[[], Any]],
    extractors: Dict[str, Callable[[Any], List[Dict[str, Any]]]],
    model_builder: Callable[[Any, List[Dict[str, Any]]], Any],
    reasoner: Callable[[Any], Dict[str, Any]],
    actors: Dict[str, Callable[[Dict[str, Any]], Any]],
    measurers: Dict[str, Callable[[], Any]],
    comparator: Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]],
    updater: Callable[[Any, Dict[str, Any]], Any],
    should_continue: Callable[[CycleContext], bool],
    initial_model: Any,
    config: Optional[FAEConfig] = None
) -> CycleContext:
    """Run a single FRA cycle with default FAE configuration."""
    fae = create_fae(config)
    cycle = fae.create_cycle(
        observers=observers,
        extractors=extractors,
        model_builder=model_builder,
        reasoner=reasoner,
        actors=actors,
        measurers=measurers,
        comparator=comparator,
        updater=updater,
        should_continue=should_continue,
        initial_model=initial_model
    )
    return fae.run_cycle(cycle)


# Reset functions for testing
def reset_fae() -> None:
    """Reset all global FAE state (for testing)."""
    reset_registry()
    reset_csr()


# Export all public symbols
__all__ = [
    # Main class
    "FactualAlignmentEngine",
    "FAEConfig",
    
    # Evidence
    "Evidence",
    "ProvenanceMetadata",
    "EvidenceSource",
    "EvidenceStatus",
    "EvidenceRegistry",
    
    # FRA Cycle
    "FRACycle",
    "FRACycleStage",
    "CycleContext",
    "StageResult",
    "FRACycleError",
    "FACInvariantViolation",
    
    # Validation
    "ValidationMetricsEngine",
    "CycleValidationReport",
    "ValidationResult",
    
    # Drift
    "DriftDetectionEngine",
    "DriftEvent",
    "DriftType",
    "DriftSeverity",
    "DriftThresholds",
    
    # Governance
    "FACGovernanceHooks",
    "GovernedFRACycle",
    "FACPolicy",
    "ComponentCertification",
    "ComponentStatus",
    
    # State
    "ConstitutionalStateRecord",
    "CycleLog",
    "AlignmentCheck",
    
    # Convenience
    "create_fae",
    "quick_cycle",
    "reset_fae",
]