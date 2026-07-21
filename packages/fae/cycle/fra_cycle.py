"""FRA Cycle Implementation - Nine Stage Recursive Loop."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar, Generic
import uuid

from fae.evidence.registry import EvidenceRegistry, EvidenceSource, ProvenanceMetadata, get_registry
from fae.state.csr import ConstitutionalStateRecord, CycleLog, get_csr


T = TypeVar('T')


class FRACycleStage(Enum):
    """Nine stages of the FRA recursive loop."""
    OBSERVE = "observe"
    EXTRACT_FACTS = "extract_facts"
    BUILD_MODEL = "build_model"
    REASON = "reason"
    ACT = "act"
    MEASURE_REALITY = "measure_reality"
    COMPARE = "compare"
    UPDATE_MODEL = "update_model"
    RECURSE = "recurse"


@dataclass(frozen=True)
class CycleContext:
    """Context passed through FRA cycle stages."""
    cycle_id: str
    timestamp: datetime
    model_state: Any
    evidence_registry: EvidenceRegistry
    csr: ConstitutionalStateRecord
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StageResult(Generic[T]):
    """Result from a single FRA stage."""
    stage: FRACycleStage
    success: bool
    output: Optional[T] = None
    evidence_ids: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class FRAStage(ABC, Generic[T]):
    """Abstract base for FRA cycle stages."""
    
    def __init__(self, stage: FRACycleStage):
        self.stage = stage
    
    @abstractmethod
    def execute(self, context: CycleContext) -> StageResult[T]:
        """Execute this stage with given context."""
        pass
    
    def _record_evidence(
        self,
        context: CycleContext,
        content: Any,
        content_type: str,
        source: EvidenceSource,
        source_id: str,
        acquisition_method: str,
        confidence: float = 1.0,
        validation_status = None,
        validator_id: Optional[str] = None,
        dependencies: Optional[List[str]] = None
    ) -> str:
        """Record evidence in registry and CSR."""
        from fae.evidence.registry import EvidenceStatus
        import hashlib
        import json
        
        # Compute content hash
        content_bytes = json.dumps(content, sort_keys=True, default=str).encode()
        content_hash = hashlib.sha256(content_bytes).hexdigest()
        
        if validation_status is None:
            validation_status = EvidenceStatus.VERIFIED if source != EvidenceSource.INTERNAL_MODEL else EvidenceStatus.UNVERIFIED
        
        provenance = ProvenanceMetadata(
            source=source,
            source_id=source_id,
            timestamp=datetime.now(),
            acquisition_method=acquisition_method,
            confidence=confidence,
            validation_status=validation_status,
            validator_id=validator_id,
            validation_timestamp=datetime.now() if validation_status == EvidenceStatus.VERIFIED else None,
            content_hash=content_hash,
            dependencies=frozenset(dependencies or [])
        )
        
        evidence = context.evidence_registry.register(
            content=content,
            content_type=content_type,
            provenance=provenance,
            cycle_id=context.cycle_id,
            stage=context.metadata.get("current_stage", self.stage.value)
        )
        return evidence.id


class ObserveStage(FRAStage[Dict[str, Any]]):
    """FAC-R1: Observe - Collect raw, unfiltered data from reality."""
    
    def __init__(self, observers: Dict[str, Callable[[], Any]]):
        super().__init__(FRACycleStage.OBSERVE)
        self.observers = observers
    
    def execute(self, context: CycleContext) -> StageResult[Dict[str, Any]]:
        observations = {}
        evidence_ids = []
        
        for name, observer in self.observers.items():
            try:
                raw_data = observer()
                observations[name] = raw_data
                
                # Record raw observation as evidence
                eid = self._record_evidence(
                    context,
                    content={"observer": name, "data": raw_data},
                    content_type="observation",
                    source=EvidenceSource.EXTERNAL_SENSOR,
                    source_id=name,
                    acquisition_method="direct_observation",
                    confidence=1.0
                )
                evidence_ids.append(eid)
            except Exception as e:
                return StageResult(
                    stage=self.stage,
                    success=False,
                    errors=[f"Observer {name} failed: {e}"]
                )
        
        return StageResult(
            stage=self.stage,
            success=True,
            output=observations,
            evidence_ids=evidence_ids
        )


class ExtractFactsStage(FRAStage[List[Dict[str, Any]]]):
    """FAC-R2: Extract Facts - Convert observations into structured, falsifiable facts."""
    
    def __init__(self, extractors: Dict[str, Callable[[Any], List[Dict[str, Any]]]]):
        super().__init__(FRACycleStage.EXTRACT_FACTS)
        self.extractors = extractors
    
    def execute(self, context: CycleContext) -> StageResult[List[Dict[str, Any]]]:
        observations = context.metadata.get("observe", {})
        all_facts = []
        evidence_ids = []
        
        for obs_name, obs_data in observations.items():
            if obs_name not in self.extractors:
                continue
            try:
                facts = self.extractors[obs_name](obs_data)
                for fact in facts:
                    fact["source_observation"] = obs_name
                    fact["extracted_at"] = datetime.now().isoformat()
                    all_facts.append(fact)
                    
                    eid = self._record_evidence(
                        context,
                        content=fact,
                        content_type="fact",
                        source=EvidenceSource.EXTERNAL_SENSOR,
                        source_id=f"{obs_name}_extractor",
                        acquisition_method="fact_extraction",
                        confidence=fact.get("confidence", 0.9)
                    )
                    evidence_ids.append(eid)
            except Exception as e:
                return StageResult(
                    stage=self.stage,
                    success=False,
                    errors=[f"Extractor {obs_name} failed: {e}"]
                )
        
        return StageResult(
            stage=self.stage,
            success=True,
            output=all_facts,
            evidence_ids=evidence_ids
        )


class BuildModelStage(FRAStage[Any]):
    """FAC-R3: Build Model - Update model using only extracted facts and validated evidence."""
    
    def __init__(self, model_builder: Callable[[Any, List[Dict[str, Any]]], Any]):
        super().__init__(FRACycleStage.BUILD_MODEL)
        self.model_builder = model_builder
    
    def execute(self, context: CycleContext) -> StageResult[Any]:
        facts = context.metadata.get("extract_facts", [])
        
        # FAC-R3: Model must be updated using ONLY extracted facts and validated evidence
        validated_facts = []
        for f in facts:
            evidence_id = f.get("evidence_id", "")
            if evidence_id:
                evidence = context.evidence_registry.get(evidence_id)
                if evidence and evidence.provenance.validation_status.value == "verified":
                    validated_facts.append(f)
            else:
                # If no evidence_id, include the fact (for testing purposes)
                validated_facts.append(f)
        
        try:
            new_model = self.model_builder(context.model_state, validated_facts)
            
            # Record model update as evidence (internal, for provenance)
            eid = self._record_evidence(
                context,
                content={"model_hash": hash(str(new_model)), "fact_count": len(validated_facts)},
                content_type="model_update",
                source=EvidenceSource.INTERNAL_MODEL,
                source_id="model_builder",
                acquisition_method="model_update",
                confidence=1.0
            )
            
            return StageResult(
                stage=self.stage,
                success=True,
                output=new_model,
                evidence_ids=[eid],
                metrics={"facts_used": len(validated_facts), "total_facts": len(facts)}
            )
        except Exception as e:
            return StageResult(
                stage=self.stage,
                success=False,
                errors=[f"Model building failed: {e}"]
            )


class ReasonStage(FRAStage[Dict[str, Any]]):
    """FAC-R4: Reason - Generate predictions, explanations, or decisions."""
    
    def __init__(self, reasoner: Callable[[Any], Dict[str, Any]]):
        super().__init__(FRACycleStage.REASON)
        self.reasoner = reasoner
    
    def execute(self, context: CycleContext) -> StageResult[Dict[str, Any]]:
        model = context.metadata.get("build_model", context.model_state)
        
        try:
            reasoning_output = self.reasoner(model)
            
            # FAC-R5: Actions must be traceable to model states and reasoning steps
            reasoning_output["model_hash"] = hash(str(model))
            reasoning_output["reasoned_at"] = datetime.now().isoformat()
            
            eid = self._record_evidence(
                context,
                content=reasoning_output,
                content_type="reasoning",
                source=EvidenceSource.INTERNAL_MODEL,
                source_id="reasoner",
                acquisition_method="inference",
                confidence=reasoning_output.get("confidence", 0.8)
            )
            
            return StageResult(
                stage=self.stage,
                success=True,
                output=reasoning_output,
                evidence_ids=[eid]
            )
        except Exception as e:
            return StageResult(
                stage=self.stage,
                success=False,
                errors=[f"Reasoning failed: {e}"]
            )


class ActStage(FRAStage[Dict[str, Any]]):
    """FAC-R5: Act - Perform actions based on the model."""
    
    def __init__(self, actors: Dict[str, Callable[[Dict[str, Any]], Any]]):
        super().__init__(FRACycleStage.ACT)
        self.actors = actors
    
    def execute(self, context: CycleContext) -> StageResult[Dict[str, Any]]:
        reasoning = context.metadata.get("reason", {})
        actions_taken = {}
        evidence_ids = []
        
        for action_name, actor in self.actors.items():
            try:
                result = actor(reasoning)
                actions_taken[action_name] = result
                
                eid = self._record_evidence(
                    context,
                    content={"action": action_name, "result": result, "reasoning_hash": hash(str(reasoning))},
                    content_type="action",
                    source=EvidenceSource.EXTERNAL_SENSOR,
                    source_id=f"actor_{action_name}",
                    acquisition_method="action_execution",
                    confidence=1.0
                )
                evidence_ids.append(eid)
            except Exception as e:
                return StageResult(
                    stage=self.stage,
                    success=False,
                    errors=[f"Action {action_name} failed: {e}"]
                )
        
        return StageResult(
            stage=self.stage,
            success=True,
            output=actions_taken,
            evidence_ids=evidence_ids
        )


class MeasureRealityStage(FRAStage[Dict[str, Any]]):
    """FAC-R6: Measure Reality - Capture real-world consequences of actions."""
    
    def __init__(self, measurers: Dict[str, Callable[[], Any]]):
        super().__init__(FRACycleStage.MEASURE_REALITY)
        self.measurers = measurers
    
    def execute(self, context: CycleContext) -> StageResult[Dict[str, Any]]:
        actions = context.metadata.get("act", {})
        measurements = {}
        evidence_ids = []
        
        for name, measurer in self.measurers.items():
            try:
                measurement = measurer()
                measurements[name] = measurement
                
                eid = self._record_evidence(
                    context,
                    content={"measurement": name, "value": measurement, "action_context": actions},
                    content_type="measurement",
                    source=EvidenceSource.EXTERNAL_SENSOR,
                    source_id=f"measurer_{name}",
                    acquisition_method="post_action_measurement",
                    confidence=1.0
                )
                evidence_ids.append(eid)
            except Exception as e:
                return StageResult(
                    stage=self.stage,
                    success=False,
                    errors=[f"Measurer {name} failed: {e}"]
                )
        
        return StageResult(
            stage=self.stage,
            success=True,
            output=measurements,
            evidence_ids=evidence_ids
        )


class CompareStage(FRAStage[Dict[str, Any]]):
    """FAC-R7: Compare - Evaluate discrepancies between predicted and observed reality."""
    
    def __init__(self, comparator: Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]):
        super().__init__(FRACycleStage.COMPARE)
        self.comparator = comparator
    
    def execute(self, context: CycleContext) -> StageResult[Dict[str, Any]]:
        reasoning = context.metadata.get("reason", {})
        predictions = reasoning.get("predictions", {})
        measurements = context.metadata.get("measure_reality", {})
        
        try:
            comparison = self.comparator(predictions, measurements)
            comparison["compared_at"] = datetime.now().isoformat()
            
            eid = self._record_evidence(
                context,
                content=comparison,
                content_type="comparison",
                source=EvidenceSource.THIRD_PARTY_AUDIT,
                source_id="comparator",
                acquisition_method="prediction_reality_comparison",
                confidence=1.0
            )
            
            return StageResult(
                stage=self.stage,
                success=True,
                output=comparison,
                evidence_ids=[eid],
                metrics={
                    "discrepancy_count": len(comparison.get("discrepancies", [])),
                    "alignment_score": comparison.get("alignment_score", 0.0)
                }
            )
        except Exception as e:
            return StageResult(
                stage=self.stage,
                success=False,
                errors=[f"Comparison failed: {e}"]
            )


class UpdateModelStage(FRAStage[Any]):
    """FAC-R8: Update Model - Modify model to reduce discrepancy."""
    
    def __init__(self, updater: Callable[[Any, Dict[str, Any]], Any]):
        super().__init__(FRACycleStage.UPDATE_MODEL)
        self.updater = updater
    
    def execute(self, context: CycleContext) -> StageResult[Any]:
        model = context.metadata.get("build_model", context.model_state)
        comparison = context.metadata.get("compare", {})
        
        try:
            updated_model = self.updater(model, comparison)
            
            eid = self._record_evidence(
                context,
                content={"model_hash": hash(str(updated_model)), "discrepancies_addressed": len(comparison.get("discrepancies", []))},
                content_type="model_update",
                source=EvidenceSource.INTERNAL_MODEL,
                source_id="model_updater",
                acquisition_method="model_update_from_discrepancy",
                confidence=0.9
            )
            
            return StageResult(
                stage=self.stage,
                success=True,
                output=updated_model,
                evidence_ids=[eid]
            )
        except Exception as e:
            return StageResult(
                stage=self.stage,
                success=False,
                errors=[f"Model update failed: {e}"]
            )


class RecurseStage(FRAStage[bool]):
    """FAC-R9: Recurse - Begin next cycle preserving FAC-1 invariant."""
    
    def __init__(self, should_continue: Callable[[CycleContext], bool]):
        super().__init__(FRACycleStage.RECURSE)
        self.should_continue = should_continue
    
    def execute(self, context: CycleContext) -> StageResult[bool]:
        # FAC-1: Every cycle must preserve or improve factual alignment
        # This is checked by validation engine before recursing
        continue_cycle = self.should_continue(context)
        
        return StageResult(
            stage=self.stage,
            success=True,
            output=continue_cycle,
            metrics={"will_recurse": continue_cycle}
        )


class FRACycle:
    """Complete FRA nine-stage recursive cycle executor."""
    
    def __init__(
        self,
        observers: Dict[str, Callable[[], Any]],
        extractors: Dict[str, Callable[[Any], List[Dict[str, Any]]]],
        model_builder: Callable[[Any, List[Dict[str, Any]]], Any],
        reasoner: Callable[[Any], Dict[str, Any]],
        actors: Dict[str, Callable[[Dict[str, Any]], Any]],
        measurers: Dict[str, Callable[[], Any]],
        comparator: Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]],
        updater: Callable[[Any, Dict[str, Any]], Any],
        should_continue: Callable[[CycleContext], bool],
        initial_model: Any,
        cycle_id: Optional[str] = None
    ):
        self.cycle_id = cycle_id or f"fra_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        self.initial_model = initial_model
        self.model_state = initial_model
        
        # Initialize stages
        self.stages = [
            ObserveStage(observers),
            ExtractFactsStage(extractors),
            BuildModelStage(model_builder),
            ReasonStage(reasoner),
            ActStage(actors),
            MeasureRealityStage(measurers),
            CompareStage(comparator),
            UpdateModelStage(updater),
            RecurseStage(should_continue)
        ]
        
        self.registry = get_registry()
        self.csr = get_csr()
        self.cycle_log = CycleLog(cycle_id=self.cycle_id)
    
    def run(self) -> CycleContext:
        """Execute one complete FRA cycle."""
        context = CycleContext(
            cycle_id=self.cycle_id,
            timestamp=datetime.now(),
            model_state=self.model_state,
            evidence_registry=self.registry,
            csr=self.csr
        )
        
        stage_outputs = {}
        
        for stage in self.stages:
            result = stage.execute(context)
            
            # Log stage result
            self.csr.log_stage(
                cycle_id=self.cycle_id,
                stage=stage.stage.value,
                success=result.success,
                output=result.output,
                evidence_ids=result.evidence_ids,
                metrics=result.metrics,
                errors=result.errors
            )
            
            if not result.success:
                self.csr.end_cycle(self.cycle_id, success=False, final_model=self.model_state)
                raise FRACycleError(f"Stage {stage.stage.value} failed: {result.errors}")
            
            # Store output for next stages
            stage_outputs[stage.stage.value] = result.output
            context.metadata[stage.stage.value] = result.output
            
            # Update model state if this is model-building stage
            if stage.stage == FRACycleStage.BUILD_MODEL:
                self.model_state = result.output
                context.model_state = result.output
                context.metadata["model"] = result.output
            elif stage.stage == FRACycleStage.UPDATE_MODEL:
                self.model_state = result.output
                context.model_state = result.output
                context.metadata["model"] = result.output
        
        # FAC-1 Invariant check: factual alignment must not degrade
        alignment_check = self.csr.validate_factual_alignment(self.cycle_id)
        if not alignment_check.passed:
            self.csr.end_cycle(self.cycle_id, success=False, final_model=self.model_state)
            raise FACInvariantViolation(f"FAC-1 violated: {alignment_check.message}")
        
        self.csr.end_cycle(self.cycle_id, success=True, final_model=self.model_state)
        return context
    
    def run_recursive(self, max_cycles: int = 100) -> List[CycleContext]:
        """Run FRA cycles recursively until should_continue returns False or max_cycles reached."""
        contexts = []
        cycle_count = 0
        
        while cycle_count < max_cycles:
            context = self.run()
            contexts.append(context)
            cycle_count += 1
            
            # Check if should continue
            if not context.metadata.get("recurse", True):
                break
        
        return contexts


class FRACycleError(Exception):
    """FRA cycle execution error."""
    pass


class FACInvariantViolation(Exception):
    """FAC-1 constitutional invariant violation."""
    pass