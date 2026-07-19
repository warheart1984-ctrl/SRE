# API Contracts — SRE v0.1

RESTful, versioned, constitutional, microservice-aligned.

## 1. EvidenceRegistry API

### `POST /api/v1/evidence`

Submit new linguistic evidence for FAC-E1–E4 validation.

**Request:** EvidenceSubmission (`evidence_id`, `evidence_type`, `source_reference`, `content`, `submitted_by`, optional `provenance_chain`, `constitutional_tags`).

**Response:** `{ evidence_id, status, sha256_hash, validation_report_id }`

### `GET /api/v1/evidence/{evidence_id}`

Evidence record + constitutional status + validation report.

### `GET /api/v1/evidence/{evidence_id}/validation`

FAC-E1–E4 validation report only.

## 2. FRA Reconstruction API

### `POST /api/v1/reconstruction`

Start FRA run. Request: `project_id`, `target_language`, `time_period`, `evidence_sources`, optional `constraints`.

**Response:** `{ reconstruction_id, status, fra_stage }`

### `GET /api/v1/reconstruction/{reconstruction_id}`

State + proto model + certificate_id.

### `GET /api/v1/reconstruction/{reconstruction_id}/validation`

FAC-V1–V5 validation report.

## 3. HLRMAIAgent API

### `POST /api/v1/ai/analyze`

`{ evidence_ids: [...] }` → EvidenceAnalysis

### `POST /api/v1/ai/protoforms`

`{ analysis_id, target_language }` → ProtoFormHypotheses

## 4. CIH Governance API

### `POST /api/v1/cih/projects`

Register project → `{ project_id, status: UNDER_REVIEW }`

### `POST /api/v1/cih/projects/{project_id}/approve`

Approval → `{ project_id, status: APPROVED, certificate_id }`

### `GET /api/v1/certificates/{certificate_id}`

Sovereign Certificate document.

## Machine-readable

See [openapi.yaml](./openapi.yaml) (OpenAPI 3.0.3).
