"""FAE substrate integration tests (import boundary + evidence mirror)."""

from __future__ import annotations

from sre.evidence.models import ConstitutionalStatus
from sre.evidence.registry import EvidenceRegistry
from sre.substrate import (
    FAEEvidenceRegistry,
    FactualAlignmentEngine,
    create_fae,
    mirror_linguistic_evidence_to_fae,
    reset_fae,
    reset_fae_registry,
)


def setup_function() -> None:
    reset_fae()
    reset_fae_registry()


def test_fae_package_importable() -> None:
    import fae

    assert fae.__version__ == "1.0.0"
    engine = create_fae()
    assert isinstance(engine, FactualAlignmentEngine)
    assert isinstance(engine.registry, FAEEvidenceRegistry)


def test_substrate_reexports_fae() -> None:
    from sre.substrate import FAEMCRLRosettaEngine, FRACycle, DriftDetectionEngine

    assert FRACycle is not None
    assert DriftDetectionEngine is not None
    assert FAEMCRLRosettaEngine is not None


def test_mirror_accepted_evidence_into_fae() -> None:
    fae_reg = FAEEvidenceRegistry()
    registry = EvidenceRegistry(fae_registry=fae_reg)
    evidence = registry.add_evidence(
        {
            "evidence_id": "evid_fae_mirror_001",
            "evidence_type": "inscription",
            "source_reference": "Substrate Mirror Corpus",
            "content": {"text": "mirrored"},
            "submitted_by": "tester",
        }
    )
    assert registry.get_status(evidence.evidence_id) == ConstitutionalStatus.ACCEPTED
    report = registry.get_validation_report(evidence.evidence_id)
    assert report is not None
    assert report.report.get("fae_substrate", {}).get("evidence_id") == (
        f"fae:{evidence.evidence_id}"
    )
    mirrored = fae_reg.get(f"fae:{evidence.evidence_id}")
    assert mirrored is not None
    assert mirrored.content["content"]["text"] == "mirrored"


def test_mirror_helper_direct() -> None:
    fae_reg = FAEEvidenceRegistry()
    registry = EvidenceRegistry()
    linguistic = registry.add_evidence(
        {
            "evidence_id": "evid_fae_direct_001",
            "evidence_type": "inscription",
            "source_reference": "Direct Mirror",
            "content": {"lemma": "test"},
            "submitted_by": "tester",
        }
    )
    fae_ev = mirror_linguistic_evidence_to_fae(linguistic, fae_registry=fae_reg)
    assert fae_ev.id == f"fae:{linguistic.evidence_id}"
    assert fae_ev.verify_integrity()
