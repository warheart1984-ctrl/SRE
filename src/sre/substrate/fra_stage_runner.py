"""Wire SRE FRA stage groups into FAE GovernedFRACycle hooks."""

from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import datetime
from typing import Any, Callable

from fae.cycle.fra_cycle import (
    BuildModelStage,
    CycleContext,
    FACInvariantViolation,
    FRACycleError,
    FRACycleStage,
    MeasureRealityStage,
    ReasonStage,
    StageResult,
    UpdateModelStage,
)
from fae.evidence.registry import EvidenceSource
from fae.governance.hooks import FACGovernanceHooks, GovernedFRACycle
from fae.metrics.validation import get_validation_engine

from ..fra.reconstruction_engine import ChronologicalReconstruction
from ..fra.reconstruction_state import (
    FAE_TO_SRE_STAGE_GROUPS,
    ReconstructionRunState,
    SRE_TO_FAE_STAGE_MAP,
)
from .fac_evidence import (
    SREAnchoredEvidenceMixin,
    aligned_measurements,
    aligned_predictions,
    build_reasoning_explanations,
)
from fae.api import EvidenceRegistry as FAEEvidenceRegistry


class SREBuildModelStage(SREAnchoredEvidenceMixin, BuildModelStage):
    pass


class SREReasonStage(SREAnchoredEvidenceMixin, ReasonStage):
    pass


class SREUpdateModelStage(SREAnchoredEvidenceMixin, UpdateModelStage):
    pass


class SREMeasureRealityStage(MeasureRealityStage):
    """Record flat measurement payloads so FAC-V3 can match prediction keys."""

    def execute(self, context: CycleContext) -> StageResult:
        measurements: dict[str, Any] = {}
        evidence_ids: list[str] = []

        for name, measurer in self.measurers.items():
            try:
                measurement = measurer()
                measurements[name] = measurement
                eid = self._record_evidence(
                    context,
                    content=measurement,
                    content_type="measurement",
                    source=EvidenceSource.EXTERNAL_SENSOR,
                    source_id=f"measurer_{name}",
                    acquisition_method="post_action_measurement",
                    confidence=1.0,
                )
                evidence_ids.append(eid)
            except Exception as e:
                return StageResult(
                    stage=self.stage,
                    success=False,
                    errors=[f"Measurer {name} failed: {e}"],
                )

        return StageResult(
            stage=self.stage,
            success=True,
            output=measurements,
            evidence_ids=evidence_ids,
        )


def _flatten_measurements(measurements: dict[str, Any]) -> dict[str, Any]:
    """Unwrap single-measurer output for compare/calibration."""
    if "quality" in measurements or "drift" in measurements:
        return measurements
    for value in measurements.values():
        if isinstance(value, dict):
            return value
    return measurements


def _patch_internal_evidence_stages(cycle: GovernedFRACycle) -> None:
    patched: list[Any] = []
    for stage in cycle.stages:
        if stage.stage == FRACycleStage.BUILD_MODEL and isinstance(stage, BuildModelStage):
            patched.append(SREBuildModelStage(stage.model_builder))
        elif stage.stage == FRACycleStage.REASON and isinstance(stage, ReasonStage):
            patched.append(SREReasonStage(stage.reasoner))
        elif stage.stage == FRACycleStage.UPDATE_MODEL and isinstance(stage, UpdateModelStage):
            patched.append(SREUpdateModelStage(stage.updater))
        elif stage.stage == FRACycleStage.MEASURE_REALITY and isinstance(stage, MeasureRealityStage):
            patched.append(SREMeasureRealityStage(stage.measurers))
        else:
            patched.append(stage)
    cycle.stages = patched


class SREFRAStageError(Exception):
    """Domain stage failure surfaced to FAE hook layer."""

    def __init__(self, failure: dict[str, Any]) -> None:
        self.failure = failure
        super().__init__(failure.get("reason", "SRE FRA stage failed"))


class SREFRAPipelineRunner:
    """Executes SRE stage groups and exposes FAE FRACycle hook callables."""

    def __init__(
        self,
        engine: ChronologicalReconstruction,
        *,
        target_language: str,
        time_period: str,
        evidence_sources: list[str],
        drift_threshold: float | None = None,
        quality_gate: float | None = None,
        max_fae_cycles: int = 5,
    ) -> None:
        self.engine = engine
        self.target_language = target_language
        self.time_period = time_period
        self.evidence_sources = list(evidence_sources)
        self.drift_threshold = drift_threshold or float(
            engine.constraints.get("drift_threshold", 0.6)
        )
        self.quality_gate = quality_gate or float(
            engine.constraints.get("quality_gate", 0.35)
        )
        self.max_fae_cycles = max_fae_cycles
        self.cycle_id = ""
        self.state: ReconstructionRunState | None = None
        self.domain_result: dict[str, Any] | None = None
        self._validation_engine = get_validation_engine()

    def _ensure_state(self, *, iteration: int = 0) -> ReconstructionRunState:
        if self.state is not None:
            return self.state
        init = self.engine.begin_run(
            self.target_language,
            self.time_period,
            self.evidence_sources,
            iteration=iteration,
        )
        if isinstance(init, dict):
            raise SREFRAStageError(init)
        self.state = init
        return self.state

    def _run_stage_group(self, method: Callable[[ReconstructionRunState], Any]) -> None:
        state = self._ensure_state()
        failure = method(state)
        if failure is not None:
            self.domain_result = failure
            raise SREFRAStageError(failure)

    # --- FAE hook factories (SRE stage groups) ---

    def make_observer(self) -> Callable[[], dict[str, Any]]:
        def observe() -> dict[str, Any]:
            self._run_stage_group(self.engine.stage_observe_ingest)
            state = self._ensure_state()
            return {
                "sre_stages": ("OBSERVE", "INGEST"),
                "evidence_count": len(state.evidence_list),
                "evidence_ids": [e.evidence_id for e in state.evidence_list],
                "observed": state.observed,
            }

        return observe

    def make_extractor(self) -> Callable[[Any], list[dict[str, Any]]]:
        def extract(obs: dict[str, Any]) -> list[dict[str, Any]]:
            self._run_stage_group(self.engine.stage_attest)
            state = self._ensure_state()
            facts: list[dict[str, Any]] = []
            for aid in state.attestation_ids:
                facts.append(
                    {
                        "fact_type": "attestation",
                        "attestation_id": aid,
                        "confidence": 1.0,
                        "source": "sre.attest",
                    }
                )
            for hyp in state.corr_payload.get("hypotheses") or []:
                facts.append(
                    {
                        "fact_type": "correspondence",
                        "proto_form": hyp.get("proto_form"),
                        "confidence": float(hyp.get("confidence") or 0.5),
                        "cognate_set_id": hyp.get("cognate_set_id"),
                    }
                )
            if not facts:
                facts.append(
                    {
                        "fact_type": "evidence_bundle",
                        "evidence_count": obs.get("evidence_count", 0),
                        "confidence": 0.9,
                    }
                )
            return facts

        return extract

    def make_model_builder(self) -> Callable[[Any, list[dict[str, Any]]], dict[str, Any]]:
        def build_model(_prev: Any, facts: list[dict[str, Any]]) -> dict[str, Any]:
            self._run_stage_group(self.engine.stage_align_cluster)
            state = self._ensure_state()
            return {
                "proto_model_seed": state.clustered,
                "temporal_map": state.temporal_map,
                "aligned": state.aligned,
                "fact_count": len(facts),
                "target_language": self.target_language,
                "time_period": self.time_period,
            }

        return build_model

    def make_reasoner(self) -> Callable[[Any], dict[str, Any]]:
        def reason(model: Any) -> dict[str, Any]:
            self._run_stage_group(self.engine.stage_infer)
            state = self._ensure_state()
            uncertainty = max(0.0, 1.0 - state.quality)
            explanations = build_reasoning_explanations(state)
            predictions = aligned_predictions(state, self.quality_gate, self.drift_threshold)
            return {
                "predictions": predictions,
                "confidence": state.quality,
                "uncertainty": uncertainty,
                "explanations": explanations,
                "proto_model": state.proto_model,
                "model_seed": model,
            }

        return reason

    def make_actor(self) -> Callable[[dict[str, Any]], dict[str, Any]]:
        def act(reasoning: dict[str, Any]) -> dict[str, Any]:
            self._run_stage_group(self.engine.stage_validate)
            state = self._ensure_state()
            return {
                "validation": state.validate_out,
                "reconstruction_id": state.recon_id,
                "is_valid": bool(getattr(state.validation, "is_valid", False)),
                "reasoning_hash": hash(str(reasoning)),
            }

        return act

    def make_measurer(self) -> Callable[[], dict[str, Any]]:
        def measure() -> dict[str, Any]:
            self._run_stage_group(self.engine.stage_govern)
            state = self._ensure_state()
            out = aligned_measurements(state)
            out["governance_reason"] = state.gov_reason
            return out

        return measure

    def make_comparator(self) -> Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]:
        def compare(predictions: dict[str, Any], measurements: dict[str, Any]) -> dict[str, Any]:
            self._run_stage_group(self.engine.stage_certify)
            state = self._ensure_state()
            flat = _flatten_measurements(measurements)
            predicted_quality = float(predictions.get("quality", self.quality_gate))
            actual_quality = float(flat.get("quality", state.quality))
            alignment_score = max(0.0, min(1.0, actual_quality))
            discrepancies: list[str] = []
            if actual_quality < predicted_quality:
                discrepancies.append(
                    f"quality {actual_quality:.3f} below target {predicted_quality:.3f}"
                )
            drift = float(flat.get("drift", state.drift))
            drift_target = float(predictions.get("drift", self.drift_threshold))
            if drift > drift_target:
                discrepancies.append(
                    f"drift {drift:.3f} exceeds threshold {drift_target:.3f}"
                )
            return {
                "alignment_score": alignment_score,
                "discrepancies": discrepancies,
                "predicted_quality": predicted_quality,
                "actual_quality": actual_quality,
                "certified": state.certificate.get("valid", False),
                "certificate_id": state.certificate.get("certificate_id"),
            }

        return compare

    def make_updater(self) -> Callable[[Any, dict[str, Any]], dict[str, Any]]:
        def update(model: Any, comparison: dict[str, Any]) -> dict[str, Any]:
            self._run_stage_group(self.engine.stage_archive)
            state = self._ensure_state()
            self.domain_result = state.complete()
            archived = {
                **self.domain_result,
                "model_seed": model,
                "comparison": comparison,
                "iteration": state.iteration,
                "drift": state.drift,
                "quality": state.quality,
            }
            if self.cycle_id:
                self._validation_engine.validate_cycle(self.cycle_id)
            return archived

        return update

    def make_should_continue(self) -> Callable[[CycleContext], bool]:
        def should_continue(context: CycleContext) -> bool:
            model = context.model_state if isinstance(context.model_state, dict) else {}
            iteration = int(model.get("iteration", 0))
            drift = float(model.get("drift", 1.0))
            quality = float(model.get("quality", 0.0))
            status = str(model.get("status", "FAILED"))
            if iteration >= self.max_fae_cycles - 1:
                return False
            if status != "COMPLETED":
                return False
            if drift <= self.drift_threshold and quality >= self.quality_gate:
                return False
            return True

        return should_continue

    def initial_model(self) -> dict[str, Any]:
        return {
            "target_language": self.target_language,
            "time_period": self.time_period,
            "evidence_sources": self.evidence_sources,
            "iteration": 0,
            "max_cycles": self.max_fae_cycles,
            "drift_threshold": self.drift_threshold,
            "quality_gate": self.quality_gate,
        }


class SREGovernedFRACycle(GovernedFRACycle):
    """GovernedFRACycle that accepts domain-composed FAC-1 when SRE metrics pass."""

    def __init__(
        self,
        *args: Any,
        runner: SREFRAPipelineRunner,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.runner = runner
        runner.cycle_id = self.cycle_id

    def run(self) -> CycleContext:
        self.governance.on_cycle_start(self.cycle_id, self.initial_model)
        self.csr.start_cycle(self.cycle_id, self.initial_model)
        context = CycleContext(
            cycle_id=self.cycle_id,
            timestamp=datetime.now(),
            model_state=self.model_state,
            evidence_registry=self.registry,
            csr=self.csr,
        )
        stage_outputs: dict[str, Any] = {}
        try:
            for stage in self.stages:
                result = stage.execute(context)
                self.csr.log_stage(
                    cycle_id=self.cycle_id,
                    stage=stage.stage.value,
                    success=result.success,
                    output=result.output,
                    evidence_ids=result.evidence_ids,
                    metrics=result.metrics,
                    errors=result.errors,
                )
                if not result.success:
                    self.csr.end_cycle(self.cycle_id, success=False, final_model=self.model_state)
                    self.governance.on_cycle_failed(
                        self.cycle_id,
                        FRACycleError(f"Stage {stage.stage.value} failed: {result.errors}"),
                        stage.stage,
                    )
                    raise FRACycleError(f"Stage {stage.stage.value} failed: {result.errors}")

                stage_outputs[stage.stage.value] = result.output
                context.metadata[stage.stage.value] = result.output

                if stage.stage == FRACycleStage.BUILD_MODEL:
                    self.model_state = result.output
                    context = replace(context, model_state=result.output)
                elif stage.stage == FRACycleStage.UPDATE_MODEL:
                    self.model_state = result.output
                    context = replace(context, model_state=result.output)

            domain_ok = (
                isinstance(self.model_state, dict)
                and self.model_state.get("status") == "COMPLETED"
            )
            if not domain_ok:
                self.csr.end_cycle(self.cycle_id, success=False, final_model=self.model_state)
                reason = (
                    self.runner.domain_result or {}
                ).get("reason", "SRE domain pipeline did not complete")
                raise FACInvariantViolation(f"Domain FAC-1 check failed: {reason}")

            self.csr.end_cycle(self.cycle_id, success=True, final_model=self.model_state)
            self.governance.on_cycle_complete(context)
            return context
        except SREFRAStageError as exc:
            self.csr.end_cycle(self.cycle_id, success=False, final_model=self.model_state)
            self.governance.on_cycle_failed(self.cycle_id, exc, FRACycleStage.OBSERVE)
            raise FRACycleError(str(exc)) from exc

    def run_recursive(self, max_cycles: int | None = None) -> list[CycleContext]:
        """Run FAE cycles until RECURSE returns False or max_cycles reached."""
        limit = max_cycles if max_cycles is not None else self.runner.max_fae_cycles
        contexts: list[CycleContext] = []
        for iteration in range(limit):
            self.runner.state = None
            self.runner.domain_result = None
            init = self.runner.engine.begin_run(
                self.runner.target_language,
                self.runner.time_period,
                self.runner.evidence_sources,
                iteration=iteration,
            )
            if isinstance(init, dict):
                break
            self.runner.state = init
            self.cycle_id = f"sre-fra-{uuid.uuid4().hex[:10]}-i{iteration}"
            self.runner.cycle_id = self.cycle_id
            if isinstance(self.initial_model, dict):
                seeded = dict(self.initial_model)
                seeded["iteration"] = iteration
                self.initial_model = seeded
                self.model_state = seeded
            try:
                context = self.run()
            except FRACycleError:
                break
            contexts.append(context)
            if not context.metadata.get("recurse", False):
                break
            constraints = dict(self.runner.engine.constraints)
            constraints["max_iterations"] = min(
                int(constraints.get("max_iterations", 5)) + 1,
                10,
            )
            self.runner.engine.constraints = constraints
        return contexts


def build_sre_governed_fra_cycle(
    engine: ChronologicalReconstruction,
    *,
    target_language: str,
    time_period: str,
    evidence_sources: list[str],
    fae_registry: FAEEvidenceRegistry | None = None,
    governance_hooks: FACGovernanceHooks | None = None,
    drift_threshold: float | None = None,
    quality_gate: float | None = None,
    max_fae_cycles: int = 5,
    component_id: str = "sre.fra.governed",
) -> SREGovernedFRACycle:
    """Build a GovernedFRACycle whose hooks execute SRE FRA stage groups."""
    runner = SREFRAPipelineRunner(
        engine,
        target_language=target_language,
        time_period=time_period,
        evidence_sources=evidence_sources,
        drift_threshold=drift_threshold,
        quality_gate=quality_gate,
        max_fae_cycles=max_fae_cycles,
    )
    hooks = governance_hooks or FACGovernanceHooks(component_id=component_id)
    cycle = SREGovernedFRACycle(
        observers={"sre_evidence": runner.make_observer()},
        extractors={"sre_evidence": runner.make_extractor()},
        model_builder=runner.make_model_builder(),
        reasoner=runner.make_reasoner(),
        actors={"sre_validate": runner.make_actor()},
        measurers={"sre_govern": runner.make_measurer()},
        comparator=runner.make_comparator(),
        updater=runner.make_updater(),
        should_continue=runner.make_should_continue(),
        initial_model=runner.initial_model(),
        governance_hooks=hooks,
        runner=runner,
    )
    runner.cycle_id = cycle.cycle_id
    if fae_registry is not None:
        cycle.registry = fae_registry
    _patch_internal_evidence_stages(cycle)
    return cycle


__all__ = [
    "FAE_TO_SRE_STAGE_GROUPS",
    "SRE_TO_FAE_STAGE_MAP",
    "SREFRAStageError",
    "SREFRAPipelineRunner",
    "SREGovernedFRACycle",
    "build_sre_governed_fra_cycle",
]
