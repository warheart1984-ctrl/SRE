"""Governance Kernel Integration Hooks - FAC integration with CIEMS Governance Kernel."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
import threading
import uuid

from fae.evidence.registry import EvidenceRegistry, get_registry
from fae.state.csr import ConstitutionalStateRecord, get_csr
from fae.cycle.fra_cycle import FRACycle, CycleContext, FRACycleStage
from fae.metrics.validation import ValidationMetricsEngine, CycleValidationReport, get_validation_engine
from fae.drift.detection import DriftDetectionEngine, DriftEvent, DriftSeverity, get_drift_engine
from fae.drift.detection import ConstitutionalViolationDetector


class GovernanceEventType(Enum):
    """Types of events reported to Governance Kernel."""
    CYCLE_STARTED = "cycle_started"
    CYCLE_COMPLETED = "cycle_completed"
    CYCLE_FAILED = "cycle_failed"
    VALIDATION_REPORT = "validation_report"
    DRIFT_DETECTED = "drift_detected"
    VIOLATION_DETECTED = "violation_detected"
    CERTIFICATION_REQUESTED = "certification_requested"
    CERTIFICATION_GRANTED = "certification_granted"
    CERTIFICATION_DENIED = "certification_denied"
    COMPONENT_HALTED = "component_halted"
    COMPONENT_ROLLED_BACK = "component_rolled_back"
    CONSTITUTIONAL_REVIEW_TRIGGERED = "constitutional_review_triggered"


class ComponentStatus(Enum):
    """Certification status of FRA-compliant components."""
    UNCERTIFIED = "uncertified"
    PENDING = "pending"
    CERTIFIED = "certified"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


@dataclass
class GovernanceEvent:
    """Event published to Governance Kernel."""
    event_id: str
    event_type: GovernanceEventType
    timestamp: datetime
    component_id: str
    cycle_id: Optional[str]
    payload: Dict[str, Any]
    severity: str = "info"  # info, warning, critical


@dataclass
class FACPolicy:
    """Governance Kernel policy for FAC compliance."""
    policy_id: str
    name: str
    description: str
    # Thresholds
    min_factual_alignment: float = 0.7
    max_uncertainty: float = 0.3
    min_calibration: float = 0.7
    min_explanatory_power: float = 0.5
    min_error_correction: float = 0.5
    # Actions on violation
    halt_on_critical: bool = True
    rollback_on_degradation: bool = True
    require_certification_for_high_impact: bool = True


@dataclass
class ComponentCertification:
    """Factual Alignment Certificate for a component."""
    component_id: str
    certification_id: str
    issued_at: datetime
    expires_at: Optional[datetime]
    status: ComponentStatus
    cycles_evaluated: int
    min_alignment_score: float
    policy_id: str
    conditions: List[str] = field(default_factory=list)


class GovernanceKernelInterface(ABC):
    """Abstract interface for Governance Kernel integration."""
    
    @abstractmethod
    def publish_event(self, event: GovernanceEvent) -> None:
        """Publish event to Governance Kernel."""
        pass
    
    @abstractmethod
    def evaluate_policy(self, component_id: str, cycle_id: str, report: CycleValidationReport) -> Dict[str, Any]:
        """Evaluate FAC policies against validation report."""
        pass
    
    @abstractmethod
    def request_certification(self, component_id: str, cycles: List[str]) -> ComponentCertification:
        """Request certification for component."""
        pass
    
    @abstractmethod
    def halt_component(self, component_id: str, reason: str) -> bool:
        """Halt component execution."""
        pass
    
    @abstractmethod
    def rollback_component(self, component_id: str, cycle_id: str) -> bool:
        """Rollback component to previous cycle."""
        pass
    
    @abstractmethod
    def trigger_constitutional_review(self, component_id: str, violations: List[Dict]) -> str:
        """Trigger constitutional review process."""
        pass


class MockGovernanceKernel(GovernanceKernelInterface):
    """Mock implementation for testing/development."""
    
    def __init__(self):
        self.events: List[GovernanceEvent] = []
        self.certifications: Dict[str, ComponentCertification] = {}
        self.halted_components: Set[str] = set()
        self.policies: Dict[str, FACPolicy] = {}
        self._lock = threading.Lock()
    
    def publish_event(self, event: GovernanceEvent) -> None:
        with self._lock:
            self.events.append(event)
            print(f"[GOVERNANCE] {event.event_type.value} | {event.component_id} | {event.severity} | {event.payload}")
    
    def evaluate_policy(self, component_id: str, cycle_id: str, report: CycleValidationReport) -> Dict[str, Any]:
        with self._lock:
            policy = self.policies.get(component_id)
            if not policy:
                return {"passed": True, "message": "No policy configured"}
            
            violations = []
            
            # Check overall alignment
            if report.overall_score < policy.min_factual_alignment:
                violations.append(f"Overall score {report.overall_score:.3f} below minimum {policy.min_factual_alignment}")
            
            # Check individual tests
            for result in report.results:
                if result.test_name == "FAC-V1: Accuracy Test" and result.score < policy.min_factual_alignment:
                    violations.append(f"Accuracy {result.score:.3f} below minimum {policy.min_factual_alignment}")
                elif result.test_name == "FAC-V2: Uncertainty Test" and (1 - result.score) > policy.max_uncertainty:
                    violations.append(f"Uncertainty {1-result.score:.3f} above maximum {policy.max_uncertainty}")
                elif result.test_name == "FAC-V3: Calibration Test" and result.score < policy.min_calibration:
                    violations.append(f"Calibration {result.score:.3f} below minimum {policy.min_calibration}")
                elif result.test_name == "FAC-V4: Explanatory Power Test" and result.score < policy.min_explanatory_power:
                    violations.append(f"Explanatory power {result.score:.3f} below minimum {policy.min_explanatory_power}")
                elif result.test_name == "FAC-V5: Error Correction Test" and result.score < policy.min_error_correction:
                    violations.append(f"Error correction {result.score:.3f} below minimum {policy.min_error_correction}")
            
            return {
                "passed": len(violations) == 0,
                "violations": violations,
                "policy_id": policy.policy_id
            }
    
    def request_certification(self, component_id: str, cycles: List[str]) -> ComponentCertification:
        with self._lock:
            cert = ComponentCertification(
                component_id=component_id,
                certification_id=str(uuid.uuid4()),
                issued_at=datetime.now(),
                expires_at=None,
                status=ComponentStatus.CERTIFIED,
                cycles_evaluated=len(cycles),
                min_alignment_score=0.8,
                policy_id=self.policies.get(component_id, FACPolicy("", "", "")).policy_id
            )
            self.certifications[component_id] = cert
            return cert
    
    def halt_component(self, component_id: str, reason: str) -> bool:
        with self._lock:
            self.halted_components.add(component_id)
            print(f"[GOVERNANCE] HALTED component {component_id}: {reason}")
            return True
    
    def rollback_component(self, component_id: str, cycle_id: str) -> bool:
        with self._lock:
            print(f"[GOVERNANCE] ROLLBACK component {component_id} to cycle {cycle_id}")
            return True
    
    def trigger_constitutional_review(self, component_id: str, violations: List[Dict]) -> str:
        with self._lock:
            review_id = str(uuid.uuid4())
            print(f"[GOVERNANCE] CONSTITUTIONAL REVIEW {review_id} for {component_id}: {violations}")
            return review_id
    
    def register_policy(self, policy: FACPolicy) -> None:
        with self._lock:
            self.policies[policy.policy_id] = policy


# Global governance kernel instance
_global_kernel: Optional[GovernanceKernelInterface] = None
_kernel_lock = threading.Lock()


def get_governance_kernel() -> GovernanceKernelInterface:
    """Get or create global governance kernel."""
    global _global_kernel
    with _kernel_lock:
        if _global_kernel is None:
            _global_kernel = MockGovernanceKernel()
        return _global_kernel


def set_governance_kernel(kernel: GovernanceKernelInterface) -> None:
    """Set custom governance kernel implementation."""
    global _global_kernel
    with _kernel_lock:
        _global_kernel = kernel


class FACGovernanceHooks:
    """
    FAC Governance Kernel Integration Hooks.
    
    Implements FAC → Governance Kernel integration per specification:
    - FAC Telemetry Interface
    - FAC Policy Hooks
    - FAC Certification
    """
    
    def __init__(
        self,
        kernel: Optional[GovernanceKernelInterface] = None,
        component_id: str = "fae_default"
    ):
        self.kernel = kernel or get_governance_kernel()
        self.component_id = component_id
        self.violation_detector = ConstitutionalViolationDetector()
        self._cycle_subscribers: List[Callable[[CycleContext], None]] = []
        self._violation_subscribers: List[Callable[[List[Dict]], None]] = []
    
    # ========== FAC Telemetry Interface ==========
    
    def on_cycle_start(self, cycle_id: str, initial_model: Any) -> None:
        """Called when FRA cycle begins."""
        event = GovernanceEvent(
            event_id=str(uuid.uuid4()),
            event_type=GovernanceEventType.CYCLE_STARTED,
            timestamp=datetime.now(),
            component_id=self.component_id,
            cycle_id=cycle_id,
            payload={"initial_model_hash": hash(str(initial_model))},
            severity="info"
        )
        self.kernel.publish_event(event)
    
    def on_cycle_complete(self, context: CycleContext) -> None:
        """Called when FRA cycle completes successfully."""
        # Run validation
        validation_engine = get_validation_engine()
        report = validation_engine.validate_cycle(context.cycle_id)
        
        # Publish validation report
        event = GovernanceEvent(
            event_id=str(uuid.uuid4()),
            event_type=GovernanceEventType.VALIDATION_REPORT,
            timestamp=datetime.now(),
            component_id=self.component_id,
            cycle_id=context.cycle_id,
            payload={
                "overall_passed": report.overall_passed,
                "overall_score": report.overall_score,
                "results": [
                    {
                        "test": r.test_name,
                        "passed": r.passed,
                        "score": r.score,
                        "message": r.message
                    }
                    for r in report.results
                ]
            },
            severity="info" if report.overall_passed else "warning"
        )
        self.kernel.publish_event(event)
        
        # Evaluate policies
        policy_result = self.kernel.evaluate_policy(self.component_id, context.cycle_id, report)
        
        if not policy_result["passed"]:
            self._handle_policy_violation(context.cycle_id, policy_result)
        
        # Check for drift
        drift_engine = get_drift_engine()
        drift_events = drift_engine.check_cycle(context.cycle_id)
        for drift_event in drift_events:
            self.on_drift_detected(context.cycle_id, drift_event)
        
        # Check for constitutional violations
        violations = self.violation_detector.check_violations(context.cycle_id)
        if violations:
            self.on_violations_detected(context.cycle_id, violations)
        
        # Notify subscribers
        for sub in self._cycle_subscribers:
            try:
                sub(context)
            except Exception:
                pass  # Don't let subscriber errors break governance
        
        # Publish completion event
        event = GovernanceEvent(
            event_id=str(uuid.uuid4()),
            event_type=GovernanceEventType.CYCLE_COMPLETED,
            timestamp=datetime.now(),
            component_id=self.component_id,
            cycle_id=context.cycle_id,
            payload={"validation_passed": report.overall_passed, "policy_passed": policy_result["passed"]},
            severity="info"
        )
        self.kernel.publish_event(event)
    
    def on_cycle_failed(self, cycle_id: str, error: Exception, stage: FRACycleStage) -> None:
        """Called when FRA cycle fails."""
        event = GovernanceEvent(
            event_id=str(uuid.uuid4()),
            event_type=GovernanceEventType.CYCLE_FAILED,
            timestamp=datetime.now(),
            component_id=self.component_id,
            cycle_id=cycle_id,
            payload={"error": str(error), "failed_stage": stage.value},
            severity="critical"
        )
        self.kernel.publish_event(event)
    
    def on_drift_detected(self, cycle_id: str, drift_event: DriftEvent) -> None:
        """Called when drift is detected."""
        event = GovernanceEvent(
            event_id=str(uuid.uuid4()),
            event_type=GovernanceEventType.DRIFT_DETECTED,
            timestamp=datetime.now(),
            component_id=self.component_id,
            cycle_id=cycle_id,
            payload={
                "drift_type": drift_event.drift_type.value,
                "severity": drift_event.severity.value,
                "message": drift_event.message,
                "details": drift_event.details
            },
            severity=drift_event.severity.value
        )
        self.kernel.publish_event(event)
        
        # Critical drift triggers immediate action
        if drift_event.severity == DriftSeverity.CRITICAL:
            self.kernel.halt_component(self.component_id, f"Critical drift: {drift_event.message}")
    
    def on_violations_detected(self, cycle_id: str, violations: List[Dict]) -> None:
        """Called when constitutional violations are detected."""
        for violation in violations:
            event = GovernanceEvent(
                event_id=str(uuid.uuid4()),
                event_type=GovernanceEventType.VIOLATION_DETECTED,
                timestamp=datetime.now(),
                component_id=self.component_id,
                cycle_id=cycle_id,
                payload=violation,
                severity=violation.get("severity", "high")
            )
            self.kernel.publish_event(event)
        
        # Critical violations trigger constitutional review
        critical_violations = [v for v in violations if v.get("severity") == "critical"]
        if critical_violations:
            review_id = self.kernel.trigger_constitutional_review(self.component_id, critical_violations)
            
            event = GovernanceEvent(
                event_id=str(uuid.uuid4()),
                event_type=GovernanceEventType.CONSTITUTIONAL_REVIEW_TRIGGERED,
                timestamp=datetime.now(),
                component_id=self.component_id,
                cycle_id=cycle_id,
                payload={"review_id": review_id, "violations": critical_violations},
                severity="critical"
            )
            self.kernel.publish_event(event)
            
            # Halt component per FAC specification
            self.kernel.halt_component(self.component_id, f"Constitutional violations: {len(critical_violations)} critical")
    
    def _handle_policy_violation(self, cycle_id: str, policy_result: Dict) -> None:
        """Handle policy evaluation failure."""
        if policy_result.get("violations"):
            # Rollback if configured
            kernel = self.kernel
            if isinstance(kernel, MockGovernanceKernel):
                policies = kernel.policies.get(self.component_id)
                if policies and policies.rollback_on_degradation:
                    kernel.rollback_component(self.component_id, cycle_id)
    
    # ========== FAC Certification ==========
    
    def request_certification(self, cycles: List[str]) -> ComponentCertification:
        """Request Factual Alignment Certificate for this component."""
        event = GovernanceEvent(
            event_id=str(uuid.uuid4()),
            event_type=GovernanceEventType.CERTIFICATION_REQUESTED,
            timestamp=datetime.now(),
            component_id=self.component_id,
            cycle_id=cycles[-1] if cycles else None,
            payload={"cycles": cycles, "cycle_count": len(cycles)},
            severity="info"
        )
        self.kernel.publish_event(event)
        
        cert = self.kernel.request_certification(self.component_id, cycles)
        
        event = GovernanceEvent(
            event_id=str(uuid.uuid4()),
            event_type=GovernanceEventType.CERTIFICATION_GRANTED if cert.status == ComponentStatus.CERTIFIED else GovernanceEventType.CERTIFICATION_DENIED,
            timestamp=datetime.now(),
            component_id=self.component_id,
            cycle_id=cycles[-1] if cycles else None,
            payload={"certification_id": cert.certification_id, "status": cert.status.value},
            severity="info"
        )
        self.kernel.publish_event(event)
        
        return cert
    
    # ========== Subscriber Management ==========
    
    def subscribe_cycle_events(self, callback: Callable[[CycleContext], None]) -> None:
        """Subscribe to cycle completion events."""
        self._cycle_subscribers.append(callback)
    
    def subscribe_violation_events(self, callback: Callable[[List[Dict]], None]) -> None:
        """Subscribe to violation events."""
        self._violation_subscribers.append(callback)


class GovernedFRACycle(FRACycle):
    """FRA Cycle with integrated Governance Kernel hooks."""
    
    def __init__(self, *args, governance_hooks: Optional[FACGovernanceHooks] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.governance = governance_hooks or FACGovernanceHooks(component_id=self.cycle_id)
    
    def run(self) -> CycleContext:
        """Execute cycle with governance hooks."""
        self.governance.on_cycle_start(self.cycle_id, self.initial_model)
        
        try:
            context = super().run()
            self.governance.on_cycle_complete(context)
            return context
        except Exception as e:
            # Find failed stage
            failed_stage = FRACycleStage.RECURSE
            for stage in self.stages:
                # Check if stage was attempted (simplified)
                pass
            self.governance.on_cycle_failed(self.cycle_id, e, failed_stage)
            raise


def create_governed_fra_cycle(
    component_id: str,
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
    policy: Optional[FACPolicy] = None,
    kernel: Optional[GovernanceKernelInterface] = None
) -> GovernedFRACycle:
    """Factory for creating a governance-integrated FRA cycle."""
    hooks = FACGovernanceHooks(kernel=kernel, component_id=component_id)
    
    if policy and kernel:
        kernel.register_policy(policy)
    
    return GovernedFRACycle(
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
        governance_hooks=hooks
    )