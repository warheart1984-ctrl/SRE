"""Drift Detection Engine - FAC-D1 through FAC-D3 drift prevention."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import statistics

from fae.state.csr import ConstitutionalStateRecord, get_csr
from fae.evidence.registry import EvidenceRegistry, EvidenceSource, get_registry
from fae.metrics.validation import ValidationMetricsEngine, CycleValidationReport, get_csr


class DriftType(Enum):
    """Types of drift detected per FAC-D mechanisms."""
    ALIGNMENT_DEGRADATION = "alignment_degradation"        # FAC-D1: External anchor loss
    CONFIDENCE_INFLATION = "confidence_inflation"           # FAC-D2: Discrepancy penalty failure
    BELIEF_REINFORCEMENT = "belief_reinforcement"           # FAC-D3: Self-reinforcing belief loops
    EVIDENCE_DECAY = "evidence_decay"                       # External evidence becoming stale
    CIRCULAR_EVIDENCE = "circular_evidence"                 # FAC-E4 violation


class DriftSeverity(Enum):
    """Severity levels for drift violations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"  # Triggers constitutional halt


@dataclass
class DriftEvent:
    """Recorded drift detection event."""
    cycle_id: str
    drift_type: DriftType
    severity: DriftSeverity
    message: str
    metrics: Dict[str, float]
    timestamp: datetime = field(default_factory=datetime.now)
    mitigated: bool = False
    mitigation_action: Optional[str] = None


@dataclass
class DriftThresholds:
    """Configurable thresholds for drift detection."""
    # FAC-D1: External Anchor
    min_alignment_score: float = 0.5
    max_alignment_drop: float = 0.15  # Max drop between cycles
    
    # FAC-D2: Discrepancy Penalty
    max_confidence_inflation: float = 0.2  # Confidence - accuracy > this = inflation
    min_discrepancy_penalty: float = 0.1   # Confidence should drop by this much per discrepancy
    
    # FAC-D3: Belief Isolation
    max_self_reinforcement_cycles: int = 3  # Cycles without external evidence
    max_internal_confidence_boost: float = 0.15  # Max confidence increase from internal only
    
    # Evidence Decay
    max_evidence_age_hours: float = 24.0  # Evidence older than this decays
    
    # Circular Evidence
    max_circular_depth: int = 2  # Max self-referential evidence chain


class DriftDetectionEngine:
    """
    Monitors and detects drift per FAC-D1, FAC-D2, FAC-D3.
    
    FAC-D1: External Anchor - Every cycle must anchor to external evidence
    FAC-D2: Discrepancy Penalty - Discrepancies must reduce confidence unless corrected
    FAC-D3: Belief Isolation - Internal beliefs cannot recursively reinforce without external validation
    """
    
    def __init__(
        self,
        evidence_registry: Optional[EvidenceRegistry] = None,
        csr: Optional[ConstitutionalStateRecord] = None,
        thresholds: Optional[DriftThresholds] = None
    ):
        self.registry = evidence_registry or get_registry()
        self.csr = csr or get_csr()
        self.thresholds = thresholds or DriftThresholds()
        self.drift_events: List[DriftEvent] = []
        self._validation_engine = ValidationMetricsEngine(self.registry, self.csr)
    
    def check_cycle(self, cycle_id: str) -> List[DriftEvent]:
        """Run all drift checks for a completed cycle."""
        events = []
        
        # FAC-D1: External Anchor Check
        events.extend(self._check_external_anchor(cycle_id))
        
        # FAC-D2: Discrepancy Penalty Check
        events.extend(self._check_discrepancy_penalty(cycle_id))
        
        # FAC-D3: Belief Isolation Check
        events.extend(self._check_belief_isolation(cycle_id))
        
        # Evidence Decay Check
        events.extend(self._check_evidence_decay(cycle_id))
        
        # Circular Evidence Check
        events.extend(self._check_circular_evidence(cycle_id))
        
        # Record events
        self.drift_events.extend(events)
        
        # Log to CSR
        for event in events:
            self.csr.log_drift_event(event)
        
        return events
    
    def _check_external_anchor(self, cycle_id: str) -> List[DriftEvent]:
        """FAC-D1: Every cycle must anchor itself to external evidence."""
        events = []
        
        # Check if cycle has external evidence in observe/extract/measure stages
        external_stages = ["observe", "extract_facts", "measure_reality"]
        external_evidence_count = 0
        
        for stage in external_stages:
            evs = self.registry.get_by_cycle_and_stage(cycle_id, stage)
            for ev in evs:
                if ev.source in (EvidenceSource.EXTERNAL_SENSOR, EvidenceSource.EXTERNAL_API,
                                  EvidenceSource.HUMAN_OBSERVER, EvidenceSource.EXTERNAL_DATABASE,
                                  EvidenceSource.THIRD_PARTY_AUDIT, EvidenceSource.CRYPTOGRAPHIC_PROOF):
                    external_evidence_count += 1
        
        if external_evidence_count == 0:
            events.append(DriftEvent(
                cycle_id=cycle_id,
                drift_type=DriftType.ALIGNMENT_DEGRADATION,
                severity=DriftSeverity.CRITICAL,
                message="FAC-D1 violated: No external evidence in cycle",
                metrics={"external_evidence_count": 0}
            ))
        
        # Check alignment score
        comparison_evidence = self.registry.get_by_cycle_and_stage(cycle_id, "compare")
        if comparison_evidence:
            for ev in comparison_evidence:
                if isinstance(ev.content, dict) and "alignment_score" in ev.content:
                    score = ev.content["alignment_score"]
                    if score < self.thresholds.min_alignment_score:
                        events.append(DriftEvent(
                            cycle_id=cycle_id,
                            drift_type=DriftType.ALIGNMENT_DEGRADATION,
                            severity=DriftSeverity.HIGH,
                            message=f"FAC-D1: Alignment score {score:.3f} below threshold {self.thresholds.min_alignment_score}",
                            metrics={"alignment_score": score}
                        ))
                    
                    # Check drop from previous cycle
                    prev_cycles = self.csr.get_previous_cycles(cycle_id, limit=1)
                    if prev_cycles:
                        prev_comparison = self.registry.get_by_cycle_and_stage(prev_cycles[0].cycle_id, "compare")
                        for pev in prev_comparison:
                            if isinstance(pev.content, dict) and "alignment_score" in pev.content:
                                prev_score = pev.content["alignment_score"]
                                drop = prev_score - score
                                if drop > self.thresholds.max_alignment_drop:
                                    events.append(DriftEvent(
                                        cycle_id=cycle_id,
                                        drift_type=DriftType.ALIGNMENT_DEGRADATION,
                                        severity=DriftSeverity.HIGH,
                                        message=f"FAC-D1: Alignment dropped {drop:.3f} (max allowed: {self.thresholds.max_alignment_drop})",
                                        metrics={"alignment_drop": drop, "prev_score": prev_score, "current_score": score}
                                    ))
                                break
        
        return events
    
    def _check_discrepancy_penalty(self, cycle_id: str) -> List[DriftEvent]:
        """FAC-D2: Discrepancies must reduce confidence unless corrected."""
        events = []
        
        comparison_evidence = self.registry.get_by_cycle_and_stage(cycle_id, "compare")
        reasoning_evidence = self.registry.get_by_cycle_and_stage(cycle_id, "reason")
        
        if not comparison_evidence or not reasoning_evidence:
            return events
        
        # Count discrepancies
        total_discrepancies = 0
        for ev in comparison_evidence:
            if isinstance(ev.content, dict):
                total_discrepancies += len(ev.content.get("discrepancies", []))
        
        if total_discrepancies == 0:
            return events  # No discrepancies, no penalty needed
        
        # Check confidence in reasoning
        for rev in reasoning_evidence:
            if isinstance(rev.content, dict):
                confidence = rev.content.get("confidence", 0.5)
                
                # Expected confidence reduction from discrepancies
                expected_penalty = total_discrepancies * self.thresholds.min_discrepancy_penalty
                max_allowed_confidence = 1.0 - expected_penalty
                
                if confidence > max_allowed_confidence + 0.1:  # Allow small margin
                    events.append(DriftEvent(
                        cycle_id=cycle_id,
                        drift_type=DriftType.CONFIDENCE_INFLATION,
                        severity=DriftSeverity.HIGH,
                        message=f"FAC-D2: Confidence {confidence:.3f} too high for {total_discrepancies} discrepancies (max allowed: {max_allowed_confidence:.3f})",
                        metrics={
                            "confidence": confidence,
                            "discrepancies": total_discrepancies,
                            "expected_penalty": expected_penalty,
                            "max_allowed_confidence": max_allowed_confidence
                        }
                    ))
        
        return events
    
    def _check_belief_isolation(self, cycle_id: str) -> List[DriftEvent]:
        """FAC-D3: Internal beliefs cannot recursively reinforce without external validation."""
        events = []
        
        # Check recent cycles for external evidence
        recent_cycles = self.csr.get_recent_cycles(limit=self.thresholds.max_self_reinforcement_cycles + 1)
        
        if len(recent_cycles) < 2:
            return events
        
        cycles_without_external = 0
        internal_confidence_boost = 0.0
        prev_confidence = 0.5
        
        for cycle in reversed(recent_cycles):
            # Check for external evidence
            has_external = False
            for stage in ["observe", "extract_facts", "measure_reality"]:
                evs = self.registry.get_by_cycle_and_stage(cycle.cycle_id, stage)
                for ev in evs:
                    if ev.source in (EvidenceSource.EXTERNAL_SENSOR, EvidenceSource.EXTERNAL_API,
                                      EvidenceSource.HUMAN_OBSERVER, EvidenceSource.EXTERNAL_DATABASE,
                                      EvidenceSource.THIRD_PARTY_AUDIT, EvidenceSource.CRYPTOGRAPHIC_PROOF):
                        has_external = True
                        break
                if has_external:
                    break
            
            if not has_external:
                cycles_without_external += 1
                
                # Check confidence boost from internal sources only
                reasoning_evidence = self.registry.get_by_cycle_and_stage(cycle.cycle_id, "reason")
                for rev in reasoning_evidence:
                    if isinstance(rev.content, dict):
                        confidence = rev.content.get("confidence", 0.5)
                        if confidence > prev_confidence:
                            internal_confidence_boost += confidence - prev_confidence
                        prev_confidence = confidence
            else:
                cycles_without_external = 0
                internal_confidence_boost = 0.0
                prev_confidence = 0.5
        
        if cycles_without_external > self.thresholds.max_self_reinforcement_cycles:
            events.append(DriftEvent(
                cycle_id=cycle_id,
                drift_type=DriftType.BELIEF_REINFORCEMENT,
                severity=DriftSeverity.CRITICAL,
                message=f"FAC-D3: {cycles_without_external} cycles without external evidence (max: {self.thresholds.max_self_reinforcement_cycles})",
                metrics={
                    "cycles_without_external": cycles_without_external,
                    "internal_confidence_boost": internal_confidence_boost
                }
            ))
        
        if internal_confidence_boost > self.thresholds.max_internal_confidence_boost:
            events.append(DriftEvent(
                cycle_id=cycle_id,
                drift_type=DriftType.BELIEF_REINFORCEMENT,
                severity=DriftSeverity.HIGH,
                message=f"FAC-D3: Internal confidence boost {internal_confidence_boost:.3f} exceeds threshold {self.thresholds.max_internal_confidence_boost}",
                metrics={"internal_confidence_boost": internal_confidence_boost}
            ))
        
        return events
    
    def _check_evidence_decay(self, cycle_id: str) -> List[DriftEvent]:
        """Check for stale evidence."""
        events = []
        now = datetime.now()
        
        all_evidence = self.registry.get_by_cycle(cycle_id)
        for ev in all_evidence:
            age_hours = (now - ev.timestamp).total_seconds() / 3600
            if age_hours > self.thresholds.max_evidence_age_hours:
                events.append(DriftEvent(
                    cycle_id=cycle_id,
                    drift_type=DriftType.EVIDENCE_DECAY,
                    severity=DriftSeverity.MEDIUM,
                    message=f"Evidence {ev.evidence_id} is {age_hours:.1f}h old (max: {self.thresholds.max_evidence_age_hours}h)",
                    metrics={"evidence_age_hours": age_hours, "evidence_id": ev.evidence_id}
                ))
        
        return events
    
    def _check_circular_evidence(self, cycle_id: str) -> List[DriftEvent]:
        """FAC-E4: Evidence cannot be derived from the model it validates."""
        events = []
        
        # Check if any evidence in this cycle has INTERNAL_MODEL source and is used for validation
        internal_evidence = self.registry.get_by_source(EvidenceSource.INTERNAL_MODEL, cycle_id)
        derived_evidence = self.registry.get_by_source(EvidenceSource.DERIVED_INFERENCE, cycle_id)
        
        circular_count = len(internal_evidence) + len(derived_evidence)
        
        # Check if these are used in validation stages
        validation_stages = ["compare", "build_model"]
        used_in_validation = False
        
        for stage in validation_stages:
            evs = self.registry.get_by_cycle_and_stage(cycle_id, stage)
            for ev in evs:
                # Check if evidence references internal/derived sources
                if isinstance(ev.content, dict):
                    sources = ev.content.get("evidence_sources", [])
                    for src in sources:
                        if src in [e.evidence_id for e in internal_evidence + derived_evidence]:
                            used_in_validation = True
                            break
        
        if used_in_validation and circular_count > self.thresholds.max_circular_depth:
            events.append(DriftEvent(
                cycle_id=cycle_id,
                drift_type=DriftType.CIRCULAR_EVIDENCE,
                severity=DriftSeverity.CRITICAL,
                message=f"FAC-E4 violated: {circular_count} circular evidence items used in validation",
                metrics={"circular_evidence_count": circular_count, "used_in_validation": True}
            ))
        
        return events
    
    def get_drift_summary(self, cycle_id: Optional[str] = None) -> Dict[str, Any]:
        """Get drift summary for a cycle or all cycles."""
        if cycle_id:
            events = [e for e in self.drift_events if e.cycle_id == cycle_id]
        else:
            events = self.drift_events
        
        summary = {
            "total_events": len(events),
            "by_type": {},
            "by_severity": {},
            "critical_count": 0,
            "mitigated_count": 0
        }
        
        for event in events:
            summary["by_type"][event.drift_type.value] = summary["by_type"].get(event.drift_type.value, 0) + 1
            summary["by_severity"][event.severity.value] = summary["by_severity"].get(event.severity.value, 0) + 1
            if event.severity == DriftSeverity.CRITICAL:
                summary["critical_count"] += 1
            if event.mitigated:
                summary["mitigated_count"] += 1
        
        return summary
    
    def requires_constitutional_halt(self, cycle_id: str) -> bool:
        """Check if cycle has critical drift requiring constitutional halt."""
        events = [e for e in self.drift_events if e.cycle_id == cycle_id and e.severity == DriftSeverity.CRITICAL]
        return len(events) > 0


# Constitutional violation detection
class ConstitutionalViolationDetector:
    """Detects FAC constitutional violations per section 7."""
    
    VIOLATION_TYPES = [
        "recurses_on_belief",
        "fabricates_confidence",
        "ignores_discrepancies",
        "degrades_factual_alignment",
        "uses_circular_evidence"
    ]
    
    def __init__(
        self,
        drift_engine: Optional[DriftDetectionEngine] = None,
        validation_engine: Optional[ValidationMetricsEngine] = None
    ):
        self.drift_engine = drift_engine or DriftDetectionEngine()
        self.validation_engine = validation_engine or ValidationMetricsEngine()
    
    def check_violations(self, cycle_id: str) -> List[Dict[str, Any]]:
        """Check all constitutional violations for a cycle."""
        violations = []
        
        # 1. Recurses on belief rather than evidence
        if self._recurses_on_belief(cycle_id):
            violations.append({
                "type": "recurses_on_belief",
                "severity": "critical",
                "message": "Cycle recurses on internal belief without external evidence anchor",
                "cycle_id": cycle_id
            })
        
        # 2. Fabricates confidence without external validation
        if self._fabricates_confidence(cycle_id):
            violations.append({
                "type": "fabricates_confidence",
                "severity": "critical",
                "message": "Confidence inflated without external validation",
                "cycle_id": cycle_id
            })
        
        # 3. Ignores discrepancies
        if self._ignores_discrepancies(cycle_id):
            violations.append({
                "type": "ignores_discrepancies",
                "severity": "high",
                "message": "Discrepancies between prediction and reality not incorporated",
                "cycle_id": cycle_id
            })
        
        # 4. Degrades factual alignment
        if self._degrades_alignment(cycle_id):
            violations.append({
                "type": "degrades_factual_alignment",
                "severity": "critical",
                "message": "Factual alignment decreased from previous cycle",
                "cycle_id": cycle_id
            })
        
        # 5. Uses internally generated evidence to validate itself
        if self._uses_circular_evidence(cycle_id):
            violations.append({
                "type": "uses_circular_evidence",
                "severity": "critical",
                "message": "Internal evidence used to validate model (FAC-E4 violation)",
                "cycle_id": cycle_id
            })
        
        return violations
    
    def _recurses_on_belief(self, cycle_id: str) -> bool:
        """Check if cycle lacks external evidence anchor."""
        drift_events = self.drift_engine.check_cycle(cycle_id)
        return any(e.drift_type == DriftType.ALIGNMENT_DEGRADATION and e.severity == DriftSeverity.CRITICAL 
                   for e in drift_events)
    
    def _fabricates_confidence(self, cycle_id: str) -> bool:
        """Check for confidence inflation."""
        drift_events = self.drift_engine.check_cycle(cycle_id)
        return any(e.drift_type == DriftType.CONFIDENCE_INFLATION and e.severity in (DriftSeverity.HIGH, DriftSeverity.CRITICAL)
                   for e in drift_events)
    
    def _ignores_discrepancies(self, cycle_id: str) -> bool:
        """Check if discrepancies were ignored."""
        report = self.validation_engine.validate_cycle(cycle_id)
        for result in report.results:
            if result.test_name == "FAC-V5: Error Correction Test" and not result.passed:
                return True
        return False
    
    def _degrades_alignment(self, cycle_id: str) -> bool:
        """Check if factual alignment degraded."""
        report = self.validation_engine.validate_cycle(cycle_id)
        for result in report.results:
            if result.test_name == "FAC-V1: Accuracy Test" and not result.passed:
                return True
        return False
    
    def _uses_circular_evidence(self, cycle_id: str) -> bool:
        """Check for circular evidence."""
        drift_events = self.drift_engine.check_cycle(cycle_id)
        return any(e.drift_type == DriftType.CIRCULAR_EVIDENCE for e in drift_events)


def get_drift_engine() -> DriftDetectionEngine:
    """Get global drift detection engine instance."""
    return DriftDetectionEngine()