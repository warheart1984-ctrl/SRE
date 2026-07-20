"""Mythar living lexicon tests — clusters 12–94 + gap-fill."""

from __future__ import annotations

from pathlib import Path

from sre.evidence.models import ConstitutionalStatus
from sre.evidence.registry import EvidenceRegistry
from sre.evidence.dantomax_client import DantomaxClient
from sre.fra.reconstruction_engine import ChronologicalReconstruction
from sre.ai.hlrm_agent import HLRMAIAgent
from sre.mythar import MytharLexicon

ROOT = Path(__file__).resolve().parents[1]
LEX_PATH = ROOT / "data" / "mythar_lexicon_v01.json"


def domains_covered(lex: MytharLexicon) -> bool:
    report = lex.gap_fill()
    return all(d["cluster_count"] >= 5 for d in report["domains"])


def _content_meta(ev) -> dict:
    return dict((ev.content or {}).get("metadata") or {})


def test_mythar_lexicon_file_and_counts() -> None:
    lex = MytharLexicon(LEX_PATH)
    assert lex.lexicon_id == "mythar_lexicon_v01"
    assert LEX_PATH.is_file()
    ids = lex.cluster_ids()
    assert ids == list(range(12, 95))
    assert len(ids) == 83
    assert lex.get_cluster(12) is not None
    assert lex.get_cluster(80) is not None
    assert lex.get_cluster(81) is not None
    assert lex.get_cluster(87) is not None
    assert lex.get_cluster(88) is not None
    assert lex.get_cluster(94) is not None
    listed = lex.list_clusters()
    assert any(c["cluster_id"] == 81 for c in listed)
    assert any(c["cluster_id"] == 94 for c in listed)

    c81 = lex.get_cluster(81)
    assert c81 is not None
    assert c81["forms"] == ["pa", "ne", "ti"]

    c83 = lex.get_cluster(83)
    assert c83 is not None
    assert c83["forms"] == ["fi", "wa", "hi"]

    c88 = lex.get_cluster(88)
    assert c88 is not None
    assert c88["forms"] == ["chi", "ma", "loi"]

    c94 = lex.get_cluster(94)
    assert c94 is not None
    assert "rama" in c94["forms"]

    for root in (
        "ma", "pa", "ti", "chi", "loi", "sha", "sa", "rama", "ko",
        "peh", "dak", "toh", "tek", "nuka", "sola", "luna", "fe",
        "krato", "bura", "tem", "reka", "ver", "never", "lo", "dunu",
        "tima", "sura", "nema", "ke", "in", "ex", "duta", "neta",
        "da", "hu", "am", "no", "du", "me", "mica", "ska", "ula",
        "fi", "yafora", "makyo",
    ):
        assert root in lex.root_forms(), root
    assert domains_covered(lex)
    inv = lex.gap_fill()["invocation"]
    assert "Pa ne ti" in inv
    assert "Fi wa hi" in inv
    assert "Chi ma loi" in inv
    assert "Sola luna fe" in inv
    assert "Ye kra ro ya" in inv


def test_mythar_gap_fill_domains() -> None:
    lex = MytharLexicon(LEX_PATH)
    report = lex.gap_fill()
    assert report["mode"] == "gap_fill"
    domains = {d["domain"]: d for d in report["domains"]}
    for name in ("kinship", "body", "motion", "abstract", "nature"):
        assert name in domains
        assert domains[name]["cluster_count"] >= 5
        assert domains[name]["status"] in {"covered", "thin", "ok"}
    assert domains["abstract"]["cluster_count"] >= 20


def test_mythar_proto_world_table() -> None:
    rows = MytharLexicon(LEX_PATH).compare_proto_world()
    assert any(r["mythar"] == "pa" for r in rows)
    assert any(r["mythar"] == "chi" for r in rows)
    assert any(r["mythar"] == "sola" for r in rows)
    assert any(r["mythar"] == "ver" for r in rows)
    assert any(r["mythar"] == "in" for r in rows)


def test_mythar_seed_and_reconstruct_clusters() -> None:
    lex = MytharLexicon(LEX_PATH)
    registry = EvidenceRegistry()
    seeded = lex.seed_registry(registry)
    assert seeded
    for eid in (
        "evid_myt_cluster_12",
        "evid_myt_cluster_81",
        "evid_myt_cluster_88",
        "evid_myt_cluster_94",
        "evid_myt_root_ma",
        "evid_myt_root_chi",
        "evid_myt_root_rama",
        "evid_myt_root_sola",
        "evid_myt_root_ver",
    ):
        ev = registry.get_evidence(eid)
        assert ev is not None, eid
        assert registry.get_status(eid) == ConstitutionalStatus.ACCEPTED

    evidence_ids = [
        "evid_myt_cluster_12",
        "evid_myt_cluster_81",
        "evid_myt_cluster_83",
        "evid_myt_cluster_88",
        "evid_myt_root_pa",
        "evid_myt_root_ma",
        "evid_myt_root_fi",
        "evid_myt_root_chi",
    ]
    engine = ChronologicalReconstruction(
        registry, HLRMAIAgent(registry), corpus_path="mythar-lex"
    )
    result = engine.reconstruct_language("Mythar", "Living Lexicon", evidence_ids)
    assert result["status"] == "COMPLETED", result


def test_mythar_compound_clusters_dantomax_attestation() -> None:
    lex = MytharLexicon(LEX_PATH)
    dmx = DantomaxClient(signing_key="mythar-cluster47-48-test")
    registry = EvidenceRegistry(dantomax_client=dmx)
    lex.seed_registry(registry)

    for eid in ("evid_myt_cluster_47", "evid_myt_cluster_48"):
        ev = registry.get_evidence(eid)
        assert ev is not None
        assert registry.get_status(eid) == ConstitutionalStatus.ACCEPTED
        meta = _content_meta(ev)
        assert "provenance_note" in meta
        verified = registry.verify_with_dantomax(eid)
        assert verified is not None
        assert verified.get("is_verified") is True or verified.get("is_attested") is True

    for compound_id in (
        "evid_myt_compound_yuckara",
        "evid_myt_compound_yocfua_ro",
        "evid_myt_compound_manalara_ya",
    ):
        compound = registry.get_evidence(compound_id)
        assert compound is not None, compound_id
        c_verified = registry.verify_with_dantomax(compound_id)
        assert c_verified is not None
        assert c_verified.get("is_verified") is True
