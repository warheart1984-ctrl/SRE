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
from .reconstruction_state import ReconstructionRunState
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
        init = self.begin_run(target_language, time_period, evidence_sources)
        if isinstance(init, dict):
            return init
        state = init
        for step in (
            self.stage_observe_ingest,
            self.stage_attest,
            self.stage_align_cluster,
            self.stage_infer,
            self.stage_validate,
            self.stage_govern,
            self.stage_certify,
            self.stage_archive,
        ):
            failure = step(state)
            if failure is not None:
                return failure
        return state.complete()

    def begin_run(
        self,
        target_language: str,
        time_period: str,
        evidence_sources: list[str],
        *,
        iteration: int = 0,
    ) -> ReconstructionRunState | dict[str, Any]:
        """Initialize pipeline state; return failure dict when evidence is missing."""
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

        evidence_list: list[Any] = []
        missing: list[str] = []
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

        state = ReconstructionRunState(
            target_language=target_language,
            time_period=time_period,
            evidence_sources=list(evidence_sources),
            evidence_list=evidence_list,
            iteration=iteration,
            _engine=self,
        )
        return state

    def stage_observe_ingest(self, state: ReconstructionRunState) -> dict[str, Any] | None:
        state.observed = self.stages.observe(state.evidence_list)
        state.stages_completed.append("OBSERVE")
        state.ingested = self.stages.ingest(state.evidence_list)
        state.stages_completed.append("INGEST")
        return None

    def stage_attest(self, state: ReconstructionRunState) -> dict[str, Any] | None:
        dantomax = state.dantomax
        cel = state.cel
        state.attestation_ids = collect_attestation_ids(state.evidence_list)
        if dantomax is not None:
            state.att_summary = seed_attestations_from_evidence(
                dantomax, state.evidence_list, cel=cel
            )
            for aid in state.att_summary.get("registered") or []:
                try:
                    dantomax.approve_attestation(aid)
                except ValueError:
                    pass
            state.attestation_ids = collect_attestation_ids(state.evidence_list) or list(
                state.att_summary.get("registered") or []
            )
            if state.att_summary.get("errors"):
                return state.fail(
                    "ATTEST",
                    f"attestation errors: {state.att_summary['errors']}",
                    metrics={"attest": state.att_summary},
                )
        else:
            state.att_summary = {
                "registered": [],
                "skipped_duplicates": [],
                "errors": [],
                "count": 0,
                "note": "dantomax_not_attached",
            }
        state.attest_out = self.stages.attest(state.att_summary)
        state.stages_completed.append("ATTEST")

        state.analysis = self.ai_agent.analyze_evidence_patterns(state.evidence_list)
        state.flags_by_lang = evidence_flags_by_lang(state.evidence_list)
        state.corr_payload = self._run_correspondence_search(
            state.analysis,
            state.evidence_list,
            state.attestation_ids,
            state.flags_by_lang,
        )
        if cel is not None:
            for hyp in state.corr_payload.get("hypotheses") or []:
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
        return None

    def stage_align_cluster(self, state: ReconstructionRunState) -> dict[str, Any] | None:
        state.temporal_map = self.rosetta.map_temporal(state.evidence_list)
        state.aligned = self.stages.align(
            None,
            state.temporal_map,
            correspondence_report=state.corr_payload.get("alignment_report"),
        )
        state.stages_completed.append("ALIGN")
        state.clustered = self.stages.cluster(state.analysis)
        state.stages_completed.append("CLUSTER")
        return None

    def stage_infer(self, state: ReconstructionRunState) -> dict[str, Any] | None:
        hypotheses = self.ai_agent.predict_proto_forms(state.analysis)
        if state.corr_payload.get("hypotheses"):
            hypotheses = self._merge_hypotheses(hypotheses, state.corr_payload["hypotheses"])
        state.proto_model = self.stages.infer(
            hypotheses,
            state.target_language,
            state.time_period,
            correspondence_hypotheses=state.corr_payload.get("hypotheses"),
        )
        state.test_result = self.stages.test(state.proto_model, state.evidence_list)
        state.drift = float(state.test_result.get("drift", 1.0))
        state.quality = float(state.test_result.get("quality", 0.0))
        threshold = float(self.constraints["drift_threshold"])
        quality_gate = float(self.constraints["quality_gate"])
        needs_extra = state.drift > threshold or state.quality < quality_gate
        max_iterations = int(self.constraints["max_iterations"]) if needs_extra else 1
        state.refine_out = self.stages.refine(
            state.proto_model,
            state.analysis,
            self.ai_agent,
            max_iterations=max_iterations,
            quality_gate=quality_gate,
        )
        state.proto_model = state.refine_out["proto_model"]
        state.proto_model["correspondence_hypotheses"] = (
            state.corr_payload.get("hypotheses") or []
        )
        state.test_result = self.stages.test(state.proto_model, state.evidence_list)
        state.drift = float(state.test_result.get("drift", state.drift))
        state.quality = float(state.refine_out.get("quality", state.quality))
        state.stages_completed.append("INFER")

        if self.constraints.get("require_drift_metrics") and "drift" not in state.test_result:
            return state.fail(
                "INFER",
                "FRA-03: drift metrics required",
                metrics=state.test_result,
            )

        for hyp in state.proto_model.get("proto_forms") or []:
            hyp.setdefault("attestation_ids", list(state.attestation_ids))
        if state.proto_model.get("primary"):
            state.proto_model["primary"].setdefault(
                "attestation_ids", list(state.attestation_ids)
            )

        state.metrics = {
            "drift": state.drift,
            "coverage": float(state.test_result.get("coverage", 0.0)),
            "quality": state.quality,
            "consistency": float(state.test_result.get("coverage", 0.0)),
            "evidence_count": len(state.evidence_list),
            "observe": state.observed,
            "ingest": state.ingested,
            "attest": state.attest_out,
            "align": state.aligned,
            "cluster_summary": {
                "clusters": len(state.clustered.get("lexical_clusters") or []),
                "cognates": len(state.clustered.get("cognate_groups") or []),
                "shifts": len(state.clustered.get("phonological_shifts") or []),
            },
            "aligned": state.aligned.get("aligned", False),
            "correspondence": {
                "hypothesis_count": len(state.corr_payload.get("hypotheses") or []),
                "ambiguous_sets": state.corr_payload.get("ambiguous_sets") or [],
                "flagged_irregular": state.corr_payload.get("flagged_irregular") or [],
                "leave_one_out": state.corr_payload.get("leave_one_out_examples") or [],
            },
            "iteration": state.iteration,
        }
        state.recon_id = str(state.proto_model.get("id"))
        return None

    def stage_validate(self, state: ReconstructionRunState) -> dict[str, Any] | None:
        cel = state.cel
        dantomax = state.dantomax
        threshold = float(self.constraints["drift_threshold"])
        require_att = bool(
            self.constraints.get("require_attestation_lineage")
            or (dantomax is not None and bool(state.attestation_ids))
        )
        if cel is not None:
            cel.record_hypothesis(
                state.recon_id,
                {
                    "proto_forms": state.proto_model.get("proto_forms") or [],
                    "primary": state.proto_model.get("primary"),
                    "confidence": state.quality,
                    "attestation_ids": list(state.attestation_ids),
                    "correspondence_hypothesis_count": len(
                        state.corr_payload.get("hypotheses") or []
                    ),
                },
                links=[e.evidence_id for e in state.evidence_list],
            )
        self.evidence_registry.register_reconstruction(
            state.recon_id,
            evidence_ids=[e.evidence_id for e in state.evidence_list],
            proto_model=state.proto_model,
            metrics=state.metrics,
            constraints={
                "evidence_min_count": int(self.constraints["evidence_min_count"]),
                "drift_threshold": threshold,
                "require_attestation_lineage": require_att,
                "attestation_ids": list(state.attestation_ids),
            },
            governance_approved=False,
            alignment_ok=True,
        )
        state.validation = self.evidence_registry.validate_reconstruction(state.recon_id)
        state.validate_out = self.stages.validate(state.validation)
        state.stages_completed.append("VALIDATE")
        if not state.validation.is_valid:
            return state.fail(
                "VALIDATE",
                "validation failed",
                proto_language_model=state.proto_model,
                validation=state.validate_out,
                refinement_halted=state.refine_out.get("refinement_halted"),
                quality_improved=state.refine_out.get("quality_improved"),
            )
        return None

    def stage_govern(self, state: ReconstructionRunState) -> dict[str, Any] | None:
        dantomax = state.dantomax
        cel = state.cel
        state.gov_ok = True
        state.gov_reason = ""
        must_lineage = bool(self.constraints.get("require_attestation_lineage")) or bool(
            state.attestation_ids
        )
        if must_lineage:
            if dantomax is None:
                state.gov_ok = False
                state.gov_reason = "attestation lineage required but Dantomax not attached"
            else:
                bad = (
                    dantomax.require_attested_sources(state.attestation_ids)
                    if state.attestation_ids
                    else ["missing:no_attestation_ids"]
                )
                if bad:
                    state.gov_ok = False
                    state.gov_reason = f"unattested_or_invalid: {bad}"
                else:
                    state.lineage = dantomax.build_lineage_trace(
                        attestation_ids=state.attestation_ids,
                        cognate_set_id=(state.clustered.get("cognate_groups") or [{}])[0].get(
                            "group_id"
                        ),
                        correspondence_ids=[
                            f"corr_{i}"
                            for i, _ in enumerate(
                                (state.corr_payload.get("hypotheses") or [{}])[0].get(
                                    "correspondence_sets"
                                )
                                or []
                            )
                        ][:5],
                        sound_shift_ids=[
                            s.get("rule") or s.get("named_transform") or f"shift_{i}"
                            for i, s in enumerate(
                                (state.corr_payload.get("hypotheses") or [{}])[0].get(
                                    "sound_change_sequence"
                                )
                                or []
                            )
                            if isinstance(s, dict)
                        ][:5],
                        proto_form_id=str((state.proto_model.get("primary") or {}).get("id")),
                        certification_id=None,
                    )
        elif dantomax is not None and state.attestation_ids:
            state.lineage = dantomax.build_lineage_trace(
                attestation_ids=state.attestation_ids,
                cognate_set_id=(state.clustered.get("cognate_groups") or [{}])[0].get("group_id"),
                proto_form_id=str((state.proto_model.get("primary") or {}).get("id")),
            )

        state.govern_out = self.stages.govern(
            {
                "passed": state.gov_ok,
                "reason": state.gov_reason,
                "attestation_ids": state.attestation_ids,
                "lineage": state.lineage,
                "human_lineage": (state.lineage or {}).get("human_readable")
                or format_human_lineage(
                    state.lineage or {"path": list(FRAStages.STAGE_ORDER)}
                ),
                "cih_state": "PENDING_CERTIFY" if state.gov_ok else "BLOCKED",
            }
        )
        if cel is not None:
            cel.record_governance(
                f"gov_{state.recon_id}",
                {
                    "event_type": "FRA_GOVERN",
                    "passed": state.gov_ok,
                    "reason": state.gov_reason,
                    "attestation_ids": state.attestation_ids,
                    "reconstruction_id": state.recon_id,
                },
                links=list(state.attestation_ids) + [state.recon_id],
            )
        state.stages_completed.append("GOVERN")
        if not state.gov_ok:
            return state.fail(
                "GOVERN",
                state.gov_reason,
                proto_language_model=state.proto_model,
                validation=state.validate_out,
                governance=state.govern_out,
            )
        return None

    def stage_certify(self, state: ReconstructionRunState) -> dict[str, Any] | None:
        dantomax = state.dantomax
        cel = state.cel
        cert_fields = {
            "corpus_hash": self._corpus_hash(),
            "attestation_root_hash": (
                dantomax.attestation_root_hash if dantomax is not None else None
            ),
            "fabric_root_hash": cel.fabric_root_hash if cel is not None else None,
            "rule_set_version": RULE_SET_VERSION,
            "reconstruction_ids": [state.recon_id]
            + [
                str(h.get("id"))
                for h in (state.proto_model.get("proto_forms") or [])
                if h.get("id")
            ],
            "validation_summary": {
                "is_valid": state.validation.is_valid,
                "failed_checks": list(state.validation.failed_checks or []),
                "fac_report": getattr(state.validation, "report", {}) or {},
            },
            "lineage_trace": state.lineage,
        }
        state.certificate = self.stages.certify(
            state.proto_model, state.validation, certificate_fields=cert_fields
        )
        if cel is not None:
            cel_entry = cel.record_certification(
                str(state.certificate.get("certificate_id") or f"cert_{state.recon_id}"),
                state.certificate,
                links=[state.recon_id] + list(state.attestation_ids),
            )
            state.certificate["ledger_entry_id"] = cel_entry.cel_entry_id
            state.certificate["fabric_root_hash"] = cel.fabric_root_hash
            cert_fields["ledger_entry_id"] = cel_entry.cel_entry_id
            cert_fields["fabric_root_hash"] = cel.fabric_root_hash
        if state.lineage and dantomax is not None:
            state.lineage = dantomax.build_lineage_trace(
                attestation_ids=state.attestation_ids,
                cognate_set_id=(state.clustered.get("cognate_groups") or [{}])[0].get(
                    "group_id"
                ),
                correspondence_ids=state.lineage.get("nodes")
                and [
                    n["id"]
                    for n in state.lineage["nodes"]
                    if n.get("kind") == "correspondence"
                ]
                or [],
                sound_shift_ids=[
                    n["id"]
                    for n in (state.lineage.get("nodes") or [])
                    if n.get("kind") == "sound_shift"
                ],
                proto_form_id=str((state.proto_model.get("primary") or {}).get("id")),
                certification_id=state.certificate.get("certificate_id"),
            )
            state.certificate["lineage_trace"] = state.lineage
            state.govern_out["lineage"] = state.lineage
            state.govern_out["human_lineage"] = state.lineage.get("human_readable")
        state.stages_completed.append("CERTIFY")
        return None

    def stage_archive(self, state: ReconstructionRunState) -> dict[str, Any] | None:
        state.archive = self.stages.archive(
            state.proto_model, state.certificate, state.stages_completed, state.metrics
        )
        state.stages_completed.append("ARCHIVE")
        if set(FRAStages.STAGE_ORDER) - set(state.stages_completed):
            return state.fail(
                state.stages_completed[-1] if state.stages_completed else "OBSERVE",
                "FRA-01: incomplete stage set",
            )
        return None

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
