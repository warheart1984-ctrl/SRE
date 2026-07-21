"""Pydantic models for SRE API request/response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

# --- Evidence ---


class EvidenceSubmission(BaseModel):
    evidence_id: str
    evidence_type: str = "inscription"
    source_reference: str = ""
    content: dict[str, Any]
    submitted_by: str
    provenance_chain: list[str] = Field(default_factory=list)
    constitutional_tags: list[str] = Field(default_factory=list)
    claimed_sha256: str | None = None


class ValidationReport(BaseModel):
    evidence_id: str
    is_valid: bool
    failed_checks: list[str] = Field(default_factory=list)
    report: dict[str, Any] = Field(default_factory=dict)
    validated_at: str = ""


class EvidenceRecord(BaseModel):
    evidence_id: str
    evidence_type: str
    source_reference: str
    content: dict[str, Any]
    created_at: str
    submitted_by: str
    sha256_hash: str
    provenance_chain: list[str] = Field(default_factory=list)
    constitutional_tags: list[str] = Field(default_factory=list)


class EvidenceSubmitResponse(BaseModel):
    evidence_id: str
    status: str
    sha256_hash: str
    validation_report: ValidationReport | dict[str, Any] = Field(default_factory=dict)


class EvidenceGetResponse(BaseModel):
    evidence: EvidenceRecord
    status: str | None = None
    validation_report: ValidationReport | dict[str, Any] = Field(default_factory=dict)


# --- Corpus ingest ---


class CorpusIngestRequest(BaseModel):
    records: list[dict[str, Any]]

    @field_validator("records")
    @classmethod
    def records_not_empty(cls, v: list) -> list:
        if not v:
            raise ValueError("records array is required and must not be empty")
        return v


class CorpusIngestResponse(BaseModel):
    ingested: int
    accepted: int
    rejected: int
    evidence_ids: list[str]


# --- Reconstruction ---


class ReconstructionRequest(BaseModel):
    target_language: str
    time_period: str
    evidence_sources: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    corpus: str = "mythar"
    corpus_path: str | None = None
    constraints: dict[str, Any] = Field(default_factory=dict)
    require_attestation_lineage: bool = False


class ReconstructionValidationResponse(BaseModel):
    evidence_id: str
    is_valid: bool
    failed_checks: list[str] = Field(default_factory=list)
    report: dict[str, Any] = Field(default_factory=dict)
    validated_at: str = ""


# --- CIH ---


class CIHProjectRequest(BaseModel):
    project_id: str
    spec: dict[str, Any] = Field(default_factory=dict)


class CIHProjectApprove(BaseModel):
    spec: dict[str, Any] = Field(default_factory=dict)


class CIHProjectResponse(BaseModel):
    project_id: str
    status: str
    reason: str = ""
    trace_id: str = ""
    governance_trace: dict[str, Any] = Field(default_factory=dict)
    certificate_id: str | None = None


# --- CEL ---


class CELEntryOut(BaseModel):
    cel_entry_id: str
    entry_type: str
    subject_id: str
    payload: dict[str, Any] = Field(default_factory=dict)
    links: list[str] = Field(default_factory=list)
    timestamp: str = ""
    position: int = 0
    prev_cel_hash: str = ""
    cel_hash: str = ""
    checksum: str = ""
    dantomax_record_id: str | None = None
    dantomax_ledger_hash: str | None = None
    constitutional_article: str = ""


class CELHeadResponse(BaseModel):
    version: str = "1.0"
    length: int = 0
    head: str = ""
    fabric_root_hash: str = ""
    by_type: dict[str, int] = Field(default_factory=dict)
    dantomax_head: str | None = None
    integrity: dict[str, Any] = Field(default_factory=dict)


class CELEntriesResponse(BaseModel):
    entries: list[CELEntryOut] = Field(default_factory=list)
    total: int = 0
    limit: int = 100
    offset: int = 0
    head: str = ""
    fabric_root_hash: str = ""


class CELLineageResponse(BaseModel):
    reconstruction_id: str
    cel_head: str = ""
    fabric_root_hash: str = ""
    entries_by_type: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    path: list[str] = Field(default_factory=list)
    entry_count: int = 0
    human_readable: str = ""


# --- Explorer ---


class ExplorerFabricResponse(BaseModel):
    fabric: dict[str, Any] = Field(default_factory=dict)


class ExplorerEntryResponse(BaseModel):
    entry: dict[str, Any] = Field(default_factory=dict)


class ExplorerReconstructionResponse(BaseModel):
    reconstruction: dict[str, Any] = Field(default_factory=dict)


class ExplorerEntriesResponse(BaseModel):
    entries: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0
    limit: int = 100
    offset: int = 0


class ConformanceGate(BaseModel):
    gate_id: str = ""
    classification: str = ""
    test_module: str = ""
    test_name: str = ""
    ci_status: str = "profiled"


class ConformanceSummary(BaseModel):
    status: str = "profiled"
    profile_id: str = ""
    profile_version: str = ""
    runtime: dict[str, Any] = Field(default_factory=dict)
    counts: dict[str, int] = Field(default_factory=dict)
    gates: list[ConformanceGate] = Field(default_factory=list)
    references: dict[str, str] = Field(default_factory=dict)


# --- Health ---


class HealthResponse(BaseModel):
    status: str = "ok"
    api_version: str = "1.0.0"
    cel_length: int = 0
    signing_mode: str = ""
    persist_backend: str = ""
