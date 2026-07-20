# CIH Workflow

**Normative specification:** `docs/specs/CIH_ConstitutionalSpecification_v1.md`  
**Kernel architecture:** `docs/architecture/CIH_ConstitutionalKernel_v1.md`  
**LRL domain specification:** `docs/specs/LRL_Specification_v1.md`  
**CRA reference architecture:** `docs/architecture/CRA_ReferenceArchitecture_v1.md`  
**Conformance requirements:** `docs/specs/CIH_ConformanceRequirements_v1.md`  
**SRE reference binding:** `docs/conformance/SRE_ConformanceProfile_v1.json`

CIH (Constitutional Integration Hub) defines the constitutional environment for governed reconstruction. This document summarizes the approval workflow for operators and integrators.

## Actors

- Project Sponsor
- Reconstruction Architect
- HYFAL Executive Council
- EvidenceRegistry (logical)
- CIH Service (logical)
- Sovereign Certificate Authority
- Governance Trace Engine (logical)
- Sovereign Ledger Explorer (logical)

See also: `docs/governance/GovernanceConsensusMap_v01.md`

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
- Sovereign Certificate (`schemas/sovereign_certificate.schema.json`)
- Governance Trace (`schemas/governance_trace.schema.json`)
- CEL entries (`governance`, `certification`) when ledger is attached

## SRE reference implementation

| Component | Module |
|-----------|--------|
| CIH Governance Service | `src/sre/governance/cih_service.py` |
| Sovereign Certificate | `src/sre/governance/certificates.py` |
| CEL anchoring | `src/sre/evidence/cel.py` |

## Wire targets (SRE v1.0)

- `POST /api/v1/cih/projects`
- `POST /api/v1/cih/projects/{project_id}/approve`
- `GET /api/v1/certificates/{certificate_id}`

OpenAPI: `docs/specs/openapi.yaml`

## Conformance gates

| Gate | Test |
|------|------|
| CIH-01 | `tests/test_constitutional.py::test_cih_01_project_registration` |
| CIH-02 | `tests/test_constitutional.py::test_cih_02_evidence_baseline_blocks_rejected` |
| CIH-03 | `tests/test_constitutional.py::test_cih_03_architecture_review` |
| CIH-04 | `tests/test_constitutional.py::test_cih_04_certificate_issuance` |
| CIH-05 | `tests/test_constitutional.py::test_cih_05_governance_trace` |

Automated profile validation: `tests/test_cih_conformance.py`
