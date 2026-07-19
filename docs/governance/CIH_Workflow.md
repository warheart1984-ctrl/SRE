# CIH Workflow

FAEC Language Reconstruction Service — Constitutional Integration Hub (CIH).

## Actors

- Project Sponsor
- Reconstruction Architect
- HYFAL Executive Council
- EvidenceRegistry
- HLRMAIAgent
- Sovereign Certificate Authority

## Approval lifecycle

1. Project Registration
2. Evidence Baseline (FAC-E1–E4)
3. Architecture Review
4. HYFAL Council Hearing
5. Sovereign Certificate Issuance
6. Service Activation
7. Continuous Oversight
8. Renewal / Revocation

## Outputs

- CIH Approval
- Sovereign Certificate
- Governance Trace

## Wire targets

- `POST /api/v1/cih/projects`
- `POST /api/v1/cih/projects/{project_id}/approve`
- `GET /api/v1/certificates/{certificate_id}`

Stub: `src/sre/governance/cih_service.py`
