"""Compose SRE ChronologicalReconstruction onto FAE FRACycle.



SRE's 10-stage linguistic pipeline maps onto FAE's 9-stage constitutional loop:



| FAE stage         | SRE stages        |

|-------------------|-------------------|

| OBSERVE           | OBSERVE, INGEST   |

| EXTRACT_FACTS     | ATTEST            |

| BUILD_MODEL       | ALIGN, CLUSTER    |

| REASON            | INFER             |

| ACT               | VALIDATE          |

| MEASURE_REALITY   | GOVERN            |

| COMPARE           | CERTIFY           |

| UPDATE_MODEL      | ARCHIVE           |

| RECURSE           | (auto re-loop)    |



``FRAComposedReconstruction.run_recursive()`` drives ``SREGovernedFRACycle``

with automatic re-looping until drift/quality converge or ``max_fae_cycles``.

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fae.api import EvidenceRegistry as FAEEvidenceRegistry
from fae.cycle.fra_cycle import CycleContext, FRACycleError
from fae.drift.detection import (
    DriftDetectionEngine,
    DriftEvent,
    DriftSeverity,
    DriftType,
)
from fae.evidence.registry import get_registry as get_fae_registry
from fae.governance.hooks import FACGovernanceHooks
from fae.metrics.validation import ValidationMetricsEngine
from fae.state.csr import get_csr

from .fra_stage_runner import (
    FAE_TO_SRE_STAGE_GROUPS,
    SRE_TO_FAE_STAGE_MAP,
    SREFRAPipelineRunner,
    SREGovernedFRACycle,
    build_sre_governed_fra_cycle,
)

if TYPE_CHECKING:
    from ..fra.reconstruction_engine import ChronologicalReconstruction


class FRAComposedReconstruction:
    """Run SRE ChronologicalReconstruction through a FAE GovernedFRACycle."""

    def __init__(
        self,
        domain_engine: ChronologicalReconstruction,
        *,
        fae_registry: FAEEvidenceRegistry | None = None,
        governance_hooks: FACGovernanceHooks | None = None,
        drift_threshold: float = 0.6,
        quality_gate: float = 0.35,
        max_fae_cycles: int = 5,
        use_governed_cycle: bool = True,
    ) -> None:

        self.domain_engine = domain_engine

        self._fae_registry = fae_registry or get_fae_registry()

        self._csr = get_csr()

        self._drift_engine = DriftDetectionEngine(self._fae_registry, self._csr)

        self._validation_engine = ValidationMetricsEngine(self._fae_registry, self._csr)

        self._governance = governance_hooks or FACGovernanceHooks(component_id="sre.fra.composed")

        self._drift_threshold = drift_threshold

        self._quality_gate = quality_gate

        self._max_fae_cycles = max_fae_cycles

        self._use_governed_cycle = use_governed_cycle

        self._target_language = ""

        self._time_period = ""

        self._evidence_sources: list[str] = []

        self._cycle: SREGovernedFRACycle | None = None

        self._runner: SREFRAPipelineRunner | None = None

    def _build_cycle(
        self,
        target_language: str,
        time_period: str,
        evidence_sources: list[str],
    ) -> SREGovernedFRACycle:

        self._target_language = target_language

        self._time_period = time_period

        self._evidence_sources = list(evidence_sources)

        cycle = build_sre_governed_fra_cycle(
            self.domain_engine,
            target_language=target_language,
            time_period=time_period,
            evidence_sources=evidence_sources,
            fae_registry=self._fae_registry,
            governance_hooks=self._governance,
            drift_threshold=self._drift_threshold,
            quality_gate=self._quality_gate,
            max_fae_cycles=self._max_fae_cycles,
        )

        self._cycle = cycle

        self._runner = cycle.runner

        return cycle

    def run_recursive(
        self,
        target_language: str,
        time_period: str,
        evidence_sources: list[str],
        *,
        max_cycles: int | None = None,
    ) -> RecursiveCompositionResult:
        """Execute full GovernedFRACycle with automatic re-looping."""

        cycle = self._build_cycle(target_language, time_period, evidence_sources)

        try:
            contexts = cycle.run_recursive(max_cycles=max_cycles)

        except FRACycleError as exc:
            domain_result = (cycle.runner.domain_result if cycle.runner else None) or {
                "status": "FAILED",
                "reason": str(exc),
                "metrics": {},
            }

            return RecursiveCompositionResult(
                contexts=[],
                domain_result=domain_result,
                iterations=0,
                converged=False,
                drift_events=[],
            )

        domain_result = cycle.runner.domain_result if cycle.runner else {}

        if not domain_result and contexts:
            final_model = contexts[-1].model_state

            if isinstance(final_model, dict):
                domain_result = final_model

        drift = float(
            (domain_result or {}).get(
                "drift", (domain_result or {}).get("metrics", {}).get("drift", 1.0)
            )
        )

        quality = float(
            (domain_result or {}).get(
                "quality", (domain_result or {}).get("metrics", {}).get("quality", 0.0)
            )
        )

        status = str((domain_result or {}).get("status", "FAILED"))

        drift_events = self._collect_drift_events(contexts, drift)

        converged = (
            status == "COMPLETED"
            and drift <= self._drift_threshold
            and quality >= self._quality_gate
        )

        return RecursiveCompositionResult(
            contexts=contexts,
            domain_result=domain_result or {},
            iterations=len(contexts),
            converged=converged,
            drift=drift,
            quality=quality,
            drift_events=drift_events,
        )

    def run(
        self,
        target_language: str,
        time_period: str,
        evidence_sources: list[str],
    ) -> ComposedReconstructionResult:
        """Execute one governed FAE cycle (single iteration)."""

        if not self._use_governed_cycle:
            return self._run_legacy_pass(target_language, time_period, evidence_sources)

        recursive = self.run_recursive(target_language, time_period, evidence_sources, max_cycles=1)

        last = recursive.contexts[-1] if recursive.contexts else None

        return ComposedReconstructionResult(
            domain_result=recursive.domain_result,
            cycle_id=last.cycle_id if last else "sre-fra-none",
            iteration=1,
            drift=recursive.drift,
            quality=recursive.quality,
            drift_events=recursive.drift_events,
            should_continue=not recursive.converged
            and recursive.domain_result.get("status") == "COMPLETED",
            fae_context=last,
        )

    def _run_legacy_pass(
        self,
        target_language: str,
        time_period: str,
        evidence_sources: list[str],
    ) -> ComposedReconstructionResult:
        """Single-pass wrapper for non-ChronologicalReconstruction engines."""

        cycle_id = "sre-fra-legacy"

        self._governance.on_cycle_start(
            cycle_id,
            {
                "target_language": target_language,
                "time_period": time_period,
                "evidence_sources": evidence_sources,
            },
        )

        domain_result = self.domain_engine.reconstruct_language(
            target_language, time_period, evidence_sources
        )

        metrics = domain_result.get("metrics", {})

        drift = float(metrics.get("drift", 1.0))

        quality = float(metrics.get("quality", 0.0))

        status = domain_result.get("status", "FAILED")

        drift_events: list[DriftEvent] = []

        if drift > self._drift_threshold:
            event = DriftEvent(
                cycle_id=cycle_id,
                drift_type=DriftType.ALIGNMENT_DEGRADATION,
                severity=DriftSeverity.MEDIUM,
                message=f"SRE drift {drift:.3f} exceeds threshold {self._drift_threshold}",
                metrics={"domain_drift": drift, "threshold": self._drift_threshold},
            )

            drift_events.append(event)

        should_continue = status == "COMPLETED" and drift <= self._drift_threshold and quality > 0.0

        return ComposedReconstructionResult(
            domain_result=domain_result,
            cycle_id=cycle_id,
            iteration=1,
            drift=drift,
            quality=quality,
            drift_events=drift_events,
            should_continue=should_continue,
        )

    def _collect_drift_events(self, contexts: list[CycleContext], drift: float) -> list[DriftEvent]:

        events: list[DriftEvent] = []

        for ctx in contexts:
            if drift > self._drift_threshold:
                events.append(
                    DriftEvent(
                        cycle_id=ctx.cycle_id,
                        drift_type=DriftType.ALIGNMENT_DEGRADATION,
                        severity=DriftSeverity.MEDIUM,
                        message=(
                            f"SRE drift {drift:.3f} exceeds threshold {self._drift_threshold}"
                        ),
                        metrics={
                            "domain_drift": drift,
                            "threshold": self._drift_threshold,
                        },
                    )
                )

                self._csr.log_drift_event(events[-1])

        return events


class ComposedReconstructionResult:
    """Result from a single FAE-governed reconstruction pass."""

    __slots__ = (
        "domain_result",
        "cycle_id",
        "iteration",
        "drift",
        "quality",
        "drift_events",
        "should_continue",
        "fae_context",
    )

    def __init__(
        self,
        *,
        domain_result: dict[str, Any],
        cycle_id: str,
        iteration: int,
        drift: float,
        quality: float,
        drift_events: list[DriftEvent],
        should_continue: bool,
        fae_context: CycleContext | None = None,
    ) -> None:

        self.domain_result = domain_result

        self.cycle_id = cycle_id

        self.iteration = iteration

        self.drift = drift

        self.quality = quality

        self.drift_events = drift_events

        self.should_continue = should_continue

        self.fae_context = fae_context

    @property
    def status(self) -> str:

        return self.domain_result.get("status", "UNKNOWN")

    @property
    def reconstruction_id(self) -> str | None:

        return self.domain_result.get("reconstruction_id")


class RecursiveCompositionResult:
    """Result from ``run_recursive`` — all FAE cycle contexts plus domain output."""

    __slots__ = (
        "contexts",
        "domain_result",
        "iterations",
        "converged",
        "drift",
        "quality",
        "drift_events",
    )

    def __init__(
        self,
        *,
        contexts: list[CycleContext],
        domain_result: dict[str, Any],
        iterations: int,
        converged: bool,
        drift: float = 1.0,
        quality: float = 0.0,
        drift_events: list[DriftEvent] | None = None,
    ) -> None:

        self.contexts = contexts

        self.domain_result = domain_result

        self.iterations = iterations

        self.converged = converged

        self.drift = drift

        self.quality = quality

        self.drift_events = drift_events or []

    @property
    def status(self) -> str:

        return self.domain_result.get("status", "UNKNOWN")


__all__ = [
    "ComposedReconstructionResult",
    "FRAComposedReconstruction",
    "RecursiveCompositionResult",
    "FAE_TO_SRE_STAGE_GROUPS",
    "SRE_TO_FAE_STAGE_MAP",
]
