"""Validation Metrics Engine - FAC-V1 through FAC-V5 constitutional tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import statistics

from fae.state.csr import ConstitutionalStateRecord, get_csr
from fae.evidence.registry import EvidenceRegistry, get_registry


@dataclass
class ValidationResult:
    """Result of a FAC validation test."""
    test_name: str
    passed: bool
    score: float  # 0.0 - 1.0
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CycleValidationReport:
    """Complete validation report for one FRA cycle."""
    cycle_id: str
    results: List[ValidationResult]
    overall_passed: bool
    overall_score: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def failed_tests(self) -> List[ValidationResult]:
        return [r for r in self.results if not r.passed]


class ValidationMetricsEngine:
    """
    Computes FAC-V1 through FAC-V5 validation tests per cycle.
    
    FAC-V1: Accuracy Test - Did factual accuracy increase or remain stable?
    FAC-V2: Uncertainty Test - Did uncertainty decrease without artificial confidence inflation?
    FAC-V3: Calibration Test - Did confidence levels become better aligned with actual outcomes?
    FAC-V4: Explanatory Power Test - Does the model explain more observed evidence than before?
    FAC-V5: Error Correction Test - Did the model incorporate discrepancies rather than reinforce prior assumptions?
    """
    
    def __init__(
        self,
        evidence_registry: Optional[EvidenceRegistry] = None,
        csr: Optional[ConstitutionalStateRecord] = None
    ):
        self.registry = evidence_registry or get_registry()
        self.csr = csr or get_csr()
    
    def validate_cycle(self, cycle_id: str) -> CycleValidationReport:
        """Run all five FAC validation tests for a cycle."""
        results = []
        
        # FAC-V1: Accuracy Test
        results.append(self._accuracy_test(cycle_id))
        
        # FAC-V2: Uncertainty Test
        results.append(self._uncertainty_test(cycle_id))
        
        # FAC-V3: Calibration Test
        results.append(self._calibration_test(cycle_id))
        
        # FAC-V4: Explanatory Power Test
        results.append(self._explanatory_power_test(cycle_id))
        
        # FAC-V5: Error Correction Test
        results.append(self._error_correction_test(cycle_id))
        
        # Compute overall
        passed = all(r.passed for r in results)
        overall_score = statistics.mean(r.score for r in results) if results else 0.0
        
        report = CycleValidationReport(
            cycle_id=cycle_id,
            results=results,
            overall_passed=passed,
            overall_score=overall_score
        )
        
        # Store in CSR
        self.csr.log_validation_report(cycle_id, report)
        
        return report
    
    def _accuracy_test(self, cycle_id: str) -> ValidationResult:
        """
        FAC-V1: Accuracy Test
        Did the model's predictions match observed reality more closely than before?
        """
        cycle_log = self.csr.get_cycle(cycle_id)
        if not cycle_log:
            return ValidationResult(
                test_name="FAC-V1: Accuracy Test",
                passed=False,
                score=0.0,
                message="Cycle not found in CSR"
            )
        
        # Get comparison evidence from this cycle
        comparison_evidence = self.registry.get_by_cycle_and_stage(cycle_id, "compare")
        
        if not comparison_evidence:
            return ValidationResult(
                test_name="FAC-V1: Accuracy Test",
                passed=False,
                score=0.0,
                message="No comparison evidence found"
            )
        
        # Extract alignment scores
        alignment_scores = []
        for ev in comparison_evidence:
            if isinstance(ev.content, dict) and "alignment_score" in ev.content:
                alignment_scores.append(ev.content["alignment_score"])
        
        if not alignment_scores:
            return ValidationResult(
                test_name="FAC-V1: Accuracy Test",
                passed=False,
                score=0.0,
                message="No alignment scores in comparison evidence"
            )
        
        current_accuracy = alignment_scores[-1]  # Latest alignment score
        
        # Compare with previous cycle
        prev_cycles = self.csr.get_previous_cycles(cycle_id, limit=1)
        prev_accuracy = 0.0
        if prev_cycles:
            prev_report = self.csr.get_validation_report(prev_cycles[0].cycle_id)
            if prev_report:
                for r in prev_report.results:
                    if r.test_name == "FAC-V1: Accuracy Test":
                        prev_accuracy = r.details.get("alignment_score", 0.0)
                        break
        
        improved = current_accuracy >= prev_accuracy
        score = current_accuracy
        
        return ValidationResult(
            test_name="FAC-V1: Accuracy Test",
            passed=improved,
            score=score,
            message=f"Accuracy {'improved' if improved else 'degraded'}: {prev_accuracy:.3f} -> {current_accuracy:.3f}",
            details={
                "current_accuracy": current_accuracy,
                "previous_accuracy": prev_accuracy,
                "alignment_scores": alignment_scores
            }
        )
    
    def _uncertainty_test(self, cycle_id: str) -> ValidationResult:
        """
        FAC-V2: Uncertainty Test
        Did uncertainty decrease without artificial confidence inflation?
        """
        cycle_log = self.csr.get_cycle(cycle_id)
        if not cycle_log:
            return ValidationResult(
                test_name="FAC-V2: Uncertainty Test",
                passed=False,
                score=0.0,
                message="Cycle not found"
            )
        
        # Get reasoning evidence
        reasoning_evidence = self.registry.get_by_cycle_and_stage(cycle_id, "reason")
        
        if not reasoning_evidence:
            return ValidationResult(
                test_name="FAC-V2: Uncertainty Test",
                passed=False,
                score=0.0,
                message="No reasoning evidence found"
            )
        
        # Extract confidence and uncertainty metrics
        confidences = []
        for ev in reasoning_evidence:
            if isinstance(ev.content, dict):
                if "confidence" in ev.content:
                    confidences.append(ev.content["confidence"])
                if "uncertainty" in ev.content:
                    confidences.append(1.0 - ev.content["uncertainty"])
        
        if not confidences:
            return ValidationResult(
                test_name="FAC-V2: Uncertainty Test",
                passed=False,
                score=0.0,
                message="No confidence/uncertainty data found"
            )
        
        avg_confidence = statistics.mean(confidences)
        
        # Check for artificial inflation: confidence > accuracy
        accuracy_result = self._accuracy_test(cycle_id)
        accuracy = accuracy_result.details.get("current_accuracy", 0.0)
        
        # Uncertainty should decrease (confidence increase) but not exceed accuracy significantly
        confidence_inflation = max(0.0, avg_confidence - accuracy - 0.1)  # Allow 10% margin
        
        prev_cycles = self.csr.get_previous_cycles(cycle_id, limit=1)
        prev_confidence = 0.5
        if prev_cycles:
            prev_report = self.csr.get_validation_report(prev_cycles[0].cycle_id)
            if prev_report:
                for r in prev_report.results:
                    if r.test_name == "FAC-V2: Uncertainty Test":
                        prev_confidence = r.details.get("avg_confidence", 0.5)
                        break
        
        uncertainty_decreased = avg_confidence >= prev_confidence
        no_inflation = confidence_inflation < 0.15  # Threshold for artificial inflation
        
        passed = uncertainty_decreased and no_inflation
        score = max(0.0, 1.0 - confidence_inflation * 2) if uncertainty_decreased else 0.0
        
        return ValidationResult(
            test_name="FAC-V2: Uncertainty Test",
            passed=passed,
            score=score,
            message=f"Uncertainty {'decreased' if uncertainty_decreased else 'increased'}; inflation: {confidence_inflation:.3f}",
            details={
                "avg_confidence": avg_confidence,
                "previous_confidence": prev_confidence,
                "accuracy": accuracy,
                "confidence_inflation": confidence_inflation,
                "uncertainty_decreased": uncertainty_decreased
            }
        )
    
    def _calibration_test(self, cycle_id: str) -> ValidationResult:
        """
        FAC-V3: Calibration Test
        Did confidence levels become better aligned with actual outcomes?
        """
        cycle_log = self.csr.get_cycle(cycle_id)
        if not cycle_log:
            return ValidationResult(
                test_name="FAC-V3: Calibration Test",
                passed=False,
                score=0.0,
                message="Cycle not found"
            )
        
        # Get predictions and actual outcomes
        reasoning_evidence = self.registry.get_by_cycle_and_stage(cycle_id, "reason")
        measurement_evidence = self.registry.get_by_cycle_and_stage(cycle_id, "measure_reality")
        
        if not reasoning_evidence or not measurement_evidence:
            return ValidationResult(
                test_name="FAC-V3: Calibration Test",
                passed=False,
                score=0.0,
                message="Missing reasoning or measurement evidence"
            )
        
        # Build calibration data: (confidence, actual_correct)
        calibration_points = []
        
        for r_ev in reasoning_evidence:
            if not isinstance(r_ev.content, dict):
                continue
            predictions = r_ev.content.get("predictions", {})
            confidence = r_ev.content.get("confidence", 0.5)
            
            for m_ev in measurement_evidence:
                if not isinstance(m_ev.content, dict):
                    continue
                measurements = m_ev.content
                
                # Match predictions to measurements
                for pred_key, pred_value in predictions.items():
                    if pred_key in measurements:
                        actual_value = measurements[pred_key]
                        # Simple binary: prediction correct if close enough
                        is_correct = self._values_close(pred_value, actual_value)
                        calibration_points.append((confidence, is_correct))
        
        if not calibration_points:
            return ValidationResult(
                test_name="FAC-V3: Calibration Test",
                passed=False,
                score=0.0,
                message="No calibration points could be established"
            )
        
        # Compute Expected Calibration Error (ECE)
        ece = self._compute_ece(calibration_points)
        
        # Compare with previous cycle
        prev_cycles = self.csr.get_previous_cycles(cycle_id, limit=1)
        prev_ece = 1.0  # Worst case
        if prev_cycles:
            prev_report = self.csr.get_validation_report(prev_cycles[0].cycle_id)
            if prev_report:
                for r in prev_report.results:
                    if r.test_name == "FAC-V3: Calibration Test":
                        prev_ece = r.details.get("ece", 1.0)
                        break
        
        improved = ece <= prev_ece
        # Score is inverse of ECE (lower ECE = better calibration)
        score = max(0.0, 1.0 - ece * 2)
        
        return ValidationResult(
            test_name="FAC-V3: Calibration Test",
            passed=improved,
            score=score,
            message=f"Calibration {'improved' if improved else 'degraded'}: ECE {prev_ece:.3f} -> {ece:.3f}",
            details={
                "ece": ece,
                "previous_ece": prev_ece,
                "calibration_points": len(calibration_points),
                "improved": improved
            }
        )
    
    def _explanatory_power_test(self, cycle_id: str) -> ValidationResult:
        """
        FAC-V4: Explanatory Power Test
        Does the model explain more observed evidence than before?
        """
        cycle_log = self.csr.get_cycle(cycle_id)
        if not cycle_log:
            return ValidationResult(
                test_name="FAC-V4: Explanatory Power Test",
                passed=False,
                score=0.0,
                message="Cycle not found"
            )
        
        # Count facts explained by model
        fact_evidence = self.registry.get_by_cycle_and_stage(cycle_id, "extract_facts")
        reasoning_evidence = self.registry.get_by_cycle_and_stage(cycle_id, "reason")
        
        if not fact_evidence or not reasoning_evidence:
            return ValidationResult(
                test_name="FAC-V4: Explanatory Power Test",
                passed=False,
                score=0.0,
                message="Missing fact or reasoning evidence"
            )
        
        total_facts = len(fact_evidence)
        explained_facts = 0
        
        for r_ev in reasoning_evidence:
            if isinstance(r_ev.content, dict):
                explanations = r_ev.content.get("explanations", [])
                explained_facts += len(explanations)
        
        # Cap at total facts
        explained_facts = min(explained_facts, total_facts)
        explanatory_ratio = explained_facts / total_facts if total_facts > 0 else 0.0
        
        # Compare with previous cycle
        prev_cycles = self.csr.get_previous_cycles(cycle_id, limit=1)
        prev_ratio = 0.0
        if prev_cycles:
            prev_report = self.csr.get_validation_report(prev_cycles[0].cycle_id)
            if prev_report:
                for r in prev_report.results:
                    if r.test_name == "FAC-V4: Explanatory Power Test":
                        prev_ratio = r.details.get("explanatory_ratio", 0.0)
                        break
        
        improved = explanatory_ratio >= prev_ratio
        score = explanatory_ratio
        
        return ValidationResult(
            test_name="FAC-V4: Explanatory Power Test",
            passed=improved,
            score=score,
            message=f"Explanatory power {'improved' if improved else 'degraded'}: {prev_ratio:.3f} -> {explanatory_ratio:.3f}",
            details={
                "explanatory_ratio": explanatory_ratio,
                "previous_ratio": prev_ratio,
                "total_facts": total_facts,
                "explained_facts": explained_facts,
                "improved": improved
            }
        )
    
    def _error_correction_test(self, cycle_id: str) -> ValidationResult:
        """
        FAC-V5: Error Correction Test
        Did the model incorporate discrepancies rather than reinforce prior assumptions?
        """
        cycle_log = self.csr.get_cycle(cycle_id)
        if not cycle_log:
            return ValidationResult(
                test_name="FAC-V5: Error Correction Test",
                passed=False,
                score=0.0,
                message="Cycle not found"
            )
        
        # Get comparison evidence (discrepancies) and update evidence
        comparison_evidence = self.registry.get_by_cycle_and_stage(cycle_id, "compare")
        update_evidence = self.registry.get_by_cycle_and_stage(cycle_id, "update_model")
        
        if not comparison_evidence:
            return ValidationResult(
                test_name="FAC-V5: Error Correction Test",
                passed=False,
                score=0.0,
                message="No comparison evidence found"
            )
        
        # Count discrepancies and how many were addressed
        total_discrepancies = 0
        addressed_discrepancies = 0
        
        for c_ev in comparison_evidence:
            if isinstance(c_ev.content, dict):
                discrepancies = c_ev.content.get("discrepancies", [])
                total_discrepancies += len(discrepancies)
        
        for u_ev in update_evidence:
            if isinstance(u_ev.content, dict):
                addressed = u_ev.content.get("discrepancies_addressed", 0)
                addressed_discrepancies += addressed
        
        if total_discrepancies == 0:
            # No discrepancies is actually good - model was accurate
            return ValidationResult(
                test_name="FAC-V5: Error Correction Test",
                passed=True,
                score=1.0,
                message="No discrepancies found - model accurate",
                details={"total_discrepancies": 0, "addressed": 0}
            )
        
        correction_rate = addressed_discrepancies / total_discrepancies
        
        # Check if model reinforced prior assumptions (anti-pattern)
        # This would show as high confidence despite discrepancies
        reasoning_evidence = self.registry.get_by_cycle_and_stage(cycle_id, "reason")
        confidence_despite_errors = False
        for r_ev in reasoning_evidence:
            if isinstance(r_ev.content, dict):
                confidence = r_ev.content.get("confidence", 0.5)
                if confidence > 0.8 and total_discrepancies > 0:
                    confidence_despite_errors = True
                    break
        
        passed = correction_rate > 0.5 and not confidence_despite_errors
        score = correction_rate * (0.5 if confidence_despite_errors else 1.0)
        
        return ValidationResult(
            test_name="FAC-V5: Error Correction Test",
            passed=passed,
            score=score,
            message=f"Error correction rate: {correction_rate:.3f}; confidence_despite_errors: {confidence_despite_errors}",
            details={
                "correction_rate": correction_rate,
                "total_discrepancies": total_discrepancies,
                "addressed_discrepancies": addressed_discrepancies,
                "confidence_despite_errors": confidence_despite_errors
            }
        )
    
    def _values_close(self, pred: Any, actual: Any, tolerance: float = 0.1) -> bool:
        """Check if predicted and actual values are close."""
        if isinstance(pred, (int, float)) and isinstance(actual, (int, float)):
            if actual == 0:
                return abs(pred - actual) < tolerance
            return abs(pred - actual) / abs(actual) < tolerance
        return pred == actual
    
    def _compute_ece(self, calibration_points: List[Tuple[float, bool]], n_bins: int = 10) -> float:
        """Compute Expected Calibration Error."""
        if not calibration_points:
            return 1.0
        
        bin_counts = [0] * n_bins
        bin_correct = [0] * n_bins
        bin_confidence = [0.0] * n_bins
        
        for confidence, correct in calibration_points:
            bin_idx = min(int(confidence * n_bins), n_bins - 1)
            bin_counts[bin_idx] += 1
            bin_correct[bin_idx] += 1 if correct else 0
            bin_confidence[bin_idx] += confidence
        
        ece = 0.0
        total = len(calibration_points)
        
        for i in range(n_bins):
            if bin_counts[i] > 0:
                avg_confidence = bin_confidence[i] / bin_counts[i]
                accuracy = bin_correct[i] / bin_counts[i]
                ece += (bin_counts[i] / total) * abs(avg_confidence - accuracy)
        
        return ece


def validate_all_cycles() -> Dict[str, CycleValidationReport]:
    """Validate all completed cycles in CSR."""
    csr = get_csr()
    engine = ValidationMetricsEngine()
    reports = {}
    
    for cycle_log in csr.get_completed_cycles():
        report = engine.validate_cycle(cycle_log.cycle_id)
        reports[cycle_log.cycle_id] = report
    
    return reports


def get_validation_engine() -> ValidationMetricsEngine:
    """Get global validation engine instance."""
    return ValidationMetricsEngine()