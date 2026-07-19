#!/usr/bin/env python3
"""FRA reconstruction demos — Mythar (synthetic) or IE cognate mini-corpus."""

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
from sre.fra.reconstruction_engine import ChronologicalReconstruction
from sre.governance.cih_service import FAECLanguageReconstructionService


PRESETS = {
    "mythar": {
        "corpus": "mythar",
        "target_language": "Mythar",
        "time_period": "Phase I",
        "evidence_ids": ["evid_myt_001", "evid_myt_002", "evid_rel_001"],
    },
    "ie": {
        "corpus": "ie",
        "target_language": "Proto-Indo-European",
        "time_period": "Classical→Modern",
        "evidence_ids": [
            # kin
            "evid_lat_pater",
            "evid_spa_padre",
            "evid_fra_pere",
            "evid_skt_pitar",
            "evid_lat_mater",
            "evid_spa_madre",
            "evid_fra_mere",
            "evid_skt_matar",
            # numbers
            "evid_lat_unus",
            "evid_spa_uno",
            "evid_fra_un",
            "evid_skt_eka",
            "evid_lat_duo",
            "evid_spa_dos",
            "evid_fra_deux",
            "evid_skt_dva",
            # body
            "evid_lat_oculus",
            "evid_spa_ojo",
            "evid_fra_oeil",
            "evid_skt_aksi",
            "evid_lat_dens",
            "evid_spa_diente",
            "evid_fra_dent",
            "evid_skt_dant",
            # verbs
            "evid_lat_ferre",
            "evid_spa_llevar",
            "evid_fra_porter",
            "evid_skt_bhar",
            "evid_lat_edere",
            "evid_spa_comer",
            "evid_fra_manger",
            "evid_skt_ad",
            # PIE rules
            "evid_pie_phter",
            "evid_pie_mehter",
            "evid_pie_oynos",
            "evid_pie_bher",
        ],
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(description="SRE reconstruction demo")
    parser.add_argument(
        "--corpus",
        choices=sorted(PRESETS.keys()),
        default="mythar",
        help="mythar (synthetic) or ie (Latin/Romance/Sanskrit mini-set)",
    )
    parser.add_argument(
        "--with-cih",
        action="store_true",
        help="Run CIH approval and attach Sovereign Certificate",
    )
    parser.add_argument(
        "--dantomax",
        action="store_true",
        help="Attach local Dantomax attestation ledger to EvidenceRegistry",
    )
    args = parser.parse_args()
    preset = PRESETS[args.corpus]

    dantomax = DantomaxClient() if args.dantomax else None
    registry = EvidenceRegistry(dantomax_client=dantomax)
    agent = HLRMAIAgent(registry)
    engine = ChronologicalReconstruction(
        registry, agent, corpus_path=preset["corpus"]
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
            "integrity": dantomax.verify_ledger_integrity(),
        }

    if args.with_cih and result.get("status") == "COMPLETED":
        cih = FAECLanguageReconstructionService(registry)
        approval = cih.approve_reconstruction_project(
            {
                "project_id": f"proj_{args.corpus}_demo",
                "spec": {
                    "target_language": preset["target_language"],
                    "time_period": preset["time_period"],
                    "evidence_sources": list(preset["evidence_ids"]),
                    "reconstruction_id": result.get("reconstruction_id"),
                },
            }
        )
        result["cih"] = {
            "status": approval.get("status"),
            "certificate_id": approval.get("certificate_id"),
            "trace_id": approval.get("trace_id"),
        }

    print(json.dumps(result, indent=2, default=str))
    print(
        f"\n# corpus={args.corpus} known_ids={len(list_evidence_ids(preset['corpus']))}",
        file=sys.stderr,
    )
    return 0 if result.get("status") == "COMPLETED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
