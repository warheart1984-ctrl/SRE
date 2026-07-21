"""Tests for SRE FRA/MCRL composition onto FAE substrate."""

from __future__ import annotations

import pytest

from sre.fra.reconstruction_state import FAE_TO_SRE_STAGE_GROUPS, SRE_TO_FAE_STAGE_MAP
from sre.substrate import (
    ComposedRosettaEngine,
    FRAComposedReconstruction,
    RecursiveCompositionResult,
    reset_fae,
    reset_fae_registry,
    reset_mcrl,
)
from sre.substrate.fra_composition import ComposedReconstructionResult
from fae.cycle.fra_cycle import FRACycleStage
from fae.drift.detection import DriftType, DriftSeverity
from fae.mcr.rosetta import ExternalRoot


@pytest.fixture(autouse=True)
def _reset_fae_state():
    """Reset FAE singletons between tests."""
    reset_fae()
    reset_fae_registry()
    reset_mcrl()
    yield
    reset_fae()
    reset_fae_registry()
    reset_mcrl()


class TestSREToFAEStageMap:
    """Verify documented SRE→FAE stage mapping."""

    def test_all_sre_stages_mapped(self):
        sre_stages = (
            "OBSERVE", "INGEST", "ATTEST", "ALIGN", "CLUSTER",
            "INFER", "VALIDATE", "GOVERN", "CERTIFY", "ARCHIVE",
        )
        for stage in sre_stages:
            assert stage in SRE_TO_FAE_STAGE_MAP

    def test_fae_groups_cover_all_sre_stages(self):
        covered = {s for group in FAE_TO_SRE_STAGE_GROUPS.values() for s in group}
        expected = set(SRE_TO_FAE_STAGE_MAP.keys())
        assert covered == expected

    def test_observe_maps_observe_ingest(self):
        assert SRE_TO_FAE_STAGE_MAP["OBSERVE"] == FRACycleStage.OBSERVE
        assert SRE_TO_FAE_STAGE_MAP["INGEST"] == FRACycleStage.OBSERVE
        assert FAE_TO_SRE_STAGE_GROUPS[FRACycleStage.OBSERVE] == ("OBSERVE", "INGEST")


class TestComposedRosettaEngine:
    """Test MCRL composition layer."""

    def test_map_and_align_empty(self):
        composed = ComposedRosettaEngine()
        result = composed.map_and_align([])
        assert result["temporal_valid"] is True
        assert result["alignment_count"] == 0
        assert result["fae_alignments"] == []

    def test_map_and_align_with_evidence(self):
        from datetime import datetime, timezone

        from sre.evidence.models import LinguisticEvidence, EvidenceType

        now = datetime.now(timezone.utc)
        ev1 = LinguisticEvidence(
            evidence_id="ev_comp_1",
            evidence_type=EvidenceType.INSCRIPTION,
            source_reference="test",
            content={"period": "archaic", "language_code": "MYT", "text": "a"},
            created_at=now,
            submitted_by="tester",
            sha256_hash="abc123",
        )
        ev2 = LinguisticEvidence(
            evidence_id="ev_comp_2",
            evidence_type=EvidenceType.INSCRIPTION,
            source_reference="test",
            content={"period": "classical", "language_code": "MYT", "text": "b"},
            created_at=now,
            submitted_by="tester",
            sha256_hash="def456",
        )
        composed = ComposedRosettaEngine()
        result = composed.map_and_align([ev1, ev2], source_language="mythar")
        assert result["temporal_valid"] is True
        assert result["alignment_count"] == 1
        assert result["fae_alignments"][0]["from_period"] == "archaic"
        assert result["fae_alignments"][0]["to_period"] == "classical"

    def test_register_external_root(self):
        composed = ComposedRosettaEngine()
        root = composed.register_external_root(
            language="latin",
            form="aqua",
            domain="natural",
            gloss="water",
            evidence_id="ev_root_1",
        )
        assert isinstance(root, ExternalRoot)
        assert root.language == "latin"
        assert root.form == "aqua"


class TestFRAComposedReconstruction:
    """Test FRA composition layer (uses mock domain engine)."""

    def test_run_returns_composed_result(self):
        class FakeDomainEngine:
            def reconstruct_language(self, target, period, sources):
                return {
                    "reconstruction_id": "recon_001",
                    "status": "COMPLETED",
                    "fra_stage": "ARCHIVE",
                    "metrics": {"drift": 0.2, "quality": 0.8, "coverage": 0.8},
                    "stages_completed": ["OBSERVE", "ARCHIVE"],
                }

        composed = FRAComposedReconstruction(
            domain_engine=FakeDomainEngine(),
            drift_threshold=0.6,
            use_governed_cycle=False,
        )
        result = composed.run("mythar", "archaic", ["ev1"])
        assert isinstance(result, ComposedReconstructionResult)
        assert result.status == "COMPLETED"
        assert result.drift == 0.2
        assert result.quality == 0.8
        assert result.should_continue is True
        assert result.drift_events == []
        assert result.iteration == 1

    def test_drift_exceeds_threshold(self):
        class HighDriftEngine:
            def reconstruct_language(self, target, period, sources):
                return {
                    "reconstruction_id": "recon_drift",
                    "status": "COMPLETED",
                    "fra_stage": "ARCHIVE",
                    "metrics": {"drift": 0.9, "quality": 0.3, "coverage": 0.1},
                    "stages_completed": ["OBSERVE"],
                }

        composed = FRAComposedReconstruction(
            domain_engine=HighDriftEngine(),
            drift_threshold=0.5,
            use_governed_cycle=False,
        )
        result = composed.run("mythar", "archaic", ["ev1"])
        assert result.should_continue is False
        assert len(result.drift_events) == 1
        assert result.drift_events[0].drift_type == DriftType.ALIGNMENT_DEGRADATION
        assert result.drift_events[0].severity == DriftSeverity.MEDIUM

    def test_failed_domain_result(self):
        class FailEngine:
            def reconstruct_language(self, target, period, sources):
                return {
                    "reconstruction_id": None,
                    "status": "FAILED",
                    "fra_stage": "OBSERVE",
                    "reason": "empty evidence",
                    "metrics": {},
                    "stages_completed": [],
                }

        composed = FRAComposedReconstruction(
            domain_engine=FailEngine(),
            drift_threshold=0.6,
            use_governed_cycle=False,
        )
        result = composed.run("mythar", "archaic", [])
        assert result.status == "FAILED"
        assert result.should_continue is False


class TestGovernedFRACycleRecursive:
    """Integration: SRE stages through GovernedFRACycle.run_recursive."""

    def test_run_recursive_single_converged_cycle(self):
        from sre.ai.hlrm_agent import HLRMAIAgent
        from sre.evidence.registry import EvidenceRegistry
        from sre.fra.reconstruction_engine import ChronologicalReconstruction
        from sre.substrate.fra_stage_runner import build_sre_governed_fra_cycle
        from fae.metrics.validation import get_validation_engine

        registry = EvidenceRegistry()
        agent = HLRMAIAgent(registry)
        engine = ChronologicalReconstruction(registry, agent)
        cycle = build_sre_governed_fra_cycle(
            engine,
            target_language="Mythar",
            time_period="Phase I",
            evidence_sources=["evid_myt_001", "evid_myt_002", "evid_rel_001"],
            max_fae_cycles=3,
        )
        contexts = cycle.run_recursive(max_cycles=3)
        assert len(contexts) >= 1
        assert cycle.runner.domain_result is not None
        assert cycle.runner.domain_result.get("status") == "COMPLETED"
        assert "recurse" in contexts[-1].metadata

        report = get_validation_engine().validate_cycle(cycle.cycle_id)
        by_name = {r.test_name: r for r in report.results}
        assert by_name["FAC-V2: Uncertainty Test"].passed
        assert by_name["FAC-V3: Calibration Test"].passed
        assert by_name["FAC-V4: Explanatory Power Test"].passed
        assert report.overall_passed

    def test_fra_composed_run_recursive(self):
        from sre.ai.hlrm_agent import HLRMAIAgent
        from sre.evidence.registry import EvidenceRegistry
        from sre.fra.reconstruction_engine import ChronologicalReconstruction

        registry = EvidenceRegistry()
        agent = HLRMAIAgent(registry)
        engine = ChronologicalReconstruction(registry, agent)
        composed = FRAComposedReconstruction(
            engine,
            drift_threshold=0.6,
            quality_gate=0.35,
            max_fae_cycles=2,
        )
        result = composed.run_recursive(
            "Mythar",
            "Phase I",
            ["evid_myt_001", "evid_myt_002", "evid_rel_001"],
            max_cycles=2,
        )
        assert isinstance(result, RecursiveCompositionResult)
        assert result.iterations >= 1
        assert result.domain_result.get("status") == "COMPLETED"
        assert "drift" in result.domain_result or "metrics" in result.domain_result
