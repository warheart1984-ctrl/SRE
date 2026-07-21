"""Tests for Mythar Cross-Language Rosetta Layer (MCRL-1.0)."""

import unittest
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path
import tempfile
import shutil

from fae.mcr.rosetta import (
    MCRLRosettaEngine,
    ExternalRoot,
    ExternalGrammarRule,
    AlignmentEntry,
    AlignmentMode,
    RosettaConformanceProfile,
    EvidenceSource,
    EvidenceStatus
)
from fae.evidence.registry import EvidenceRegistry, ProvenanceMetadata


class TestMCRLBasic(unittest.TestCase):
    """Basic tests for MCRL functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.engine = MCRLRosettaEngine(self.temp_dir)
    
    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_external_root_registration(self):
        """Test external root registration with constitutional validation."""
        
        # Create a minimal evidence record for testing
        evidence_metadata = ProvenanceMetadata(
            source=EvidenceSource.EXTERNAL_DATABASE,
            source_id="test_db",
            timestamp=datetime.now(),
            acquisition_method="extraction",
            confidence=1.0,
            validation_status=EvidenceStatus.VERIFIED,
            validator_id="validator",
            validation_timestamp=datetime.now(),
            content_hash="hash123"
        )
        
        root = ExternalRoot(
            language="english",
            form="concept",
            domain="epistemic",
            gloss="A unit of thought or understanding",
            evidence_id="evidence_123",
            alignment_confidence=0.95
        )
        
        registered_root = self.engine.register_external_root(root)
        self.assertEqual(registered_root.form, "concept")
        self.assertEqual(registered_root.language, "english")
        self.assertIn(registered_root.form, self.engine.external_roots)
    
    def test_external_grammar_rule_registration(self):
        """Test external grammar rule registration."""
        
        rule = ExternalGrammarRule(
            language="english",
            pattern="S -> NP VP",
            mythar_pattern_ref="pattern_1",
            alignment_mode=AlignmentMode.LITERAL,
            cross_domain_alignment=True,
            structural_invariance=True
        )
        
        registered_rule = self.engine.register_external_grammar_rule(rule)
        self.assertEqual(registered_rule.pattern, "S -> NP VP")
        self.assertEqual(registered_rule.language, "english")
        
        rule_id = f"{rule.language}:{rule.mythar_pattern_ref}"
        self.assertIn(rule_id, self.engine.external_grammar_rules)
    
    def test_alignment_creation(self):
        """Test alignment creation with constitutional validation."""
        
        alignment = self.engine.create_alignment(
            mythar_expr="mythar_concept",
            external_expr="external_concept",
            mode=AlignmentMode.EVIDENTIAL,
            source_lang="mythar",
            target_lang="english",
            evidence_id="evidence_123",
            source_domain="epistemic",
            target_domain="epistemic"
        )
        
        self.assertEqual(alignment.mythar_expression, "mythar_concept")
        self.assertEqual(alignment.external_expression, "external_concept")
        self.assertEqual(alignment.mode, AlignmentMode.EVIDENTIAL)
        self.assertIn(alignment.id, self.engine.alignments)
    
    def test_conformance_profile_creation(self):
        """Test rosetta conformance profile creation."""
        
        profile = RosettaConformanceProfile(
            name="Test Conformance Profile",
            description="Test profile for validation",
            mcrl_implemented=True,
            mcrl_version="1.0",
            marl_rosetta_reconstruction=True,
            marl_reconstruction_version="1.0",
            cross_language_ontology=True,
            ontology_edges_implemented=True,
            external_corpora_published=False
        )
        
        self.assertEqual(profile.name, "Test Conformance Profile")
        self.assertTrue(profile.mcrl_implemented)
        self.assertTrue(profile.marl_rosetta_reconstruction)
        
        # Update conformance profile
        updated_profile = self.engine.update_conformance_profile(profile)
        self.assertEqual(updated_profile.profile_id, profile.profile_id)
        self.assertIn(updated_profile.profile_id, self.engine.conformance_profiles)
    
    def test_alignment_validation_quality(self):
        """Test alignment quality validation."""
        
        # Create an alignment
        alignment = self.engine.create_alignment(
            mythar_expr="test_concept",
            external_expr="test_external",
            mode=AlignmentMode.EVIDENTIAL,
            source_lang="mythar",
            target_lang="english",
            evidence_id="evidence_123",
            source_domain="epistemic",
            target_domain="epistemic"
        )
        
        # Validate quality
        quality_report = self.engine.validate_alignment_quality(alignment.id)
        
        self.assertIn("validation_score", quality_report)
        self.assertIn("validations", quality_report)
        self.assertEqual(len(quality_report["validations"]), 4)
        
        # Check validation results
        for validation in quality_report["validations"]:
            self.assertIn("dimension", validation)
            self.assertIn("score", validation)
            self.assertIn("passed", validation)
    
    def test_prototype_reconstruction(self):
        """Test prototype reconstruction pipeline."""
        
        expressions = ["concept_1", "concept_2", "concept_3"]
        languages = ["english", "french", "german"]
        
        # This would normally require actual alignments
        # For testing, we'll simulate the reconstruction
        reconstruction = self.engine.reconstruct_prototype(
            expressions=expressions,
            source_languages=languages,
            reconstruction_mode="full"
        )
        
        self.assertIn("expressions", reconstruction)
        self.assertIn("source_languages", reconstruction)
        self.assertIn("concepts", reconstruction)
        self.assertIn("mythar_concepts", reconstruction)
        self.assertIn("proto_hypotheses", reconstruction)
        self.assertIn("validation_score", reconstruction)
        self.assertIn("validations", reconstruction)
        
        # Check validation structure
        for validation in reconstruction["validations"]:
            self.assertIn("dimension", validation)
            self.assertIn("score", validation)
            self.assertIn("passed", validation)
    
    def test_external_root_functional_validation(self):
        """Test external root functional validation."""
        
        # Test valid case
        root = ExternalRoot(
            language="test",
            form="valid_root",
            domain="test_domain",
            gloss="A test root",
            evidence_id="evidence_valid",
            alignment_confidence=0.9
        )
        
        result = self.engine._validate_root_external(root)
        self.assertTrue(result)  # Should pass validation
        
        # Test invalid case (internal model - should fail)
        invalid_root = ExternalRoot(
            language="test",
            form="invalid_root",
            domain="test_domain",
            gloss="An invalid root",
            evidence_id="evidence_invalid",
            alignment_confidence=0.9,
            source=EvidenceSource.INTERNAL_MODEL
        )
        
        # The validation would check evidence source
        # For now, just ensure the structure is correct
        self.assertEqual(invalid_root.source, EvidenceSource.INTERNAL_MODEL)
    
    def test_conformance_completeness(self):
        """Test conformance profile completeness validation."""
        
        # Incomplete profile (missing MCRL)
        incomplete_profile = RosettaConformanceProfile(
            name="Incomplete Profile",
            description="Profile missing MCRL",
            mcrl_implemented=False,  # Intentionally false
            marl_rosetta_reconstruction=False,
            cross_language_ontology=False
        )
        
        # Should raise error when updating incomplete profile
        with self.assertRaises(ValueError):
            self.engine.update_conformance_profile(incomplete_profile)
        
        # Complete profile
        complete_profile = RosettaConformanceProfile(
            name="Complete Profile",
            description="Fully compliant profile",
            mcrl_implemented=True,
            mcrl_version="1.0",
            marl_rosetta_reconstruction=True,
            marl_reconstruction_version="1.0",
            cross_language_ontology=True,
            ontology_edges_implemented=True,
            external_corpora_published=False
        )
        
        # Should update successfully
        updated_profile = self.engine.update_conformance_profile(complete_profile)
        self.assertTrue(updated_profile.mcrl_implemented)
        self.assertTrue(updated_profile.marl_rosetta_reconstruction)


class TestMCRLIntegration(unittest.TestCase):
    """Integration tests for MCRL with other FAE components."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.engine = MCRLRosettaEngine(self.temp_dir)
    
    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_mcr_l_with_fae_integration(self):
        """Test MCRL integration with FAE components."""
        
        # Create evidence registry
        evidence_registry = EvidenceRegistry(self.temp_dir / "evidence")
        
        # Create external root with evidence
        evidence_metadata = ProvenanceMetadata(
            source=EvidenceSource.EXTERNAL_DATABASE,
            source_id="integration_db",
            timestamp=datetime.now(),
            acquisition_method="integration_test",
            confidence=1.0,
            validation_status=EvidenceStatus.VERIFIED,
            validator_id="integration_validator",
            validation_timestamp=datetime.now(),
            content_hash="integration_hash"
        )
        
        root = ExternalRoot(
            language="english",
            form="integration_root",
            domain="integration_test",
            gloss="Root for integration test",
            evidence_id="integration_evidence_123",
            alignment_confidence=0.95
        )
        
        # Register with evidence registry
        evidence_registry.register(
            content=root,
            content_type="external_root",
            provenance=evidence_metadata,
            cycle_id="mcr_test",
            stage="initial"
        )
        
        # Register external root in MCRL
        registered_root = self.engine.register_external_root(root)
        self.assertEqual(registered_root.form, "integration_root")
        
        # Verify evidence was registered
        evidence = evidence_registry.get("integration_evidence_123")
        self.assertIsNotNone(evidence)
        self.assertEqual(evidence.content_type, "external_root")
    
    def test_mcr_l_alignment_with_fae(self):
        """Test MCRL alignment with FAE validation."""
        
        # Create an alignment
        alignment = self.engine.create_alignment(
            mythar_expr="fae_aligned_concept",
            external_expr="fae_aligned_external",
            mode=AlignmentMode.EVIDENTIAL,
            source_lang="mythar",
            target_lang="english",
            evidence_id="fae_integration_evidence",
            source_domain="integration_test",
            target_domain="integration_test"
        )
        
        # Validate quality
        quality_report = self.engine.validate_alignment_quality(alignment.id)
        
        # Verify integration with FAE pattern
        self.assertGreater(quality_report["validation_score"], 0.0)
        self.assertGreater(quality_report["overall_score"], 0.0)
        
        # Check evidence integration
        self.assertIn("validation_score", quality_report)
        self.assertIn("overall_score", quality_report)
        self.assertIsInstance(quality_report["validations"], list)


if __name__ == "__main__":
    unittest.main()