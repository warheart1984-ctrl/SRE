# SRE CIH Conformance Profile v1 — Summary

**Machine-readable source:** [`SRE_ConformanceProfile_v1.json`](SRE_ConformanceProfile_v1.json)  
**Schema:** `schemas/cih_conformance_profile.schema.json`  
**Validation:** `tests/test_cih_conformance.py`

---

## Quick scan

| Field | Value |
|-------|-------|
| Profile ID | `sre-cih-conformance-v1` |
| Profile version | `1.1.0` |
| Runtime | Sovereign Reconstruction Engine (`sre`) v1.0.0 |
| Role | Reference implementation |
| CIH spec | `docs/specs/CIH_ConstitutionalSpecification_v1.md` v1.0.0 |
| LRL plane | Linguistic Reconstruction Layer |
| Core entities | 6 |
| Required bindings | 1 (CEL) |
| Extensions | 6 |
| Invariants | 5 (4 enforced, 1 observed) |
| Conformance gates | 12 (5 CIH core + 4 FAC-E + 2 CEL + 1 attestation) |

---

## Conformance gates

| Gate | Classification | Test module |
|------|----------------|-------------|
| CIH-01 | core | `tests/test_constitutional.py` |
| CIH-02 | core | `tests/test_constitutional.py` |
| CIH-03 | core | `tests/test_constitutional.py` |
| CIH-04 | core | `tests/test_constitutional.py` |
| CIH-05 | core | `tests/test_constitutional.py` |
| FAC-E1 | prerequisite | `tests/test_constitutional.py` |
| FAC-E2 | prerequisite | `tests/test_constitutional.py` |
| FAC-E3 | prerequisite | `tests/test_constitutional.py` |
| FAC-E4 | prerequisite | `tests/test_constitutional.py` |
| CEL-06 | required_binding | `tests/test_cel.py` |
| CEL-07 | required_binding | `tests/test_cel.py` |

Automated profile validation (artifact existence, gate mapping, CEL types): `tests/test_cih_conformance.py`

---

## Core entities

| Entity | Module | Classification |
|--------|--------|----------------|
| ProjectSpec | `src/sre/governance/cih_service.py` | core |
| EvidenceBaseline | `src/sre/evidence/registry.py` | core |
| ArchitectureReview | `src/sre/governance/cih_service.py` | core |
| CIHApproval | `src/sre/governance/cih_service.py` | core |
| SovereignCertificate | `src/sre/governance/certificates.py` | core |
| GovernanceTrace | `src/sre/governance/cih_service.py` | core |
| ConstitutionalEvidenceLedger | `src/sre/evidence/cel.py` | required_binding |
| SovereignLedgerExplorer | `src/sre/evidence/ledger_explorer.py` | extension |

---

## Constitutional invariants

| ID | Enforcement | Gate |
|----|-------------|------|
| CIH-INV-01 | enforced | CIH-02 — No approval without FAC-E baseline |
| CIH-INV-02 | enforced | CIH-03 — No certificate without architecture review |
| CIH-INV-03 | enforced | CIH-05 — Append-only governance trace |
| CIH-INV-04 | enforced | CEL-06 — Certificate references real CEL entry |
| CIH-INV-05 | observed | — Governance decisions reconstructable via lineage |

---

## Reconstruction plane (LRL)

**Specification:** `docs/specs/LRL_Specification_v1.md`

| Component | Module |
|-----------|--------|
| FRA pipeline | `src/sre/fra/reconstruction_engine.py` |
| Linguistics engine | `src/sre/linguistics/correspondence_engine.py` |
| Evidence-bound AI | `src/sre/ai/hlrm_agent.py` |
| Living lexicon | `src/sre/mythar/lexicon.py` |

**Reference languages:** Mythar (synthetic living lexicon), Indo-European expanded comparative set.

**CEL bindings:** evidence, attestation, correspondence, hypothesis, validation, certification.

---

## API bindings

| Operation | Method | Path |
|-----------|--------|------|
| register_project | POST | `/api/v1/cih/projects` |
| approve_project | POST | `/api/v1/cih/projects/{project_id}/approve` |
| get_certificate | GET | `/api/v1/certificates/{certificate_id}` |

Explorer read model: `GET /api/v1/explorer/*` (see Sovereign Ledger Explorer UI).

---

## Extensions

| Extension | Module |
|-----------|--------|
| sovereign_ledger_explorer | `src/sre/api/static/explorer.html` |
| constitutional_evidence_ledger | `src/sre/evidence/cel.py` |
| remote_kms_signer | `src/sre/evidence/dantomax_signer.py` |
| correspondence_engine | `src/sre/linguistics/correspondence_engine.py` |
| mythar_lexicon | `src/sre/mythar/lexicon.py` |
| fra_ten_stage_pipeline | `src/sre/fra/reconstruction_engine.py` |

---

## Related

- `docs/specs/CIH_ConformanceRequirements_v1.md`
- `docs/architecture/CIH_ConstitutionalKernel_v1.md`
- `docs/submissions/Cambridge_SubmissionPackage_v1.md`
- `docs/governance/CIH_Mythar_RelationshipCharter_v1.md`
