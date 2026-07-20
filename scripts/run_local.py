#!/usr/bin/env python3
"""FRA reconstruction demos — Mythar, IE mini, or IE expanded + Dantomax lineage."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sre.ai.hlrm_agent import HLRMAIAgent
from sre.corpus.loader import list_evidence_ids
from sre.evidence.dantomax_client import DantomaxClient
from sre.evidence.registry import EvidenceRegistry
from sre.fra.reconstruction_engine import ChronologicalReconstruction, RULE_SET_VERSION
from sre.governance.cih_service import FAECLanguageReconstructionService
from sre.linguistics.lineage import format_human_lineage


def _all_ids(corpus_key: str) -> list[str]:
    return list_evidence_ids(corpus_key)


def _expanded_demo_ids() -> list[str]:
    """Representative slice covering numbers, body, verbs across branches."""
    lemmas = [
        "one",
        "two",
        "three",
        "five",
        "ten",
        "eye",
        "tooth",
        "knee",
        "bone",
        "blood",
        "be",
        "bear",
        "give",
        "know",
        "eat",
        "drink",
        "come",
        "stand",
        "father",
        "nine",  # analogy-flagged Balto-Slavic
    ]
    langs = ["lat", "grc", "skt", "got", "sga", "cu", "lit", "hit", "txb", "pie"]
    ids: list[str] = []
    available = set(_all_ids("ie-expanded"))
    for lemma in lemmas:
        for lang in langs:
            eid = f"evid_{lang}_{lemma}"
            if eid in available:
                ids.append(eid)
    # Explicit sound-change rules
    for rid in (
        "evid_pie_rule_grimm",
        "evid_pie_rule_centum",
        "evid_pie_rule_satem",
    ):
        if rid in available:
            ids.append(rid)
    return ids


PRESETS = {
    "mythar": {
        "corpus": "mythar",
        "target_language": "Mythar",
        "time_period": "Phase I",
        "evidence_ids": ["evid_myt_001", "evid_myt_002", "evid_rel_001"],
    },
    "mythar-lex": {
        "corpus": "mythar-lex",
        "target_language": "Mythar",
        "time_period": "Living Lexicon",
        "evidence_ids": [
            "evid_myt_cluster_12",
            "evid_myt_cluster_13",
            "evid_myt_cluster_14",
            "evid_myt_cluster_15",
            "evid_myt_cluster_16",
            "evid_myt_cluster_17",
            "evid_myt_cluster_26",
            "evid_myt_cluster_40",
            "evid_myt_cluster_46",
            "evid_myt_root_pa",
            "evid_myt_root_ma",
            "evid_myt_root_ti",
            "evid_myt_root_wa",
            "evid_myt_root_wi",
            "evid_myt_root_bro",
        ],
    },
    "ie": {
        "corpus": "ie",
        "target_language": "Proto-Indo-European",
        "time_period": "Classical→Modern",
        "evidence_ids": [
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
            "evid_lat_duo",
            "evid_spa_dos",
            "evid_fra_deux",
            "evid_skt_dva",
            "evid_lat_oculus",
            "evid_spa_ojo",
            "evid_fra_oeil",
            "evid_skt_aksi",
            "evid_lat_dens",
            "evid_spa_diente",
            "evid_fra_dent",
            "evid_skt_dant",
            "evid_lat_ferre",
            "evid_spa_llevar",
            "evid_fra_porter",
            "evid_skt_bhar",
            "evid_lat_edere",
            "evid_spa_comer",
            "evid_fra_manger",
            "evid_skt_ad",
            "evid_pie_phter",
            "evid_pie_mehter",
            "evid_pie_oynos",
            "evid_pie_bher",
        ],
    },
    "ie-expanded": {
        "corpus": "ie-expanded",
        "target_language": "Proto-Indo-European",
        "time_period": "IE comparative (expanded)",
        "evidence_ids": None,  # filled at runtime
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(description="SRE reconstruction demo")
    parser.add_argument(
        "--corpus",
        choices=sorted(PRESETS.keys()),
        default="mythar",
        help="mythar | mythar-lex | ie | ie-expanded",
    )
    parser.add_argument(
        "--with-cih",
        action="store_true",
        help="Run CIH approval and attach Sovereign Certificate",
    )
    parser.add_argument(
        "--dantomax",
        "--with-dantomax",
        dest="dantomax",
        action="store_true",
        help="Attach local Dantomax attestation ledger to EvidenceRegistry",
    )
    parser.add_argument(
        "--show-lineage",
        action="store_true",
        help="Print human-readable attestation→certification lineage",
    )
    parser.add_argument(
        "--show-cel",
        action="store_true",
        help="Print Constitutional Evidence Ledger (CEL) summary",
    )
    args = parser.parse_args()
    preset = dict(PRESETS[args.corpus])
    if preset.get("evidence_ids") is None:
        preset["evidence_ids"] = _expanded_demo_ids()

    # Expanded corpus defaults to Dantomax when lineage/CIH requested
    use_dantomax = args.dantomax or (
        args.corpus == "ie-expanded" and (args.with_cih or args.show_lineage)
    )
    if args.corpus == "ie-expanded":
        use_dantomax = True

    dantomax = DantomaxClient() if use_dantomax else None
    registry = EvidenceRegistry(dantomax_client=dantomax)
    agent = HLRMAIAgent(registry)
    engine = ChronologicalReconstruction(
        registry,
        agent,
        corpus_path=preset["corpus"],
        constraints={
            "require_attestation_lineage": args.corpus == "ie-expanded",
        },
    )
    result = engine.reconstruct_language(
        preset["target_language"],
        preset["time_period"],
        list(preset["evidence_ids"]),
    )

    if dantomax is not None:
        result["dantomax"] = {
            "ledger_length": dantomax.ledger_length,
            "ledger_head": dantomax.ledger_head,
            "attestation_root_hash": dantomax.attestation_root_hash,
            "integrity": dantomax.verify_ledger_integrity(),
            "governance_events": len(dantomax.governance_events()),
        }
        if registry.cel is not None:
            result["cel"] = {
                **registry.cel.summary(),
                "integrity": registry.cel.verify_integrity(),
            }

    if args.with_cih and result.get("status") == "COMPLETED":
        cert = result.get("certificate") or {}
        att_ids = list(
            ((result.get("governance") or {}).get("attestation_ids"))
            or []
        )
        cih = FAECLanguageReconstructionService(registry)
        approval = cih.approve_reconstruction_project(
            {
                "project_id": f"proj_{args.corpus}_demo".replace("-", "_"),
                "spec": {
                    "target_language": preset["target_language"],
                    "time_period": preset["time_period"],
                    "evidence_sources": list(preset["evidence_ids"]),
                    "reconstruction_id": result.get("reconstruction_id"),
                    "reconstruction_ids": cert.get("reconstruction_ids")
                    or [result.get("reconstruction_id")],
                    "attestation_ids": att_ids,
                    "require_attestation_lineage": bool(att_ids),
                    "corpus_hash": cert.get("corpus_hash"),
                    "attestation_root_hash": cert.get("attestation_root_hash"),
                    "rule_set_version": cert.get("rule_set_version") or RULE_SET_VERSION,
                    "validation_summary": cert.get("validation_summary")
                    or (result.get("validation") or {}),
                },
            }
        )
        result["cih"] = {
            "status": approval.get("status"),
            "certificate_id": approval.get("certificate_id"),
            "trace_id": approval.get("trace_id"),
            "certificate": (approval.get("certificate") or {}),
        }

    # Compact JSON for readability when lineage is shown separately
    print(json.dumps(result, indent=2, default=str))

    if args.show_lineage:
        human = result.get("human_lineage") or format_human_lineage(
            result.get("lineage") or {}
        )
        print("\n=== EVIDENCE LINEAGE ===", file=sys.stderr)
        print(human, file=sys.stderr)
        corr = result.get("correspondence_search") or {}
        print(
            f"\n# ambiguous_sets={corr.get('ambiguous_sets')} "
            f"flagged={corr.get('flagged_irregular')} "
            f"loo={len(corr.get('leave_one_out_examples') or [])}",
            file=sys.stderr,
        )

    if args.show_cel and registry.cel is not None:
        summary = registry.cel.summary()
        print("\n=== CONSTITUTIONAL EVIDENCE LEDGER ===", file=sys.stderr)
        print(json.dumps(summary, indent=2), file=sys.stderr)
        recon_id = result.get("reconstruction_id")
        if recon_id:
            lineage = registry.cel.query_lineage(str(recon_id))
            print(f"\nCEL lineage ({recon_id}):", file=sys.stderr)
            print(lineage.get("human_readable", ""), file=sys.stderr)

    print(
        f"\n# corpus={args.corpus} known_ids={len(list_evidence_ids(preset['corpus']))} "
        f"rule_set={RULE_SET_VERSION}",
        file=sys.stderr,
    )
    return 0 if result.get("status") == "COMPLETED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
