"""FRA stage scaffolding — OBSERVE → ARCHIVE (attestation-aware pipeline)."""

from __future__ import annotations

from typing import Any


class FRAStages:
    """Stage hooks for ChronologicalReconstruction."""

    STAGE_ORDER = (
        "OBSERVE",
        "INGEST",
        "ATTEST",
        "ALIGN",
        "CLUSTER",
        "INFER",
        "VALIDATE",
        "GOVERN",
        "CERTIFY",
        "ARCHIVE",
    )

    def observe(self, evidence_list: list[Any]) -> dict[str, Any]:
        by_type: dict[str, int] = {}
        by_lang: dict[str, int] = {}
        for ev in evidence_list:
            et = getattr(getattr(ev, "evidence_type", None), "value", "unknown")
            by_type[et] = by_type.get(et, 0) + 1
            lang = (getattr(ev, "content", {}) or {}).get("language_code", "?")
            by_lang[str(lang)] = by_lang.get(str(lang), 0) + 1
        return {
            "stage": "OBSERVE",
            "evidence_count": len(evidence_list),
            "by_type": by_type,
            "by_language": by_lang,
            "evidence_ids": [ev.evidence_id for ev in evidence_list],
        }

    def ingest(self, evidence_list: list[Any]) -> dict[str, Any]:
        return {
            "stage": "INGEST",
            "ingested_ids": [ev.evidence_id for ev in evidence_list],
            "count": len(evidence_list),
        }

    def attest(self, attestation_summary: dict[str, Any]) -> dict[str, Any]:
        return {
            "stage": "ATTEST",
            **attestation_summary,
        }

    def align(
        self,
        proto_model: dict[str, Any] | None,
        temporal_map: dict[str, Any],
        *,
        correspondence_report: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "stage": "ALIGN",
            "proto_model": proto_model,
            "temporal_map": temporal_map,
            "correspondence_report": correspondence_report or {},
            "aligned": bool(temporal_map.get("alignments"))
            or bool((correspondence_report or {}).get("sets")),
        }

    def cluster(self, analysis: dict[str, Any]) -> dict[str, Any]:
        return {
            "stage": "CLUSTER",
            "lexical_clusters": analysis.get("lexical_clusters", []),
            "cognate_groups": analysis.get("cognate_groups", []),
            "phonological_shifts": analysis.get("phonological_shifts", []),
        }

    def infer(
        self,
        hypotheses: dict[str, Any],
        target_language: str,
        time_period: str,
        *,
        correspondence_hypotheses: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        hyps = list(hypotheses.get("hypotheses") or [])
        top = (
            hyps[0]
            if hyps
            else {
                "id": "pf_empty",
                "form": "*?",
                "confidence": 0.0,
                "evidence_links": [],
            }
        )
        return {
            "stage": "INFER",
            "id": f"proto_{target_language}_{time_period}".replace(" ", "_"),
            "target_language": target_language,
            "time_period": time_period,
            "proto_forms": hyps,
            "primary": top,
            "correspondence_hypotheses": correspondence_hypotheses or [],
        }

    def test(self, proto_model: dict[str, Any], evidence_list: list[Any]) -> dict[str, Any]:
        """Score coverage across all proto forms (used as metrics helper)."""
        forms = list(proto_model.get("proto_forms") or [])
        primary = proto_model.get("primary") or {}
        if primary and not any(p.get("id") == primary.get("id") for p in forms):
            forms = [primary] + forms
        if not forms and primary:
            forms = [primary]

        linked_ids: set[str] = set()
        stems: list[str] = []
        for hyp in forms:
            for eid in hyp.get("evidence_links") or []:
                linked_ids.add(str(eid))
            form = str(hyp.get("form") or "").lower().strip("*").rstrip("-")
            if len(form) >= 2:
                stems.append(form[:2])

        hits = 0
        checked = 0
        for ev in evidence_list:
            eid = str(getattr(ev, "evidence_id", "") or "")
            content = getattr(ev, "content", {}) or {}
            blob = " ".join(
                str(content.get(k) or "") for k in ("form", "text", "gloss", "meaning")
            ).lower()
            if not blob.strip() and eid not in linked_ids:
                continue
            checked += 1
            if eid and eid in linked_ids:
                hits += 1
                continue
            if any(stem in blob for stem in stems):
                hits += 1
        coverage = (hits / checked) if checked else 0.0
        drift = max(0.0, 1.0 - coverage)
        return {
            "stage": "TEST",
            "hits": hits,
            "checked": checked,
            "coverage": coverage,
            "drift": drift,
            "quality": coverage,
        }

    def refine(
        self,
        proto_model: dict[str, Any],
        analysis: dict[str, Any],
        ai_agent: Any,
        max_iterations: int = 5,
        quality_gate: float = 0.4,
    ) -> dict[str, Any]:
        primary = dict(proto_model.get("primary") or {})
        quality = float(primary.get("confidence") or 0.0)
        halted = False
        improved = False
        history: list[dict[str, Any]] = []
        for i in range(1, max_iterations + 1):
            step = ai_agent.refine_reconstruction(primary, analysis, i)
            refined = step["refined_proto_form"]
            q = float(step["quality_metrics"]["score"])
            history.append({"iteration": i, "quality": q})
            if q < quality:
                halted = True
                break
            if q > quality:
                improved = True
            primary = refined
            quality = q
            if quality >= quality_gate and improved:
                break
        proto_model = dict(proto_model)
        proto_model["primary"] = primary
        proto_model["proto_forms"] = [primary] + [
            p for p in proto_model.get("proto_forms", []) if p.get("id") != primary.get("id")
        ]
        return {
            "stage": "REFINE",
            "proto_model": proto_model,
            "quality": quality,
            "quality_improved": improved,
            "refinement_halted": halted,
            "history": history,
        }

    def validate(self, validation: Any) -> dict[str, Any]:
        is_valid = bool(getattr(validation, "is_valid", False))
        return {
            "stage": "VALIDATE",
            "is_valid": is_valid,
            "failed_checks": list(getattr(validation, "failed_checks", []) or []),
            "report": getattr(validation, "report", {}) or {},
        }

    def govern(self, governance_report: dict[str, Any]) -> dict[str, Any]:
        return {
            "stage": "GOVERN",
            **governance_report,
        }

    def certify(
        self,
        proto_model: dict[str, Any],
        validation: Any,
        *,
        certificate_fields: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        cert_id = f"cert_{proto_model.get('id', 'unknown')}"
        out = {
            "stage": "CERTIFY",
            "certificate_id": cert_id,
            "valid": bool(getattr(validation, "is_valid", False)),
            "subject": {
                "reconstruction_id": proto_model.get("id"),
                "target_language": proto_model.get("target_language"),
                "time_period": proto_model.get("time_period"),
            },
        }
        if certificate_fields:
            out.update(certificate_fields)
        return out

    def archive(
        self,
        proto_model: dict[str, Any],
        certificate: dict[str, Any],
        stages_completed: list[str],
        metrics: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "stage": "ARCHIVE",
            "reconstruction_id": proto_model.get("id"),
            "certificate_id": certificate.get("certificate_id"),
            "stages_completed": list(stages_completed),
            "metrics": metrics,
            "immutable": True,
        }
