"""ChronologicalReconstruction — FRA engine (attestation + correspondence slice)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..corpus.attest import (
    collect_attestation_ids,
    evidence_flags_by_lang,
    seed_attestations_from_evidence,
)
from ..corpus.loader import resolve_corpus_path, seed_registry_from_corpus
from ..linguistics.correspondence_engine import CorrespondenceEngine
from ..linguistics.lineage import format_human_lineage
from ..mcrl.rosetta_engine import MCRLRosettaEngine
from .stages import FRAStages

if TYPE_CHECKING:
    from ..ai.hlrm_agent import HLRMAIAgent
    from ..evidence.registry import EvidenceRegistry

RULE_SET_VERSION = "correspondence_engine_v01"


class ChronologicalReconstruction:
    """
    FRA Engine — constitutional pipeline:

    OBSERVE → INGEST → ATTEST → ALIGN → CLUSTER → INFER → VALIDATE → GOVERN → CERTIFY → ARCHIVE
    """

    def __init__(
        self,
        evidence_registry: EvidenceRegistry,
        ai_agent: HLRMAIAgent | None = None,
        *,
        constraints: dict[str, Any] | None = None,
        rosetta: MCRLRosettaEngine | None = None,
        corpus_path: str | None = None,
        correspondence_engine: CorrespondenceEngine | None = None,
    ) -> None:
        self.evidence_registry = evidence_registry
        self.ai_agent = ai_agent
        self.corpus_path = corpus_path
        self.constraints = {
            "max_iterations": 5,
            "drift_threshold": 0.6,
            "evidence_min_count": 1,
            "quality_gate": 0.35,
            "require_drift_metrics": True,
            "require_attestation_lineage": False,
            **(constraints or {}),
        }
        self.stages = FRAStages()
        self.rosetta = rosetta or MCRLRosettaEngine()
        self.correspondence = correspondence_engine or CorrespondenceEngine()

    def reconstruct_language(
        self,
        target_language: str,
        time_period: str,
        evidence_sources: list[str],
    ) -> dict:
        """Wire to POST /api/v1/reconstruction — returns ReconstructionDetail-shaped dict."""
        stages_completed: list[str] = []
        dantomax = getattr(self.evidence_registry, "_dantomax", None)
        cel = getattr(self.evidence_registry, "cel", None)

        if not evidence_sources:
            return {
                "reconstruction_id": None,
                "status": "FAILED",
                "fra_stage": "OBSERVE",
                "reason": "FRA-02: empty evidence list",
                "stages_completed": [],
                "metrics": {},
            }

        seed_registry_from_corpus(
            self.evidence_registry,
            path=self.corpus_path,
            evidence_ids=list(evidence_sources),
            search_catalog=True,
        )

        evidence_list = []
        missing = []
        for eid in evidence_sources:
            ev = self.evidence_registry.get_evidence(eid)
            if ev is None:
                missing.append(eid)
            else:
                evidence_list.append(ev)

        if missing or not evidence_list:
            return {
                "reconstruction_id": None,
                "status": "FAILED",
                "fra_stage": "OBSERVE",
                "reason": f"missing evidence: {missing}",
                "stages_completed": [],
                "metrics": {},
            }

        if self.ai_agent is None:
            from ..ai.hlrm_agent import HLRMAIAgent

            self.ai_agent = HLRMAIAgent(self.evidence_registry, config={})

        # 1. OBSERVE
        observed = self.stages.observe(evidence_list)
        stages_completed.append("OBSERVE")

        # 2. INGEST
        ingested = self.stages.ingest(evidence_list)
        stages_completed.append("INGEST")

        # 3. ATTEST
        attestation_ids = collect_attestation_ids(evidence_list)
        if dantomax is not None:
            att_summary = seed_attestations_from_evidence(
                dantomax, evidence_list, cel=cel
            )
            # Auto-approve active attestations for demo governance path
            for aid in att_summary.get("registered") or []:
                try:
                    dantomax.approve_attestation(aid)
                except ValueError:
                    pass
            attestation_ids = collect_attestation_ids(evidence_list) or list(
                att_summary.get("registered") or []
            )
            if att_summary.get("errors"):
                return {
                    "reconstruction_id": None,
                    "status": "FAILED",
                    "fra_stage": "ATTEST",
                    "reason": f"attestation errors: {att_summary['errors']}",
                    "stages_completed": stages_completed + ["ATTEST"],
                    "metrics": {"attest": att_summary},
                }
        else:
            att_summary = {
                "registered": [],
                "skipped_duplicates": [],
                "errors": [],
                "count": 0,
                "note": "dantomax_not_attached",
            }
        attest_out = self.stages.attest(att_summary)
        stages_completed.append("ATTEST")

        # Analysis (feeds ALIGN / CLUSTER / INFER)
        analysis = self.ai_agent.analyze_evidence_patterns(evidence_list)
        flags_by_lang = evidence_flags_by_lang(evidence_list)
        corr_payload = self._run_correspondence_search(
            analysis, evidence_list, attestation_ids, flags_by_lang
        )
        if cel is not None:
            for hyp in corr_payload.get("hypotheses") or []:
                gid = str(hyp.get("cognate_set_id") or "cog")
                cel.record_correspondence(
                    gid,
                    {
                        "proto_form": hyp.get("proto_form"),
                        "confidence": hyp.get("confidence"),
                        "correspondence_sets": hyp.get("correspondence_sets"),
                        "flags": hyp.get("flags"),
                        "competing_hypotheses": hyp.get("competing_hypotheses"),
                    },
                    links=list(hyp.get("supporting_attestations") or []),
                )

        # 4. ALIGN
        temporal_map = self.rosetta.map_temporal(evidence_list)
        aligned = self.stages.align(
            None,
            temporal_map,
            correspondence_report=corr_payload.get("alignment_report"),
        )
        stages_completed.append("ALIGN")

        # 5. CLUSTER
        clustered = self.stages.cluster(analysis)
        stages_completed.append("CLUSTER")

        # 6. INFER
        hypotheses = self.ai_agent.predict_proto_forms(analysis)
        # Merge correspondence-ranked hypotheses
        if corr_payload.get("hypotheses"):
            hypotheses = self._merge_hypotheses(hypotheses, corr_payload["hypotheses"])
        proto_model = self.stages.infer(
            hypotheses,
            target_language,
            time_period,
            correspondence_hypotheses=corr_payload.get("hypotheses"),
        )
        # Progressive refinement (kept as INFER sub-step for FRA-04 compatibility)
        needs_extra = True
        test_result = self.stages.test(proto_model, evidence_list)
        drift = float(test_result.get("drift", 1.0))
        quality = float(test_result.get("quality", 0.0))
        threshold = float(self.constraints["drift_threshold"])
        quality_gate = float(self.constraints["quality_gate"])
        needs_extra = drift > threshold or quality < quality_gate
        max_iterations = int(self.constraints["max_iterations"]) if needs_extra else 1
        refine_out = self.stages.refine(
            proto_model,
            analysis,
            self.ai_agent,
            max_iterations=max_iterations,
            quality_gate=quality_gate,
        )
        proto_model = refine_out["proto_model"]
        proto_model["correspondence_hypotheses"] = corr_payload.get("hypotheses") or []
        test_result = self.stages.test(proto_model, evidence_list)
        drift = float(test_result.get("drift", drift))
        quality = float(refine_out.get("quality", quality))
        stages_completed.append("INFER")

        if self.constraints.get("require_drift_metrics") and "drift" not in test_result:
            return {
                "reconstruction_id": proto_model.get("id"),
                "status": "FAILED",
                "fra_stage": "INFER",
                "reason": "FRA-03: drift metrics required",
                "stages_completed": stages_completed,
                "metrics": test_result,
            }

        # Attach attestation links onto proto forms
        for hyp in proto_model.get("proto_forms") or []:
            hyp.setdefault("attestation_ids", list(attestation_ids))
        if proto_model.get("primary"):
            proto_model["primary"].setdefault("attestation_ids", list(attestation_ids))

        metrics = {
            "drift": drift,
            "coverage": float(test_result.get("coverage", 0.0)),
            "quality": quality,
            "consistency": float(test_result.get("coverage", 0.0)),
            "evidence_count": len(evidence_list),
            "observe": observed,
            "ingest": ingested,
            "attest": attest_out,
            "align": aligned,
            "cluster_summary": {
                "clusters": len(clustered.get("lexical_clusters") or []),
                "cognates": len(clustered.get("cognate_groups") or []),
                "shifts": len(clustered.get("phonological_shifts") or []),
            },
            "aligned": aligned.get("aligned", False),
            "correspondence": {
                "hypothesis_count": len(corr_payload.get("hypotheses") or []),
                "ambiguous_sets": corr_payload.get("ambiguous_sets") or [],
                "flagged_irregular": corr_payload.get("flagged_irregular") or [],
                "leave_one_out": corr_payload.get("leave_one_out_examples") or [],
            },
        }

        recon_id = str(proto_model.get("id"))
        if cel is not None:
            cel.record_hypothesis(
                recon_id,
                {
                    "proto_forms": proto_model.get("proto_forms") or [],
                    "primary": proto_model.get("primary"),
                    "confidence": quality,
                    "attestation_ids": list(attestation_ids),
                    "correspondence_hypothesis_count": len(
                        corr_payload.get("hypotheses") or []
                    ),
                },
                links=[e.evidence_id for e in evidence_list],
            )
        # Require lineage when explicitly configured, or when Dantomax has attestations.
        require_att = bool(
            self.constraints.get("require_attestation_lineage")
            or (dantomax is not None and bool(attestation_ids))
        )
        self.evidence_registry.register_reconstruction(
            recon_id,
            evidence_ids=[e.evidence_id for e in evidence_list],
            proto_model=proto_model,
            metrics=metrics,
            constraints={
                "evidence_min_count": int(self.constraints["evidence_min_count"]),
                "drift_threshold": threshold,
                "require_attestation_lineage": require_att,
                "attestation_ids": list(attestation_ids),
            },
            governance_approved=False,
            alignment_ok=True,
        )

        # 7. VALIDATE
        validation = self.evidence_registry.validate_reconstruction(recon_id)
        validate_out = self.stages.validate(validation)
        stages_completed.append("VALIDATE")

        if not validation.is_valid:
            return {
                "reconstruction_id": recon_id,
                "status": "FAILED",
                "fra_stage": "VALIDATE",
                "proto_language_model": proto_model,
                "validation": validate_out,
                "stages_completed": stages_completed,
                "metrics": metrics,
                "refinement_halted": refine_out.get("refinement_halted"),
                "quality_improved": refine_out.get("quality_improved"),
            }

        # 8. GOVERN — attestation lineage gate (only when lineage is required/present)
        lineage = None
        gov_ok = True
        gov_reason = ""
        must_lineage = bool(self.constraints.get("require_attestation_lineage")) or bool(
            attestation_ids
        )
        if must_lineage:
            if dantomax is None:
                gov_ok = False
                gov_reason = "attestation lineage required but Dantomax not attached"
            else:
                bad = (
                    dantomax.require_attested_sources(attestation_ids)
                    if attestation_ids
                    else ["missing:no_attestation_ids"]
                )
                if bad:
                    gov_ok = False
                    gov_reason = f"unattested_or_invalid: {bad}"
                else:
                    lineage = dantomax.build_lineage_trace(
                        attestation_ids=attestation_ids,
                        cognate_set_id=(clustered.get("cognate_groups") or [{}])[0].get(
                            "group_id"
                        ),
                        correspondence_ids=[
                            f"corr_{i}"
                            for i, _ in enumerate(
                                (corr_payload.get("hypotheses") or [{}])[0].get(
                                    "correspondence_sets"
                                )
                                or []
                            )
                        ][:5],
                        sound_shift_ids=[
                            s.get("rule") or s.get("named_transform") or f"shift_{i}"
                            for i, s in enumerate(
                                (corr_payload.get("hypotheses") or [{}])[0].get(
                                    "sound_change_sequence"
                                )
                                or []
                            )
                            if isinstance(s, dict)
                        ][:5],
                        proto_form_id=str((proto_model.get("primary") or {}).get("id")),
                        certification_id=None,
                    )
        elif dantomax is not None and attestation_ids:
            lineage = dantomax.build_lineage_trace(
                attestation_ids=attestation_ids,
                cognate_set_id=(clustered.get("cognate_groups") or [{}])[0].get("group_id"),
                proto_form_id=str((proto_model.get("primary") or {}).get("id")),
            )

        govern_out = self.stages.govern(
            {
                "passed": gov_ok,
                "reason": gov_reason,
                "attestation_ids": attestation_ids,
                "lineage": lineage,
                "human_lineage": (lineage or {}).get("human_readable")
                or format_human_lineage(lineage or {"path": list(FRAStages.STAGE_ORDER)}),
                "cih_state": "PENDING_CERTIFY" if gov_ok else "BLOCKED",
            }
        )
        if cel is not None:
            cel.record_governance(
                f"gov_{recon_id}",
                {
                    "event_type": "FRA_GOVERN",
                    "passed": gov_ok,
                    "reason": gov_reason,
                    "attestation_ids": attestation_ids,
                    "reconstruction_id": recon_id,
                },
                links=list(attestation_ids) + [recon_id],
            )
        stages_completed.append("GOVERN")

        if not gov_ok:
            return {
                "reconstruction_id": recon_id,
                "status": "FAILED",
                "fra_stage": "GOVERN",
                "reason": gov_reason,
                "proto_language_model": proto_model,
                "validation": validate_out,
                "governance": govern_out,
                "stages_completed": stages_completed,
                "metrics": metrics,
            }

        # 9. CERTIFY
        corpus_hash = self._corpus_hash()
        attestation_root = (
            dantomax.attestation_root_hash if dantomax is not None else None
        )
        fabric_root = cel.fabric_root_hash if cel is not None else None
        cert_fields = {
            "corpus_hash": corpus_hash,
            "attestation_root_hash": attestation_root,
            "fabric_root_hash": fabric_root,
            "rule_set_version": RULE_SET_VERSION,
            "reconstruction_ids": [recon_id]
            + [str(h.get("id")) for h in (proto_model.get("proto_forms") or []) if h.get("id")],
            "validation_summary": {
                "is_valid": validation.is_valid,
                "failed_checks": list(validation.failed_checks or []),
                "fac_report": getattr(validation, "report", {}) or {},
            },
            "lineage_trace": lineage,
        }
        certificate = self.stages.certify(
            proto_model, validation, certificate_fields=cert_fields
        )
        if cel is not None:
            cel_entry = cel.record_certification(
                str(certificate.get("certificate_id") or f"cert_{recon_id}"),
                certificate,
                links=[recon_id] + list(attestation_ids),
            )
            certificate["ledger_entry_id"] = cel_entry.cel_entry_id
            certificate["fabric_root_hash"] = cel.fabric_root_hash
            cert_fields["ledger_entry_id"] = cel_entry.cel_entry_id
            cert_fields["fabric_root_hash"] = cel.fabric_root_hash
        if lineage and dantomax is not None:
            lineage = dantomax.build_lineage_trace(
                attestation_ids=attestation_ids,
                cognate_set_id=(clustered.get("cognate_groups") or [{}])[0].get("group_id"),
                correspondence_ids=lineage.get("nodes")
                and [
                    n["id"]
                    for n in lineage["nodes"]
                    if n.get("kind") == "correspondence"
                ]
                or [],
                sound_shift_ids=[
                    n["id"]
                    for n in (lineage.get("nodes") or [])
                    if n.get("kind") == "sound_shift"
                ],
                proto_form_id=str((proto_model.get("primary") or {}).get("id")),
                certification_id=certificate.get("certificate_id"),
            )
            certificate["lineage_trace"] = lineage
            govern_out["lineage"] = lineage
            govern_out["human_lineage"] = lineage.get("human_readable")
        stages_completed.append("CERTIFY")

        # 10. ARCHIVE
        archive = self.stages.archive(
            proto_model, certificate, stages_completed, metrics
        )
        stages_completed.append("ARCHIVE")

        if set(FRAStages.STAGE_ORDER) - set(stages_completed):
            return {
                "reconstruction_id": recon_id,
                "status": "FAILED",
                "fra_stage": stages_completed[-1] if stages_completed else "OBSERVE",
                "reason": "FRA-01: incomplete stage set",
                "stages_completed": stages_completed,
                "metrics": metrics,
            }

        return {
            "reconstruction_id": recon_id,
            "status": "COMPLETED",
            "fra_stage": "ARCHIVE",
            "proto_language_model": proto_model,
            "certificate_id": certificate.get("certificate_id"),
            "certificate": certificate,
            "archive_record": archive,
            "validation": validate_out,
            "governance": govern_out,
            "stages_completed": stages_completed,
            "metrics": metrics,
            "lineage": lineage,
            "human_lineage": govern_out.get("human_lineage"),
            "refinement_halted": refine_out.get("refinement_halted"),
            "quality_improved": refine_out.get("quality_improved"),
            "correspondence_search": corr_payload,
            "cel": cel.summary() if cel is not None else None,
        }

    def _corpus_hash(self) -> str:
        try:
            path = resolve_corpus_path(self.corpus_path)
            raw = Path(path).read_bytes()
            return hashlib.sha256(raw).hexdigest()
        except Exception:
            blob = json.dumps({"corpus": str(self.corpus_path)}, sort_keys=True)
            return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def _run_correspondence_search(
        self,
        analysis: dict[str, Any],
        evidence_list: list[Any],
        attestation_ids: list[str],
        flags_by_lang: dict[str, list[str]],
    ) -> dict[str, Any]:
        eid_to_att: dict[str, list[str]] = {}
        eid_to_form: dict[str, tuple[str, str]] = {}
        for ev in evidence_list:
            content = ev.content or {}
            form = str(content.get("form") or "")
            lang = str(content.get("language_code") or "?").lower()
            meta = content.get("metadata") or {}
            aids = list(meta.get("attestation_ids") or [])
            if isinstance(meta.get("attestation"), dict):
                aids.append(meta["attestation"]["attestation_id"])
            eid_to_att[ev.evidence_id] = list(dict.fromkeys(aids))
            if form:
                eid_to_form[ev.evidence_id] = (lang, form)

        all_hyps: list[dict[str, Any]] = []
        ambiguous: list[str] = []
        irregular: list[str] = []
        loo_examples: list[dict[str, Any]] = []

        for group in analysis.get("cognate_groups") or []:
            members = group.get("members") or []
            forms: dict[str, str] = {}
            att_map: dict[str, list[str]] = {}
            for m in members:
                lang = str(m.get("language") or "?").lower()
                form = str(m.get("form") or "")
                if not form or lang in {"pie", "?"}:
                    continue
                # keep first form per language
                forms.setdefault(lang, form)
                eid = m.get("evidence_id")
                if eid and eid in eid_to_att:
                    att_map.setdefault(lang, []).extend(eid_to_att[eid])
            if len(forms) < 2:
                continue
            # known proto from PIE evidence in same meaning group
            known = None
            for m in members:
                if str(m.get("language") or "").upper() == "PIE":
                    known = str(m.get("form") or "").lstrip("*")
            group_flags = {
                lang: flags_by_lang.get(lang, [])
                for lang in forms
                if flags_by_lang.get(lang)
            }
            hyps = self.correspondence.reconstruct_set(
                forms,
                attestation_ids=att_map,
                flags_by_lang=group_flags,
                known_proto=known,
            )
            gid = group.get("group_id", "cog")
            serialized = []
            for h in hyps:
                d = {
                    "cognate_set_id": gid,
                    "proto_form": h.proto_form,
                    "confidence": h.confidence,
                    "supporting_attestations": h.supporting_attestation_ids,
                    "aligned_daughter_forms": h.aligned_daughter_forms,
                    "correspondence_sets": h.correspondence_sets,
                    "sound_change_sequence": h.sound_change_sequence,
                    "competing_hypotheses": h.competing_hypotheses,
                    "unresolved_conflicts": h.unresolved_conflicts,
                    "leave_one_out": h.leave_one_out,
                    "flags": h.flags,
                    "regularity_score": h.regularity_score,
                    "exception_penalty": h.exception_penalty,
                }
                serialized.append(d)
                all_hyps.append(d)
            if len(serialized) >= 2:
                ambiguous.append(gid)
            for h in hyps:
                if h.flags or h.unresolved_conflicts:
                    irregular.append(gid)
                    break
            if hyps and hyps[0].leave_one_out.get("applicable"):
                loo_examples.append({"cognate_set_id": gid, **hyps[0].leave_one_out})

        # global attestation fallback
        if not all_hyps and len(eid_to_form) >= 2:
            forms = {}
            for lang, form in eid_to_form.values():
                forms.setdefault(lang, form)
            hyps = self.correspondence.reconstruct_set(
                forms,
                attestation_ids={"*": attestation_ids},
                flags_by_lang=flags_by_lang,
            )
            for h in hyps:
                all_hyps.append(
                    {
                        "cognate_set_id": "cognate_global",
                        "proto_form": h.proto_form,
                        "confidence": h.confidence,
                        "supporting_attestations": h.supporting_attestation_ids,
                        "aligned_daughter_forms": h.aligned_daughter_forms,
                        "correspondence_sets": h.correspondence_sets,
                        "sound_change_sequence": h.sound_change_sequence,
                        "competing_hypotheses": h.competing_hypotheses,
                        "unresolved_conflicts": h.unresolved_conflicts,
                        "leave_one_out": h.leave_one_out,
                        "flags": h.flags,
                    }
                )

        return {
            "hypotheses": all_hyps,
            "ambiguous_sets": list(dict.fromkeys(ambiguous)),
            "flagged_irregular": list(dict.fromkeys(irregular)),
            "leave_one_out_examples": loo_examples[:5],
            "alignment_report": {
                "sets": sum(len(h.get("correspondence_sets") or []) for h in all_hyps),
                "engine": RULE_SET_VERSION,
            },
        }

    def _merge_hypotheses(
        self,
        base: dict[str, Any],
        corr_hyps: list[dict[str, Any]],
    ) -> dict[str, Any]:
        hyps = list(base.get("hypotheses") or [])
        for ch in corr_hyps[:20]:
            hyps.append(
                {
                    "id": f"pf_corr_{ch.get('cognate_set_id')}_{ch.get('proto_form')}",
                    "form": f"*{ch.get('proto_form')}-",
                    "confidence": float(ch.get("confidence") or 0.5),
                    "ancestor_hint": f"correspondence:{ch.get('cognate_set_id')}",
                    "evidence_links": [],
                    "attestation_ids": list(ch.get("supporting_attestations") or []),
                    "competing_hypotheses": ch.get("competing_hypotheses") or [],
                    "flags": ch.get("flags") or [],
                    "leave_one_out": ch.get("leave_one_out") or {},
                    "sound_change_sequence": ch.get("sound_change_sequence") or [],
                    "correspondence_sets": ch.get("correspondence_sets") or [],
                    "aligned_daughter_forms": ch.get("aligned_daughter_forms") or {},
                    "unresolved_conflicts": ch.get("unresolved_conflicts") or [],
                    "source": "correspondence_engine",
                }
            )
        hyps.sort(key=lambda h: h.get("confidence", 0), reverse=True)
        return {"hypotheses": hyps}
