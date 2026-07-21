"""Smoke + vertical-slice integration tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sre.ai.analysis_modules import CognateDetector, LexicalAnalyzer, PhonologicalAnalyzer
from sre.ai.hlrm_agent import HLRMAIAgent
from sre.ai.sound_change import induce_sound_changes, levenshtein_align
from sre.corpus.loader import seed_registry_from_corpus
from sre.enterprise.config import HREnterpriseSystem
from sre.enterprise.deployment import DeploymentManager
from sre.enterprise.monitoring import MonitoringSystem
from sre.evidence.dantomax_client import DantomaxClient
from sre.evidence.models import (
    ConstitutionalStatus,
    ConstitutionalValidationResult,
    EvidenceType,
    LinguisticEvidence,
)
from sre.evidence.registry import EvidenceRegistry
from sre.fra.reconstruction_engine import ChronologicalReconstruction
from sre.fra.stages import FRAStages
from sre.governance.certificates import SovereignCertificate
from sre.governance.cih_service import FAECLanguageReconstructionService
from sre.mcrl.rosetta_engine import MCRLRosettaEngine
from sre.mcrl.temporal_mapping import TemporalMapping

ROOT = Path(__file__).resolve().parents[1]


def test_models_and_enums_exist() -> None:
    assert EvidenceType.INSCRIPTION.value == "inscription"
    assert ConstitutionalStatus.ACCEPTED.value == "accepted"
    assert LinguisticEvidence is not None
    assert ConstitutionalValidationResult is not None
    assert SovereignCertificate is not None
    assert TemporalMapping is not None


def test_evidence_registry_fac_e_and_fac_v() -> None:
    registry = EvidenceRegistry()
    evidence = registry.add_evidence(
        {
            "evidence_id": "evid_smoke_001",
            "evidence_type": "inscription",
            "source_reference": "Smoke Corpus",
            "content": {"text": "ok"},
            "submitted_by": "tester",
        }
    )
    assert registry.get_evidence(evidence.evidence_id) is evidence
    assert registry.get_status(evidence.evidence_id) == ConstitutionalStatus.ACCEPTED
    report = registry.get_validation_report(evidence.evidence_id)
    assert report is not None and report.is_valid

    empty = registry.validate_reconstruction("recon_empty")
    assert empty.is_valid is False
    assert any("FAC-V1" in c for c in empty.failed_checks)


def test_dantomax_real_attestations() -> None:
    client = DantomaxClient(signing_key="test-key")
    receipt = client.register_evidence(
        "evid_dmx_001",
        "a" * 64,
        {"failed_checks": [], "tags": ["FAC-E"]},
    )
    assert receipt["is_attested"] is True
    assert receipt["ledger_position"] == 0
    assert len(receipt["signature"]) == 64

    verified = client.verify_evidence("evid_dmx_001", "a" * 64)
    assert verified["is_verified"] is True

    bad = client.verify_evidence("evid_dmx_001", "b" * 64)
    assert bad["is_verified"] is False

    chain = client.get_provenance_chain("evid_dmx_001")
    assert len(chain) == 1
    assert chain[0]["event_type"] == "REGISTER"

    client.register_evidence("evid_dmx_002", "c" * 64, {"failed_checks": []})
    integrity = client.verify_ledger_integrity()
    assert integrity["ok"] is True
    assert integrity["length"] == 2


def test_registry_dantomax_integration() -> None:
    dmx = DantomaxClient(signing_key="registry-key")
    registry = EvidenceRegistry(dantomax_client=dmx)
    evidence = registry.add_evidence(
        {
            "evidence_id": "evid_dmx_reg",
            "evidence_type": "lexical_item",
            "source_reference": "Fortson 2010",
            "content": {"form": "pater", "meaning": "father"},
            "submitted_by": "tester",
        }
    )
    report = registry.get_validation_report(evidence.evidence_id)
    assert report is not None
    assert report.is_valid
    assert "dantomax" in report.report
    assert report.report["dantomax"]["is_attested"] is True
    verified = registry.verify_with_dantomax(evidence.evidence_id)
    assert verified is not None
    assert verified["is_verified"] is True


def test_fra_vertical_slice_phase_i() -> None:
    registry = EvidenceRegistry()
    agent = HLRMAIAgent(registry)
    engine = ChronologicalReconstruction(registry, agent)
    result = engine.reconstruct_language(
        "Mythar", "Phase I", ["evid_myt_001", "evid_myt_002", "evid_rel_001"]
    )
    assert result["status"] == "COMPLETED"
    assert result["fra_stage"] == "ARCHIVE"
    assert "drift" in result["metrics"]
    assert result["proto_language_model"]["primary"]["form"].startswith("*")


def test_sound_change_induction() -> None:
    align = levenshtein_align("pater", "padre")
    assert any(op == "sub" for op, _, _ in align)
    rules = induce_sound_changes(
        [("pater", "padre", "a", "b"), ("mater", "madre", "c", "d")],
        min_support=1,
    )
    assert rules
    assert any("→" in r["rule"] for r in rules)


def test_ai_analysis_modules_rule_based() -> None:
    registry = EvidenceRegistry()
    seeded = seed_registry_from_corpus(
        registry, evidence_ids=["evid_myt_002", "evid_rel_001", "evid_myt_102"]
    )
    assert LexicalAnalyzer().analyze(seeded)
    assert PhonologicalAnalyzer().analyze(seeded)
    assert CognateDetector().detect(seeded)
    agent = HLRMAIAgent(registry)
    analysis = agent.analyze_evidence_patterns(seeded)
    hyps = agent.predict_proto_forms(analysis)
    assert hyps["hypotheses"]
    assert hyps["hypotheses"][0]["evidence_links"]


def test_governance_cih_live() -> None:
    registry = EvidenceRegistry()
    cih = FAECLanguageReconstructionService(registry)
    registry.add_evidence(
        {
            "evidence_id": "evid_cih_ok",
            "evidence_type": "inscription",
            "source_reference": "CIH Corpus",
            "content": {"text": "ok"},
            "submitted_by": "tester",
        }
    )
    registered = cih.approve_reconstruction_project(
        {"project_id": "proj_smoke", "spec": {"target_language": "Mythar"}}
    )
    assert registered["status"] == "UNDER_REVIEW"
    assert registered["trace_id"]
    approved = cih.approve_reconstruction_project(
        {
            "project_id": "proj_smoke_ok",
            "spec": {
                "target_language": "Latin",
                "time_period": "Classical",
                "evidence_sources": ["evid_cih_ok"],
            },
        }
    )
    assert approved["status"] == "APPROVED"
    assert approved["certificate_id"]
    cert = SovereignCertificate(certificate_id="cert_x")
    assert cert.to_dict()["certificate_id"] == "cert_x"


def test_enterprise_stubs_mcrl_live() -> None:
    with pytest.raises(NotImplementedError):
        HREnterpriseSystem("config.yaml")
    with pytest.raises(NotImplementedError):
        DeploymentManager().plan("dev")
    with pytest.raises(NotImplementedError):
        MonitoringSystem().health()
    mapping = MCRLRosettaEngine().map_temporal([])
    assert mapping["valid"] is True
    assert TemporalMapping().validate() is True
    stages = FRAStages()
    assert stages.observe([])["evidence_count"] == 0


def test_ie_cognate_corpus_reconstruction() -> None:
    registry = EvidenceRegistry(dantomax_client=DantomaxClient(signing_key="ie-demo"))
    agent = HLRMAIAgent(registry)
    engine = ChronologicalReconstruction(registry, agent, corpus_path="ie")
    evidence_ids = [
        "evid_lat_pater",
        "evid_spa_padre",
        "evid_fra_pere",
        "evid_skt_pitar",
        "evid_lat_mater",
        "evid_spa_madre",
        "evid_fra_mere",
        "evid_skt_matar",
        "evid_lat_unus",
        "evid_spa_uno",
        "evid_fra_un",
        "evid_skt_eka",
        "evid_lat_oculus",
        "evid_spa_ojo",
        "evid_fra_oeil",
        "evid_skt_aksi",
        "evid_lat_ferre",
        "evid_spa_llevar",
        "evid_fra_porter",
        "evid_skt_bhar",
    ]
    result = engine.reconstruct_language("Romance", "Classical→Modern", evidence_ids)
    assert result["status"] == "COMPLETED", result
    forms = [h.get("form", "") for h in result["proto_language_model"].get("proto_forms", [])]
    assert any(
        any(stem in f for stem in ("PATER", "MATER", "OINOS", "OKW", "BHER")) for f in forms
    ), forms
    analysis = agent.analyze_evidence_patterns([registry.get_evidence(eid) for eid in evidence_ids])
    assert analysis["cognate_groups"]
    assert analysis["phonological_shifts"]
    # Induced rules should appear for Romance alignments
    induced = [s for s in analysis["phonological_shifts"] if s.get("source") == "induced"]
    assert induced, analysis["phonological_shifts"]
    # Dantomax attestations present on accepted evidence
    report = registry.get_validation_report("evid_lat_pater")
    assert report is not None and report.report.get("dantomax", {}).get("is_attested")


def test_ie_corpus_file_present() -> None:
    corpus_path = ROOT / "data" / "ie_cognate_mini_v01.json"
    data = json.loads(corpus_path.read_text(encoding="utf-8"))
    assert data["corpus_id"] == "ie_cognate_mini_v01"
    codes = {lang["code"] for lang in data["languages"]}
    assert {"LAT", "SPA", "FRA", "SKT", "PIE"} <= codes
    assert data.get("references")
    # Expanded sets present
    lat = next(lang for lang in data["languages"] if lang["code"] == "LAT")
    lat_ids = {e["evidence_id"] for per in lat["periods"] for e in per["evidence"]}
    assert "evid_lat_unus" in lat_ids
    assert "evid_lat_oculus" in lat_ids
    assert "evid_lat_ferre" in lat_ids
    corpus_path = ROOT / "data" / "fra_corpus_v01.json"
    data = json.loads(corpus_path.read_text(encoding="utf-8"))
    assert data["corpus_id"] == "fra_test_v01"
    myt = next(lang for lang in data["languages"] if lang["code"] == "MYT")
    rel = next(lang for lang in data["languages"] if lang["code"] == "REL")
    myt_periods = {p["name"] for p in myt["periods"]}
    rel_periods = {p["name"] for p in rel["periods"]}
    assert myt_periods == {"Phase I", "Phase II", "Phase III", "Phase IV"}
    assert rel_periods == {"Phase I", "Phase II", "Phase III", "Phase IV"}
    phase_i = next(p for p in myt["periods"] if p["name"] == "Phase I")
    ids = {e["evidence_id"] for e in phase_i["evidence"]}
    assert "evid_myt_001" in ids
    assert "evid_myt_002" in ids
    evid_001 = next(e for e in phase_i["evidence"] if e["evidence_id"] == "evid_myt_001")
    assert evid_001["text"] == "ma taru en"
    rel_i = next(p for p in rel["periods"] if p["name"] == "Phase I")
    assert rel_i["evidence"][0]["form"] == "mah"


def test_schemas_and_docs_exist() -> None:
    required = [
        "schemas/sovereign_certificate.schema.json",
        "schemas/governance_trace.schema.json",
        "docs/architecture/EvidenceRegistry.md",
        "docs/governance/CIH_Workflow.md",
        "docs/governance/GovernanceConsensusMap_v01.md",
        "docs/governance/PromotionPlan_v01.md",
        "docs/specs/openapi.yaml",
        "docs/specs/ConstitutionalSpecification_v01.md",
        "docs/specs/ConstitutionalLogging.md",
        "docs/specs/API_Contracts.md",
        "docs/specs/ConstitutionalPromotionGates.md",
        "docs/architecture/MytharGapFill.md",
        "README.md",
    ]
    for rel in required:
        assert (ROOT / rel).is_file(), f"missing {rel}"
