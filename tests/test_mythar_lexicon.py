"""Mythar living lexicon tests — clusters 12–95 + gap-fill + PGC."""

from __future__ import annotations

from pathlib import Path

from sre.ai.hlrm_agent import HLRMAIAgent
from sre.evidence.dantomax_client import DantomaxClient
from sre.evidence.models import ConstitutionalStatus
from sre.evidence.registry import EvidenceRegistry
from sre.fra.reconstruction_engine import ChronologicalReconstruction
from sre.mythar import MytharLexicon
from sre.mythar.data import ALLOWED_POLYSEMY, PGC_CONTRACT, PGC_CORRECTIONS, build_lexicon_document
from sre.mythar.governance import (
    ASSURANCE_LEVELS,
    LIFECYCLE_STATES,
    validate_governance_record,
)

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
    assert ids == list(range(12, 96))
    assert len(ids) == 84
    assert lex.get_cluster(12) is not None
    assert lex.get_cluster(80) is not None
    assert lex.get_cluster(81) is not None
    assert lex.get_cluster(87) is not None
    assert lex.get_cluster(88) is not None
    assert lex.get_cluster(94) is not None
    assert lex.get_cluster(95) is not None
    listed = lex.list_clusters()
    assert any(c["cluster_id"] == 81 for c in listed)
    assert any(c["cluster_id"] == 95 for c in listed)

    c81 = lex.get_cluster(81)
    assert c81 is not None
    assert c81["forms"] == ["pa", "ne", "ti"]

    c83 = lex.get_cluster(83)
    assert c83 is not None
    assert c83["forms"] == ["fi", "wa", "hi"]

    c85 = lex.get_cluster(85)
    assert c85 is not None
    assert c85["forms"] == ["su", "pu", "ya"]

    c88 = lex.get_cluster(88)
    assert c88 is not None
    assert c88["forms"] == ["chi", "ma", "loi"]

    c94 = lex.get_cluster(94)
    assert c94 is not None
    assert "rama" in c94["forms"]

    c95 = lex.get_cluster(95)
    assert c95 is not None
    assert c95["forms"] == ["pu", "hu", "duma"]

    for root in (
        "ma",
        "pa",
        "ti",
        "chi",
        "loi",
        "sha",
        "sa",
        "rama",
        "ko",
        "peh",
        "dak",
        "toh",
        "tek",
        "nuka",
        "sola",
        "luna",
        "fe",
        "krato",
        "bura",
        "tem",
        "reka",
        "ver",
        "never",
        "lo",
        "alo",
        "dunu",
        "tima",
        "sura",
        "nema",
        "ke",
        "in",
        "ex",
        "duta",
        "neta",
        "da",
        "hu",
        "am",
        "no",
        "du",
        "duma",
        "taga",
        "me",
        "mica",
        "ska",
        "ula",
        "fi",
        "yafora",
        "makyo",
    ):
        assert root in lex.root_forms(), root
    assert domains_covered(lex)
    inv = lex.gap_fill()["invocation"]
    assert "Pa ne ti" in inv
    assert "Fi wa hi" in inv
    assert "Su pu ya" in inv
    assert "Chi ma loi" in inv
    assert "Sola luna fe" in inv
    assert "Pu hu duma" in inv
    assert "Ye kra ro ya" in inv


def test_mythar_pgc_contract() -> None:
    doc = build_lexicon_document()
    assert doc["lexicon_version"] == "1.3"
    pgc = doc["polysemy_governance"]
    assert len(pgc["contract"]) == 5
    assert {c["id"] for c in PGC_CONTRACT} == {"PGC-1", "PGC-2", "PGC-3", "PGC-4", "PGC-5"}
    assert {c["form"] for c in PGC_CORRECTIONS} == {"to", "ta", "du"}

    by_form = {r["form"]: r for r in doc["roots"]}
    for entry in ALLOWED_POLYSEMY:
        form = str(entry["form"])
        root = by_form[form]
        assert "polysemy" in root, form
        assert root["polysemy"]["axis"] == entry["axis"]

    assert "stone" not in " ".join(by_form["to"]["polysemy"]["senses"]).lower()
    assert "two" not in " ".join(by_form["du"]["polysemy"]["senses"]).lower()
    assert by_form["ta"]["polysemy"]["senses"] == ["this / that (demonstrative)"]
    assert "duma" in by_form
    assert "taga" in by_form
    assert "ska" in by_form

    lex = MytharLexicon(LEX_PATH)
    assert lex.raw.get("lexicon_version") == "1.3"
    assert "polysemy_governance" in lex.raw


def test_mythar_cra_governance_fields() -> None:
    doc = build_lexicon_document()
    model = doc["cra_governance_model"]
    assert model["schema"] == "mythar.cra_governance.v1"
    assert model["expansion_policy"]["status"] == "frozen"
    assert set(model["assurance_levels"]) == set(ASSURANCE_LEVELS)
    assert set(model["lifecycle_states"]) == set(LIFECYCLE_STATES)

    for root in doc["roots"]:
        gov = root["cra_governance"]
        assert validate_governance_record(gov) == [], root["form"]
        assert gov["identity"] == f"mythar:root:{root['form']}"
        assert gov["cel_lineage"]["subject_id"] == root["evidence_id"]
        assert gov["cel_lineage"]["binding_status"] == "deferred"
        assert gov["assurance_level"] in ASSURANCE_LEVELS
        assert gov["lifecycle_state"] in LIFECYCLE_STATES

    for cluster in doc["clusters"]:
        gov = cluster["cra_governance"]
        assert validate_governance_record(gov) == [], cluster["cluster_id"]
        assert gov["identity"] == f"mythar:cluster:{int(cluster['cluster_id']):02d}"
        assert gov["cel_lineage"]["subject_id"] == cluster["evidence_id"]

    by_form = {r["form"]: r for r in doc["roots"]}
    # PGC-stable polysemy → validated / Active
    assert by_form["ma"]["cra_governance"]["assurance_level"] == "validated"
    assert by_form["ma"]["cra_governance"]["lifecycle_state"] == "Active"
    # PGC v1.3 corrections carry revision history
    for form in ("to", "ta", "du", "duma", "ska", "taga"):
        hist = by_form[form]["cra_governance"]["revision_history"]
        assert hist, form
        assert hist[0]["version"] == "1.3"
        assert by_form[form]["cra_governance"]["assurance_level"] == "validated"

    # Proposal L candidate (non-PGC-split)
    assert by_form["chi"]["cra_governance"]["assurance_level"] == "candidate"
    assert by_form["chi"]["cra_governance"]["lifecycle_state"] == "Review"

    by_cid = {int(c["cluster_id"]): c for c in doc["clusters"]}
    assert by_cid[12]["cra_governance"]["assurance_level"] == "validated"
    assert by_cid[12]["cra_governance"]["lifecycle_state"] == "Active"
    assert by_cid[47]["cra_governance"]["assurance_level"] == "validated"
    assert by_cid[81]["cra_governance"]["assurance_level"] == "candidate"
    assert by_cid[88]["cra_governance"]["lifecycle_state"] == "Review"
    assert by_cid[95]["cra_governance"]["assurance_level"] == "candidate"
    assert by_cid[95]["cra_governance"]["revision_history"]

    lex = MytharLexicon(LEX_PATH)
    assert "cra_governance_model" in lex.raw
    assert all("cra_governance" in r for r in lex.roots())
    assert all("cra_governance" in c for c in lex.clusters())


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
    assert any(r["mythar"] == "duma" for r in rows)


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
        "evid_myt_cluster_95",
        "evid_myt_root_ma",
        "evid_myt_root_chi",
        "evid_myt_root_rama",
        "evid_myt_root_sola",
        "evid_myt_root_ver",
        "evid_myt_root_duma",
    ):
        ev = registry.get_evidence(eid)
        assert ev is not None, eid
        assert registry.get_status(eid) == ConstitutionalStatus.ACCEPTED

    evidence_ids = [
        "evid_myt_cluster_12",
        "evid_myt_cluster_81",
        "evid_myt_cluster_83",
        "evid_myt_cluster_88",
        "evid_myt_cluster_95",
        "evid_myt_root_pa",
        "evid_myt_root_ma",
        "evid_myt_root_fi",
        "evid_myt_root_chi",
        "evid_myt_root_duma",
    ]
    engine = ChronologicalReconstruction(registry, HLRMAIAgent(registry), corpus_path="mythar-lex")
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
