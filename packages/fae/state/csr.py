"""Constitutional State Record (CSR) - Immutable audit log for FRA cycles."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import threading
import json
from pathlib import Path
import uuid


class CycleStatus(Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class StageLog:
    """Log entry for a single FRA stage."""
    cycle_id: str
    stage: str
    success: bool
    output: Any = None
    evidence_ids: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "stage": self.stage,
            "success": self.success,
            "output": str(self.output)[:1000] if self.output else None,  # Truncate
            "evidence_ids": self.evidence_ids,
            "metrics": self.metrics,
            "errors": self.errors,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class CycleLog:
    """Complete log for one FRA cycle."""
    cycle_id: str
    status: CycleStatus = CycleStatus.RUNNING
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    initial_model_hash: str = ""
    final_model_hash: str = ""
    stages: List[StageLog] = field(default_factory=list)
    validation_report_id: Optional[str] = None
    drift_events: List[str] = field(default_factory=list)
    violation_events: List[str] = field(default_factory=list)
    
    @property
    def duration_seconds(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "initial_model_hash": self.initial_model_hash,
            "final_model_hash": self.final_model_hash,
            "stages": [s.to_dict() for s in self.stages],
            "validation_report_id": self.validation_report_id,
            "drift_events": self.drift_events,
            "violation_events": self.violation_events,
            "duration_seconds": self.duration_seconds
        }


@dataclass
class ValidationReportLog:
    """Logged validation report."""
    report_id: str
    cycle_id: str
    results: List[Dict[str, Any]]
    overall_passed: bool
    overall_score: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DriftEventLog:
    """Logged drift event."""
    event_id: str
    cycle_id: str
    drift_type: str
    severity: str
    message: str
    metrics: Dict[str, float]
    timestamp: datetime = field(default_factory=datetime.now)
    mitigated: bool = False


class ConstitutionalStateRecord:
    """
    Immutable constitutional state record.
    
    Maintains complete audit trail of all FRA cycles, validations,
    drift events, and constitutional violations.
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        self._cycles: Dict[str, CycleLog] = {}
        self._validation_reports: Dict[str, ValidationReportLog] = {}
        self._drift_events: Dict[str, DriftEventLog] = {}
        self._lock = threading.RLock()
        self._storage_path = storage_path
        if storage_path:
            storage_path.mkdir(parents=True, exist_ok=True)
    
    def start_cycle(self, cycle_id: str, initial_model: Any) -> CycleLog:
        """Start a new cycle log."""
        import hashlib
        model_hash = hashlib.sha256(str(initial_model).encode()).hexdigest()[:16]
        
        cycle = CycleLog(
            cycle_id=cycle_id,
            initial_model_hash=model_hash
        )
        
        with self._lock:
            self._cycles[cycle_id] = cycle
            self._persist_cycle(cycle)
        
        return cycle
    
    def log_stage(
        self,
        cycle_id: str,
        stage: str,
        success: bool,
        output: Any,
        evidence_ids: List[str],
        metrics: Dict[str, float],
        errors: List[str]
    ) -> None:
        """Log a stage execution."""
        with self._lock:
            cycle = self._cycles.get(cycle_id)
            if not cycle:
                return
            
            stage_log = StageLog(
                cycle_id=cycle_id,
                stage=stage,
                success=success,
                output=output,
                evidence_ids=evidence_ids,
                metrics=metrics,
                errors=errors
            )
            cycle.stages.append(stage_log)
            self._persist_cycle(cycle)
    
    def end_cycle(self, cycle_id: str, success: bool, final_model: Any) -> None:
        """End a cycle."""
        import hashlib
        with self._lock:
            cycle = self._cycles.get(cycle_id)
            if not cycle:
                return
            
            cycle.status = CycleStatus.COMPLETED if success else CycleStatus.FAILED
            cycle.end_time = datetime.now()
            cycle.final_model_hash = hashlib.sha256(str(final_model).encode()).hexdigest()[:16]
            self._persist_cycle(cycle)
    
    def rollback_cycle(self, cycle_id: str) -> None:
        """Mark cycle as rolled back."""
        with self._lock:
            cycle = self._cycles.get(cycle_id)
            if cycle:
                cycle.status = CycleStatus.ROLLED_BACK
                cycle.end_time = datetime.now()
                self._persist_cycle(cycle)
    
    def log_validation_report(self, cycle_id: str, report: Any) -> str:
        """Log validation report."""
        report_id = f"val_{cycle_id}_{uuid.uuid4().hex[:8]}"
        
        # Convert report to dict
        results = []
        for r in report.results:
            results.append({
                "test_name": r.test_name,
                "passed": r.passed,
                "score": r.score,
                "message": r.message,
                "details": r.details
            })
        
        val_log = ValidationReportLog(
            report_id=report_id,
            cycle_id=cycle_id,
            results=results,
            overall_passed=report.overall_passed,
            overall_score=report.overall_score
        )
        
        with self._lock:
            self._validation_reports[report_id] = val_log
            # Link to cycle
            cycle = self._cycles.get(cycle_id)
            if cycle:
                cycle.validation_report_id = report_id
                self._persist_cycle(cycle)
            self._persist_validation(val_log)
        
        return report_id
    
    def log_drift_event(self, event: Any) -> str:
        """Log drift event."""
        event_id = f"drift_{event.cycle_id}_{uuid.uuid4().hex[:8]}"
        
        drift_log = DriftEventLog(
            event_id=event_id,
            cycle_id=event.cycle_id,
            drift_type=event.drift_type.value,
            severity=event.severity.value,
            message=event.message,
            metrics=event.metrics,
            timestamp=event.timestamp,
            mitigated=event.mitigated
        )
        
        with self._lock:
            self._drift_events[event_id] = drift_log
            cycle = self._cycles.get(event.cycle_id)
            if cycle:
                cycle.drift_events.append(event_id)
                self._persist_cycle(cycle)
            self._persist_drift(drift_log)
        
        return event_id
    
    def log_violation(self, cycle_id: str, violation: Dict[str, Any]) -> str:
        """Log constitutional violation."""
        event_id = f"viol_{cycle_id}_{uuid.uuid4().hex[:8]}"
        
        with self._lock:
            cycle = self._cycles.get(cycle_id)
            if cycle:
                cycle.violation_events.append(event_id)
                self._persist_cycle(cycle)
        
        return event_id
    
    def get_cycle(self, cycle_id: str) -> Optional[CycleLog]:
        with self._lock:
            return self._cycles.get(cycle_id)
    
    def get_validation_report(self, cycle_id: str) -> Optional[ValidationReportLog]:
        with self._lock:
            for report in self._validation_reports.values():
                if report.cycle_id == cycle_id:
                    return report
            return None
    
    def get_completed_cycles(self) -> List[CycleLog]:
        with self._lock:
            return [c for c in self._cycles.values() if c.status == CycleStatus.COMPLETED]
    
    def get_previous_cycles(self, cycle_id: str, limit: int = 10) -> List[CycleLog]:
        with self._lock:
            cycles = list(self._cycles.values())
            cycles.sort(key=lambda c: c.start_time, reverse=True)
            idx = next((i for i, c in enumerate(cycles) if c.cycle_id == cycle_id), -1)
            if idx >= 0:
                return cycles[idx+1:idx+1+limit]
            return []
    
    def get_recent_cycles(self, limit: int = 10) -> List[CycleLog]:
        with self._lock:
            cycles = list(self._cycles.values())
            cycles.sort(key=lambda c: c.start_time, reverse=True)
            return cycles[:limit]
    
    def validate_factual_alignment(self, cycle_id: str) -> "AlignmentCheck":
        """FAC-1: Validate factual alignment invariant."""
        cycle = self.get_cycle(cycle_id)
        if not cycle:
            return AlignmentCheck(passed=False, message="Cycle not found")
        
        # Check if cycle has validation report
        if not cycle.validation_report_id:
            return AlignmentCheck(passed=False, message="No validation report for cycle")
        
        report = self._validation_reports.get(cycle.validation_report_id)
        if not report:
            return AlignmentCheck(passed=False, message="Validation report not found")
        
        # FAC-1: Must pass overall validation
        if not report.overall_passed:
            return AlignmentCheck(
                passed=False,
                message=f"FAC-1 violated: Overall validation failed (score: {report.overall_score:.3f})"
            )
        
        # Check accuracy specifically (FAC-V1)
        accuracy_passed = False
        for r in report.results:
            if r["test_name"] == "FAC-V1: Accuracy Test":
                accuracy_passed = r["passed"]
                break
        
        if not accuracy_passed:
            return AlignmentCheck(
                passed=False,
                message="FAC-1 violated: FAC-V1 Accuracy Test failed"
            )
        
        return AlignmentCheck(passed=True, message="Factual alignment preserved")
    
    def export_audit_trail(self, cycle_id: Optional[str] = None) -> Dict[str, Any]:
        """Export complete audit trail for audit/review."""
        with self._lock:
            if cycle_id:
                cycle = self._cycles.get(cycle_id)
                return cycle.to_dict() if cycle else {}
            
            return {
                "cycles": {cid: c.to_dict() for cid, c in self._cycles.items()},
                "validation_reports": {rid: {
                    "report_id": r.report_id,
                    "cycle_id": r.cycle_id,
                    "overall_passed": r.overall_passed,
                    "overall_score": r.overall_score,
                    "timestamp": r.timestamp.isoformat()
                } for rid, r in self._validation_reports.items()},
                "drift_events": {eid: {
                    "event_id": e.event_id,
                    "cycle_id": e.cycle_id,
                    "drift_type": e.drift_type,
                    "severity": e.severity,
                    "message": e.message,
                    "metrics": e.metrics,
                    "timestamp": e.timestamp.isoformat(),
                    "mitigated": e.mitigated
                } for eid, e in self._drift_events.items()}
            }
    
    def _persist_cycle(self, cycle: CycleLog) -> None:
        if self._storage_path:
            file_path = self._storage_path / f"cycle_{cycle.cycle_id}.json"
            file_path.write_text(json.dumps(cycle.to_dict(), indent=2))
    
    def _persist_validation(self, report: ValidationReportLog) -> None:
        if self._storage_path:
            file_path = self._storage_path / f"validation_{report.report_id}.json"
            file_path.write_text(json.dumps({
                "report_id": report.report_id,
                "cycle_id": report.cycle_id,
                "results": report.results,
                "overall_passed": report.overall_passed,
                "overall_score": report.overall_score,
                "timestamp": report.timestamp.isoformat()
            }, indent=2))
    
    def _persist_drift(self, event: DriftEventLog) -> None:
        if self._storage_path:
            file_path = self._storage_path / f"drift_{event.event_id}.json"
            file_path.write_text(json.dumps({
                "event_id": event.event_id,
                "cycle_id": event.cycle_id,
                "drift_type": event.drift_type,
                "severity": event.severity,
                "message": event.message,
                "metrics": event.metrics,
                "timestamp": event.timestamp.isoformat(),
                "mitigated": event.mitigated
            }, indent=2))


@dataclass
class AlignmentCheck:
    """Result of FAC-1 alignment check."""
    passed: bool
    message: str


# Global CSR instance
_global_csr: Optional[ConstitutionalStateRecord] = None
_csr_lock = threading.Lock()


def get_csr(storage_path: Optional[Path] = None) -> ConstitutionalStateRecord:
    """Get or create global CSR."""
    global _global_csr
    with _csr_lock:
        if _global_csr is None:
            _global_csr = ConstitutionalStateRecord(storage_path)
        return _global_csr


def reset_csr() -> None:
    """Reset global CSR (for testing)."""
    global _global_csr
    with _csr_lock:
        _global_csr = None