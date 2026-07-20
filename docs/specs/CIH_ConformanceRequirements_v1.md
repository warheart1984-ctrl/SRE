# CIH Conformance Requirements v1.0

Normative conformance gates for the Constitutional Integration Hub (CIH).

**Specification:** `docs/specs/CIH_ConstitutionalSpecification_v1.md`  
**Profile schema:** `schemas/cih_conformance_profile.schema.json`

---

## I. Core CIH gates (required)

All conformant implementations MUST satisfy CIH-01 through CIH-05.

### CIH-01 — Project registration

| | |
|--|--|
| **Invariant** | Projects receive stable `project_id` and an initial review status. |
| **Test case** | Register a valid project with minimal spec. |
| **Expected** | Status `UNDER_REVIEW` (or equivalent semantic). |

### CIH-02 — Evidence baseline

| | |
|--|--|
| **Invariant** | Approval requires FAC-E baseline over all linked evidence. |
| **Test case** | Approve with only REJECTED evidence in baseline. |
| **Expected** | Approval blocked (`status` ≠ `APPROVED`). |

### CIH-03 — Architecture review

| | |
|--|--|
| **Invariant** | Pipeline must declare reconstructable topology. |
| **Test case** | Submit project spec missing required architecture fields. |
| **Expected** | `REQUEST_CHANGES` or `REJECTED`. |

### CIH-04 — Certificate issuance

| | |
|--|--|
| **Invariant** | Approved path yields Sovereign Certificate conforming to schema. |
| **Test case** | Happy-path approval with valid evidence baseline. |
| **Expected** | Certificate validates against `schemas/sovereign_certificate.schema.json`. |

### CIH-05 — Governance trace

| | |
|--|--|
| **Invariant** | Every approval produces append-only governance trace. |
| **Test case** | Approve or reject; export trace. |
| **Expected** | Trace validates against `schemas/governance_trace.schema.json`; ≥1 event. |

---

## II. CIH constitutional invariants

| ID | Invariant | Typical enforcement |
|----|-----------|---------------------|
| CIH-INV-01 | No approval without FAC-E baseline | CIH service + EvidenceRegistry |
| CIH-INV-02 | No certificate without architecture review | CIH approval pipeline |
| CIH-INV-03 | Append-only governance trace | Governance trace engine |
| CIH-INV-04 | Certificate ledger anchor (when supported) | CEL `certification` entry |
| CIH-INV-05 | Reconstructable decisions | Trace + CEL lineage |

---

## III. External prerequisites (consumed, not defined by CIH)

CIH approval depends on evidence and reconstruction layers. Conformant runtimes SHOULD document how these prerequisites are satisfied:

| Domain | Gates | Role in CIH |
|--------|-------|-------------|
| FAC-E | E1–E4 | Evidence baseline input |
| FAC-V | V1–V5 | Reconstruction validation input |
| FRA | 01–04 | Architecture / pipeline conformance |
| AI | 01–04 | Evidence-constrained intelligence |

Gate definitions: `docs/specs/ConstitutionalPromotionGates.md`

---

## IV. Conformance evidence artifacts

| Artifact | Demonstrates |
|----------|--------------|
| Conformance profile JSON | Entity mapping, enforcement, extensions |
| Promotion gate test suite | Automated invariant verification |
| Sovereign Certificate | CIH-04 output |
| Governance Trace | CIH-05 output |
| CEL `governance` entries | Runtime governance milestones |
| CEL `certification` entries | Ledger-anchored certificates |

---

## V. Extension classification

Implementations MUST classify capabilities as:

| Class | Meaning |
|-------|---------|
| **core** | Required by CIH specification |
| **required_binding** | Required for this runtime's conformance claim |
| **extension** | Beyond CIH core; optional for other runtimes |

Extensions MUST NOT be required for CIH core conformance.
