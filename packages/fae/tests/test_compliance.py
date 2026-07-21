"""Compliance Tests for FAC v1.0 Checklist."""

from __future__ import annotations

import unittest
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List
from pathlib import Path
import tempfile
import shutil

from fae.api import (
    FactualAlignmentEngine,
    FAEConfig,
    Evidence,
    ProvenanceMetadata,
    EvidenceSource,
    EvidenceStatus,
    FRACycle,
    FRACycleStage,
    CycleContext,
    ValidationMetricsEngine,
    CycleValidationReport,
    DriftDetectionEngine,
    DriftEvent,
    DriftType,
    DriftSeverity,
    DriftThresholds,
    ConstitutionalStateRecord,
    get_csr,
    get_registry,
    reset_fae,
    create_fae,
    quick_cycle,
    FRACycleError,
    FACInvariantViolation
)
from fae.evidence.registry import EvidenceRegistry
from fae.state.csr import reset_csr
from fae.evidence.registry import reset_registry


class TestFACComplianceChecklist(unittest.TestCase):
    """Test suite covering FAC v1.0 Compliance Checklist."""
    
    def setUp(self):
        """Set up fresh FAE for each test."""
        reset_fae()
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = FAEConfig(storage_path=self.temp_dir)
        self.fae = FactualAlignmentEngine(self.config)
    
    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        reset_fae()
    
    # ========== 1. FRA Loop Compliance ==========
    
    def test_fra_loop_all_nine_stages_implemented(self):
        """Checklist 1.1: System implements all nine FRA stages."""
        stages = [s.value for s in FRACycleStage]
        expected = [
            "observe", "extract_facts", "build_model", "reason", "act",
            "measure_reality", "compare", "update_model", "recurse"
        ]
        self.assertEqual(stages, expected)
    
    def test_fra_loop_stages_explicitly_logged(self):
        """Checklist 1.2: Each stage is explicitly logged."""
        # Create minimal cycle
        cycle_id = "test_logging"
        self.fae.csr.start_cycle(cycle_id, {"test": "model"})
        
        # Log each stage
        for stage in FRACycleStage:
            self.fae.csr.log_stage(
                cycle_id=cycle_id,
                stage=stage.value,
                success=True,
                output={},
                evidence_ids=[],
                metrics={},
                errors=[]
            )
        
        cycle_log = self.fae.csr.get_cycle(cycle_id)
        self.assertIsNotNone(cycle_log)
        
        logged_stages = [s.stage for s in cycle_log.stages]
        expected_stages = [s.value for s in FRACycleStage]
        self.assertEqual(logged_stages, expected_stages)
    
    def test_fra_loop_recursion_traceable(self):
        """Checklist 1.3: Recursion is traceable across cycles."""
        cycle1_id = "cycle_1"
        cycle2_id = "cycle_2"
        
        self.fae.csr.start_cycle(cycle1_id, {"v": 1})
        self.fae.csr.end_cycle(cycle1_id, success=True, final_model={"v": 2})
        
        self.fae.csr.start_cycle(cycle2_id, {"v": 2})
        self.fae.csr.end_cycle(cycle2_id, success=True, final_model={"v": 3})
        
        # Both cycles should be retrievable
        log1 = self.fae.csr.get_cycle(cycle1_id)
        log2 = self.fae.csr.get_cycle(cycle2_id)
        
        self.assertIsNotNone(log1)
        self.assertIsNotNone(log2)
        self.assertEqual(log1.final_model, {"v": 2})
        self.assertEqual(log2.final_model, {"v": 3})
    
    # ========== 2. Evidence Compliance ==========
    
    def test_evidence_externality_requirement_fac_e1(self):
        """Checklist 2.1: All evidence is external (FAC-E1)."""
        # Valid external evidence
        prov = ProvenanceMetadata(
            source=EvidenceSource.EXTERNAL_SENSOR,
            source_id="sensor_1",
            timestamp=datetime.now(),
            acquisition_method="temperature_reading",
            confidence=0.95,
            validation_status=EvidenceStatus.VERIFIED,
            validator_id="validator_1",
            validation_timestamp=datetime.now(),
            content_hash="abc123"
        )
        
        evidence = self.fae.register_evidence(
            content={"temp": 22.5},
            content_type="sensor",
            provenance=prov,
            cycle_id="cycle_1",
            stage="observe"
        )
        self.assertEqual(evidence.provenance.source, EvidenceSource.EXTERNAL_SENSOR)
        
        # Internal model evidence should be rejected for external stages
        bad_prov = ProvenanceMetadata(
            source=EvidenceSource.INTERNAL_MODEL,
            source_id="model_1",
            timestamp=datetime.now(),
            acquisition_method="inference",
            confidence=0.9,
            validation_status=EvidenceStatus.UNVERIFIED,
            validator_id=None,
            validation_timestamp=None,
            content_hash="def456"
        )
        
        with self.assertRaises(ValueError) as ctx:
            self.fae.register_evidence(
                content={"prediction": 23.0},
                content_type="prediction",
                provenance=bad_prov,
                cycle_id="cycle_1",
                stage="observe"  # Observe stage requires external
            )
        self.assertIn("FAC-E1 violation", str(ctx.exception))
    
    def test_evidence_independent_verifiability_fac_e2(self):
        """Checklist 2.2: All evidence independently verifiable (FAC-E2)."""
        prov = ProvenanceMetadata(
            source=EvidenceSource.THIRD_PARTY_AUDIT,
            source_id="auditor_1",
            timestamp=datetime.now(),
            acquisition_method="independent_audit",
            confidence=0.99,
            validation_status=EvidenceStatus.VERIFIED,
            validator_id="auditor_1",
            validation_timestamp=datetime.now(),
            content_hash="hash123"
        )
        
        evidence = self.fae.register_evidence(
            content={"audit_result": "pass"},
            content_type="audit",
            provenance=prov,
            cycle_id="cycle_1",
            stage="extract_facts"
        )
        
        self.assertTrue(evidence.is_externally_verifiable())
        
        # Unverified evidence should fail check
        prov_unverified = ProvenanceMetadata(
            source=EvidenceSource.EXTERNAL_API,
            source_id="api_1",
            timestamp=datetime.now(),
            acquisition_method="api_call",
            confidence=0.8,
            validation_status=EvidenceStatus.UNVERIFIED,
            validator_id=None,
            validation_timestamp=None,
            content_hash="hash456"
        )
        
        evidence_unverified = self.fae.register_evidence(
            content={"data": "unverified"},
            content_type="api",
            provenance=prov_unverified,
            cycle_id="cycle_1",
            stage="extract_facts"
        )
        
        self.assertFalse(evidence_unverified.is_externally_verifiable())
        unverified = self.fae.get_unverified_evidence("cycle_1")
        self.assertIn(evidence_unverified, unverified)
    
    def test_evidence_provenance_metadata_fac_e3(self):
        """Checklist 2.3: All evidence has provenance metadata (FAC-E3)."""
        prov = ProvenanceMetadata(
            source=EvidenceSource.EXTERNAL_DATABASE,
            source_id="db_1",
            timestamp=datetime.now(),
            acquisition_method="sql_query",
            confidence=0.9,
            validation_status=EvidenceStatus.VERIFIED,
            validator_id="validator_1",
            validation_timestamp=datetime.now(),
            content_hash="provenance_hash",
            dependencies=frozenset(["dep1", "dep2"])
        )
        
        evidence = self.fae.register_evidence(
            content={"record": "data"},
            content_type="database",
            provenance=prov,
            cycle_id="cycle_1",
            stage="observe"
        )
        
        # Verify all provenance fields present
        p = evidence.provenance
        self.assertEqual(p.source, EvidenceSource.EXTERNAL_DATABASE)
        self.assertEqual(p.source_id, "db_1")
        self.assertIsNotNone(p.timestamp)
        self.assertEqual(p.acquisition_method, "sql_query")
        self.assertEqual(p.confidence, 0.9)
        self.assertEqual(p.validation_status, EvidenceStatus.VERIFIED)
        self.assertEqual(p.validator_id, "validator_1")
        self.assertIsNotNone(p.validation_timestamp)
        self.assertEqual(p.content_hash, "provenance_hash")
        self.assertEqual(set(p.dependencies), {"dep1", "dep2"})
    
    def test_evidence_non_circularity_fac_e4(self):
        """Checklist 2.4: No circular evidence dependencies (FAC-E4)."""
        # Create evidence A
        prov_a = ProvenanceMetadata(
            source=EvidenceSource.EXTERNAL_SENSOR,
            source_id="sensor_a",
            timestamp=datetime.now(),
            acquisition_method="read",
            confidence=1.0,
            validation_status=EvidenceStatus.VERIFIED,
            validator_id="val",
            validation_timestamp=datetime.now(),
            content_hash="hash_a"
        )
        
        ev_a = self.fae.register_evidence(
            content={"a": 1},
            content_type="test",
            provenance=prov_a,
            cycle_id="cycle_1",
            stage="observe"
        )
        
        # Create evidence B that depends on A
        prov_b = ProvenanceMetadata(
            source=EvidenceSource.EXTERNAL_SENSOR,
            source_id="sensor_b",
            timestamp=datetime.now(),
            acquisition_method="read",
            confidence=1.0,
            validation_status=EvidenceStatus.VERIFIED,
            validator_id="val",
            validation_timestamp=datetime.now(),
            content_hash="hash_b",
            dependencies=frozenset([ev_a.id])
        )
        
        ev_b = self.fae.register_evidence(
            content={"b": 2},
            content_type="test",
            provenance=prov_b,
            cycle_id="cycle_1",
            stage="extract_facts"
        )
        
        # Try to create evidence C that depends on B and A (should work)
        prov_c = ProvenanceMetadata(
            source=EvidenceSource.EXTERNAL_SENSOR,
            source_id="sensor_c",
            timestamp=datetime.now(),
            acquisition_method="read",
            confidence=1.0,
            validation_status=EvidenceStatus.VERIFIED,
            validator_id="val",
            validation_timestamp=datetime.now(),
            content_hash="hash_c",
            dependencies=frozenset([ev_a.id, ev_b.id])
        )
        
        ev_c = self.fae.register_evidence(
            content={"c": 3},
            content_type="test",
            provenance=prov_c,
            cycle_id="cycle_1",
            stage="measure_reality"
        )
        
        # Try circular: evidence that depends on itself
        prov_circular = ProvenanceMetadata(
            source=EvidenceSource.EXTERNAL_SENSOR,
            source_id="sensor_d",
            timestamp=datetime.now(),
            acquisition_method="read",
            confidence=1.0,
            validation_status=EvidenceStatus.VERIFIED,
            validator_id="val",
            validation_timestamp=datetime.now(),
            content_hash="hash_d",
            dependencies=frozenset([ev_c.id, "self_ref"])  # Would need to reference itself
        )
        
        # Direct circular dependency in constructor should fail
        with self.assertRaises(ValueError) as ctx:
            Evidence(
                id="self_ref",
                content={},
                content_type="test",
                provenance=ProvenanceMetadata(
                    source=EvidenceSource.EXTERNAL_SENSOR,
                    source_id="x",
                    timestamp=datetime.now(),
                    acquisition_method="x",
                    confidence=1.0,
                    validation_status=EvidenceStatus.VERIFIED,
                    validator_id="x",
                    validation_timestamp=datetime.now(),
                    content_hash="x",
                    dependencies=frozenset(["self_ref"])
                ),
                cycle_id="cycle_1",
                stage="observe"
            )
        self.assertIn("FAC-E4 violation", str(ctx.exception))
    
    # ========== 3. Invariant Compliance ==========
    
    def test_invariant_factual_alignment_measured(self):
        """Checklist 3.1: Factual alignment measured per cycle."""
        cycle_id = "alignment_test"
        self.fae.csr.start_cycle(cycle_id, {"accuracy": 0.8})
        
        # Add comparison evidence with alignment score
        prov = ProvenanceMetadata(
            source=EvidenceSource.THIRD_PARTY_AUDIT,
            source_id="comparator",
            timestamp=datetime.now(),
            acquisition_method="comparison",
            confidence=1.0,
            validation_status=EvidenceStatus.VERIFIED,
            validator_id="comparator",
            validation_timestamp=datetime.now(),
            content_hash="comp_hash"
        )
        
        self.fae.register_evidence(
            content={"alignment_score": 0.85, "discrepancies": []},
            content_type="comparison",
            provenance=prov,
            cycle_id=cycle_id,
            stage="compare"
        )
        
        self.fae.csr.end_cycle(cycle_id, success=True, final_model={"accuracy": 0.85})
        
        # Validate alignment
        check = self.fae.check_alignment(cycle_id)
        self.assertTrue(check.passed)
        self.assertIn("0.85", check.message)
    
    def test_invariant_no_cycle_degrades_alignment(self):
        """Checklist 3.2: No cycle degrades factual alignment."""
        # First cycle with high alignment
        self.fae.csr.start_cycle("cycle_1", {"model": 1})
        prov1 = ProvenanceMetadata(
            source=EvidenceSource.THIRD_PARTY_AUDIT,
            source_id="comp", timestamp=datetime.now(),
            acquisition_method="compare", confidence=1.0,
            validation_status=EvidenceStatus.VERIFIED, validator_id="v",
            validation_timestamp=datetime.now(), content_hash="h1"
        )
        self.fae.register_evidence(
            content={"alignment_score": 0.9},
            content_type="compare",
            provenance=prov1,
            cycle_id="cycle_1",
            stage="compare"
        )
        self.fae.csr.end_cycle("cycle_1", True, {"model": 1})
        
        # Second cycle with lower alignment - should fail invariant
        self.fae.csr.start_cycle("cycle_2", {"model": 2})
        prov2 = ProvenanceMetadata(
            source=EvidenceSource.THIRD_PARTY_AUDIT,
            source_id="comp", timestamp=datetime.now(),
            acquisition_method="compare", confidence=1.0,
            validation_status=EvidenceStatus.VERIFIED, validator_id="v",
            validation_timestamp=datetime.now(), content_hash="h2"
        )
        self.fae.register_evidence(
            content={"alignment_score": 0.5},
            content_type="compare",
            provenance=prov2,
            cycle_id="cycle_2",
            stage="compare"
        )
        self.fae.csr.end_cycle("cycle_2", True, {"model": 2})
        
        # Validation should catch degradation
        report = self.fae.validate_cycle("cycle_2")
        accuracy_result = next(r for r in report.results if r.test_name == "FAC-V1: Accuracy Test")
        self.assertFalse(accuracy_result.passed)
    
    def test_invariant_violations_trigger_intervention(self):
        """Checklist 3.3: Violations trigger intervention."""
        # Create cycle with critical drift
        self.fae.csr.start_cycle("violation_test", {})
        
        # Add evidence that will trigger confidence inflation
        prov_reason = ProvenanceMetadata(
            source=EvidenceSource.INTERNAL_MODEL,
            source_id="reasoner", timestamp=datetime.now(),
            acquisition_method="inference", confidence=0.95,
            validation_status=EvidenceStatus.UNVERIFIED, validator_id=None,
            validation_timestamp=None, content_hash="rhash"
        )
        self.fae.register_evidence(
            content={"confidence": 0.95, "predictions": {"x": 1}},
            content_type="reasoning", provenance=prov_reason,
            cycle_id="violation_test", stage="reason"
        )
        
        # Add comparison with discrepancies but high confidence
        prov_comp = ProvenanceMetadata(
            source=EvidenceSource.THIRD_PARTY_AUDIT,
            source_id="comp", timestamp=datetime.now(),
            acquisition_method="compare", confidence=1.0,
            validation_status=EvidenceStatus.VERIFIED, validator_id="v",
            validation_timestamp=datetime.now(), content_hash="chash"
        )
        self.fae.register_evidence(
            content={"alignment_score": 0.3, "discrepancies": ["d1", "d2", "d3"]},
            content_type="compare", provenance=prov_comp,
            cycle_id="violation_test", stage="compare"
        )
        
        self.fae.csr.end_cycle("violation_test", True, {})
        
        # Check drift
        drift_events = self.fae.check_drift("violation_test")
        # Should detect confidence inflation
        inflation_events = [e for e in drift_events if e.drift_type == DriftType.CONFIDENCE_INFLATION]
        self.assertGreater(len(inflation_events), 0)
    
    # ========== 4. Validation Compliance ==========
    
    def test_validation_accuracy_computed_per_cycle(self):
        """Checklist 4.1: Accuracy metric computed and stored per cycle."""
        cycle_id = "val_cycle_1"
        self.fae.csr.start_cycle(cycle_id, {})
        
        prov = ProvenanceMetadata(
            source=EvidenceSource.THIRD_PARTY_AUDIT,
            source_id="auditor", timestamp=datetime.now(),
            acquisition_method="audit", confidence=1.0,
            validation_status=EvidenceStatus.VERIFIED, validator_id="auditor",
            validation_timestamp=datetime.now(), content_hash="vh"
        )
        self.fae.register_evidence(
            content={"alignment_score": 0.88},
            content_type="compare",
            provenance=prov,
            cycle_id=cycle_id,
            stage="compare"
        )
        self.fae.csr.end_cycle(cycle_id, True, {})
        
        report = self.fae.validate_cycle(cycle_id)
        accuracy = next(r for r in report.results if r.test_name == "FAC-V1: Accuracy Test")
        self.assertGreater(accuracy.score, 0)
        self.assertIn("current_accuracy", accuracy.details)
    
    def test_validation_uncertainty_computed_per_cycle(self):
        """Checklist 4.2: Uncertainty metric computed and stored per cycle."""
        cycle_id = "val_cycle_2"
        self.fae.csr.start_cycle(cycle_id, {})
        
        prov = ProvenanceMetadata(
            source=EvidenceSource.INTERNAL_MODEL,
            source_id="reasoner", timestamp=datetime.now(),
            acquisition_method="inference", confidence=0.7,
            validation_status=EvidenceStatus.UNVERIFIED, validator_id=None,
            validation_timestamp=None, content_hash="rh"
        )
        self.fae.register_evidence(
            content={"confidence": 0.7, "predictions": {}},
            content_type="reason",
            provenance=prov,
            cycle_id=cycle_id,
            stage="reason"
        )
        self.fae.csr.end_cycle(cycle_id, True, {})
        
        report = self.fae.validate_cycle(cycle_id)
        unc = next(r for r in report.results if r.test_name == "FAC-V2: Uncertainty Test")
        self.assertIn("avg_confidence", unc.details)
    
    def test_validation_calibration_computed_per_cycle(self):
        """Checklist 4.3: Calibration metric computed and stored per cycle."""
        cycle_id = "val_cycle_3"
        self.fae.csr.start_cycle(cycle_id, {})
        
        # Need both reasoning and measurement for calibration
        prov_r = ProvenanceMetadata(
            source=EvidenceSource.INTERNAL_MODEL, source_id="r", timestamp=datetime.now(),
            acquisition_method="inf", confidence=0.8,
            validation_status=EvidenceStatus.UNVERIFIED, validator_id=None,
            validation_timestamp=None, content_hash="rh"
        )
        self.fae.register_evidence(
            content={"confidence": 0.8, "predictions": {"x": 10}},
            content_type="reason",
            provenance=prov_r,
            cycle_id=cycle_id,
            stage="reason"
        )
        
        prov_m = ProvenanceMetadata(
            source=EvidenceSource.EXTERNAL_SENSOR, source_id="m", timestamp=datetime.now(),
            acquisition_method="measure", confidence=1.0,
            validation_status=EvidenceStatus.VERIFIED, validator_id="v",
            validation_timestamp=datetime.now(), content_hash="mh"
        )
        self.fae.register_evidence(
            content={"x": 10},
            content_type="measure_reality",
            provenance=prov_m,
            cycle_id=cycle_id,
            stage="measure_reality"
        )
        self.fae.csr.end_cycle(cycle_id, True, {})
        
        report = self.fae.validate_cycle(cycle_id)
        cal = next(r for r in report.results if r.test_name == "FAC-V3: Calibration Test")
        self.assertIn("ece", cal.details)
    
    def test_validation_explanatory_power_computed_per_cycle(self):
        """Checklist 4.4: Explanatory power metric computed and stored per cycle."""
        cycle_id = "val_cycle_4"
        self.fae.csr.start_cycle(cycle_id, {})
        
        # Facts
        for i in range(3):
            prov = ProvenanceMetadata(
                source=EvidenceSource.EXTERNAL_SENSOR, source_id=f"s{i}", timestamp=datetime.now(),
                acquisition_method="obs", confidence=1.0,
                validation_status=EvidenceStatus.VERIFIED, validator_id="v",
                validation_timestamp=datetime.now(), content_hash=f"h{i}"
            )
            self.fae.register_evidence(
                content={"fact": i},
                content_type="extract_facts",
                provenance=prov,
                cycle_id=cycle_id,
                stage="extract_facts"
            )
        
        # Reasoning with explanations
        prov_r = ProvenanceMetadata(
            source=EvidenceSource.INTERNAL_MODEL, source_id="r", timestamp=datetime.now(),
            acquisition_method="inf", confidence=0.8,
            validation_status=EvidenceStatus.UNVERIFIED, validator_id=None,
            validation_timestamp=None, content_hash="rh"
        )
        self.fae.register_evidence(
            content={"confidence": 0.8, "explanations": ["e1", "e2"]},
            content_type="reason",
            provenance=prov_r,
            cycle_id=cycle_id,
            stage="reason"
        )
        self.fae.csr.end_cycle(cycle_id, True, {})
        
        report = self.fae.validate_cycle(cycle_id)
        exp = next(r for r in report.results if r.test_name == "FAC-V4: Explanatory Power Test")
        self.assertIn("explanatory_ratio", exp.details)
    
    def test_validation_error_correction_recorded_per_cycle(self):
        """Checklist 4.5: Error correction behavior recorded per cycle."""
        cycle_id = "val_cycle_5"
        self.fae.csr.start_cycle(cycle_id, {})
        
        # Comparison with discrepancies
        prov_c = ProvenanceMetadata(
            source=EvidenceSource.THIRD_PARTY_AUDIT, source_id="c", timestamp=datetime.now(),
            acquisition_method="compare", confidence=1.0,
            validation_status=EvidenceStatus.VERIFIED, validator_id="v",
            validation_timestamp=datetime.now(), content_hash="ch"
        )
        self.fae.register_evidence(
            content={"alignment_score": 0.6, "discrepancies": ["d1", "d2"]},
            content_type="compare",
            provenance=prov_c,
            cycle_id=cycle_id,
            stage="compare"
        )
        
        # Update addressing discrepancies
        prov_u = ProvenanceMetadata(
            source=EvidenceSource.INTERNAL_MODEL, source_id="u", timestamp=datetime.now(),
            acquisition_method="update", confidence=0.9,
            validation_status=EvidenceStatus.UNVERIFIED, validator_id=None,
            validation_timestamp=None, content_hash="uh"
        )
        self.fae.register_evidence(
            content={"discrepancies_addressed": 2},
            content_type="update_model",
            provenance=prov_u,
            cycle_id=cycle_id,
            stage="update_model"
        )
        self.fae.csr.end_cycle(cycle_id, True, {})
        
        report = self.fae.validate_cycle(cycle_id)
        err = next(r for r in report.results if r.test_name == "FAC-V5: Error Correction Test")
        self.assertIn("correction_rate", err.details)
        self.assertEqual(err.details["correction_rate"], 1.0)  # 2/2 addressed
    
    # ========== 5. Drift Prevention Compliance ==========
    
    def test_drift_external_anchor_enforced(self):
        """Checklist 5.1: External evidence anchor enforced."""
        # Cycle with no external evidence
        cycle_id = "no_anchor"
        self.fae.csr.start_cycle(cycle_id, {})
        
        # Only internal evidence
        prov = ProvenanceMetadata(
            source=EvidenceSource.INTERNAL_MODEL, source_id="m", timestamp=datetime.now(),
            acquisition_method="inf", confidence=0.9,
            validation_status=EvidenceStatus.UNVERIFIED, validator_id=None,
            validation_timestamp=None, content_hash="h"
        )
        self.fae.register_evidence(
            content={"internal": "data"},
            content_type="reason",
            provenance=prov,
            cycle_id=cycle_id,
            stage="reason"
        )
        self.fae.csr.end_cycle(cycle_id, True, {})
        
        drift = self.fae.check_drift(cycle_id)
        anchor_events = [e for e in drift if e.drift_type == DriftType.ALIGNMENT_DEGRADATION]
        self.assertGreater(len(anchor_events), 0)
        self.assertEqual(anchor_events[0].severity, DriftSeverity.CRITICAL)
    
    def test_drift_discrepancy_penalty_enforced(self):
        """Checklist 5.2: Discrepancy reduces confidence unless corrected."""
        cycle_id = "disc_penalty"
        self.fae.csr.start_cycle(cycle_id, {})
        
        # Reasoning with high confidence
        prov_r = ProvenanceMetadata(
            source=EvidenceSource.INTERNAL_MODEL, source_id="r", timestamp=datetime.now(),
            acquisition_method="inf", confidence=0.9,
            validation_status=EvidenceStatus.UNVERIFIED, validator_id=None,
            validation_timestamp=None, content_hash="rh"
        )
        self.fae.register_evidence(
            content={"confidence": 0.9, "predictions": {}},
            content_type="reason",
            provenance=prov_r,
            cycle_id=cycle_id,
            stage="reason"
        )
        
        # Comparison with many discrepancies
        prov_c = ProvenanceMetadata(
            source=EvidenceSource.THIRD_PARTY_AUDIT, source_id="c", timestamp=datetime.now(),
            acquisition_method="compare", confidence=1.0,
            validation_status=EvidenceStatus.VERIFIED, validator_id="v",
            validation_timestamp=datetime.now(), content_hash="ch"
        )
        self.fae.register_evidence(
            content={"alignment_score": 0.4, "discrepancies": ["d1", "d2", "d3", "d4", "d5"]},
            content_type="compare",
            provenance=prov_c,
            cycle_id=cycle_id,
            stage="compare"
        )
        self.fae.csr.end_cycle(cycle_id, True, {})
        
        drift = self.fae.check_drift(cycle_id)
        penalty_events = [e for e in drift if e.drift_type == DriftType.CONFIDENCE_INFLATION]
        self.assertGreater(len(penalty_events), 0)
    
    def test_drift_belief_isolation_enforced(self):
        """Checklist 5.3: Internal beliefs cannot self-reinforce without external validation."""
        # Multiple cycles without external evidence
        for i in range(5):
            cid = f"belief_cycle_{i}"
            self.fae.csr.start_cycle(cid, {})
            
            prov = ProvenanceMetadata(
                source=EvidenceSource.INTERNAL_MODEL, source_id="m", timestamp=datetime.now(),
                acquisition_method="inf", confidence=0.7 + i * 0.05,  # Increasing confidence
                validation_status=EvidenceStatus.UNVERIFIED, validator_id=None,
                validation_timestamp=None, content_hash=f"h{i}"
            )
            self.fae.register_evidence(
                content={"confidence": 0.7 + i * 0.05},
                content_type="reason",
                provenance=prov,
                cycle_id=cid,
                stage="reason"
            )
            self.fae.csr.end_cycle(cid, True, {})
        
        # Check last cycle for belief reinforcement
        drift = self.fae.check_drift("belief_cycle_4")
        belief_events = [e for e in drift if e.drift_type == DriftType.BELIEF_REINFORCEMENT]
        self.assertGreater(len(belief_events), 0)


class TestEndToEndFRAcycle(unittest.TestCase):
    """End-to-end tests for complete FRA cycle execution."""
    
    def setUp(self):
        reset_fae()
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = FAEConfig(storage_path=self.temp_dir)
        self.fae = FactualAlignmentEngine(self.config)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        reset_fae()
    
    def test_complete_fra_cycle_execution(self):
        """Test full FRA cycle with all stages."""
        # Track calls
        calls = {"observe": 0, "extract": 0, "build": 0, "reason": 0,
                 "act": 0, "measure": 0, "compare": 0, "update": 0, "recurse": 0}
        
        def observe():
            calls["observe"] += 1
            return {"sensor_data": 42.0}
        
        def extract(data):
            calls["extract"] += 1
            return [{"fact": data["sensor_data"], "confidence": 0.95}]
        
        def build_model(model, facts):
            calls["build"] += 1
            return {"value": facts[0]["fact"], "confidence": facts[0]["confidence"]}
        
        def reason(model):
            calls["reason"] += 1
            return {"predictions": {"next": model["value"] + 1}, "confidence": 0.85}
        
        def act(reasoning):
            calls["act"] += 1
            return {"action": "increment", "result": reasoning["predictions"]["next"]}
        
        def measure():
            calls["measure"] += 1
            return {"next": 43.0}
        
        def compare(predictions, measurements):
            calls["compare"] += 1
            pred = predictions.get("next", 0)
            actual = measurements.get("next", 0)
            diff = abs(pred - actual)
            return {
                "alignment_score": 1.0 - min(diff / 10, 1.0),
                "discrepancies": [] if diff < 0.5 else ["prediction_off"]
            }
        
        def update_model(model, comparison):
            calls["update"] += 1
            return {**model, "value": model["value"] + 1}
        
        def should_continue(ctx):
            calls["recurse"] += 1
            return ctx.metadata.get("recurse", False)
        
        cycle = self.fae.create_cycle(
            observers={"sensor": observe},
            extractors={"sensor": extract},
            model_builder=build_model,
            reasoner=reason,
            actors={"increment": act},
            measurers={"next_val": measure},
            comparator=compare,
            updater=update_model,
            should_continue=should_continue,
            initial_model={"value": 42.0}
        )
        
        context = self.fae.run_cycle(cycle)
        
        # All stages executed
        for stage, count in calls.items():
            if stage != "recurse":  # recurse called at end
                self.assertEqual(count, 1, f"Stage {stage} not executed")
        
        # Cycle completed successfully
        self.assertTrue(context.metadata.get("recurse", False))
        
        # Evidence registered for each stage
        for stage in ["observe", "extract_facts", "build_model", "reason",
                      "act", "measure_reality", "compare", "update_model"]:
            evidence = self.fae.get_stage_evidence(cycle.cycle_id, stage)
            self.assertGreater(len(evidence), 0, f"No evidence for {stage}")
    
    def test_fra_cycle_validation_passes(self):
        """Test that a well-formed cycle passes validation."""
        def observe(): return {"x": 1.0}
        def extract(d): return [{"fact": d["x"], "confidence": 0.9}]
        def build(m, f): return {"val": f[0]["fact"]}
        def reason(m): return {"predictions": {"y": m["val"] + 1}, "confidence": 0.8}
        def act(r): return {"done": True}
        def measure(): return {"y": 2.0}
        def compare(p, m): return {"alignment_score": 1.0, "discrepancies": []}
        def update(m, c): return m
        def should_continue(ctx): return False
        
        cycle = self.fae.create_cycle(
            observers={"s": observe}, extractors={"s": extract},
            model_builder=build, reasoner=reason, actors={"a": act},
            measurers={"m": measure}, comparator=compare, updater=update,
            should_continue=should_continue, initial_model={}
        )
        
        self.fae.run_cycle(cycle)
        report = self.fae.validate_cycle(cycle.cycle_id)
        
        # All validation tests should pass for this perfect cycle
        self.assertTrue(report.overall_passed)
    
    def test_fra_cycle_fails_on_invariant_violation(self):
        """Test that FAC-1 violation halts cycle."""
        def observe(): return {"x": 1.0}
        def extract(d): return [{"fact": d["x"], "confidence": 0.9}]
        def build(m, f): return {"val": f[0]["fact"]}
        def reason(m): return {"predictions": {"y": 100}, "confidence": 0.9}  # Wildly wrong
        def act(r): return {"done": True}
        def measure(): return {"y": 2.0}  # Actual is 2, predicted 100
        def compare(p, m): return {"alignment_score": 0.02, "discrepancies": ["huge_error"]}
        def update(m, c): return m
        def should_continue(ctx): return False
        
        cycle = self.fae.create_cycle(
            observers={"s": observe}, extractors={"s": extract},
            model_builder=build, reasoner=reason, actors={"a": act},
            measurers={"m": measure}, comparator=compare, updater=update,
            should_continue=should_continue, initial_model={}
        )
        
        with self.assertRaises(FACInvariantViolation):
            self.fae.run_cycle(cycle)


class TestGovernanceIntegration(unittest.TestCase):
    """Test Governance Kernel integration."""
    
    def setUp(self):
        reset_fae()
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = FAEConfig(storage_path=self.temp_dir, enable_governance=True)
        self.fae = FactualAlignmentEngine(self.config)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        reset_fae()
    
    def test_policy_evaluation(self):
        """Test FAC policy evaluation by Governance Kernel."""
        from fae.governance.hooks import FACPolicy
        
        policy = FACPolicy(
            policy_id="test_policy",
            name="Test Policy",
            description="Test",
            min_factual_alignment=0.8,
            max_uncertainty=0.2
        )
        self.fae.register_policy(policy)
        
        # Run cycle with low alignment
        def observe(): return {"x": 1.0}
        def extract(d): return [{"fact": d["x"]}]
        def build(m, f): return {"val": f[0]["fact"]}
        def reason(m): return {"predictions": {"y": 100}, "confidence": 0.9}
        def act(r): return {}
        def measure(): return {"y": 2.0}
        def compare(p, m): return {"alignment_score": 0.5, "discrepancies": ["error"]}
        def update(m, c): return m
        def should_continue(ctx): return False
        
        cycle = self.fae.create_cycle(
            observers={"s": observe}, extractors={"s": extract},
            model_builder=build, reasoner=reason, actors={"a": act},
            measurers={"m": measure}, comparator=compare, updater=update,
            should_continue=should_continue, initial_model={}
        )
        
        self.fae.run_cycle(cycle)
        
        # Check governance events were published
        kernel = self.fae.governance_hooks.kernel
        events = [e for e in kernel.events if e.component_id == "fae_core"]
        validation_events = [e for e in events if e.event_type.value == "validation_report"]
        self.assertGreater(len(validation_events), 0)


if __name__ == "__main__":
    unittest.main()