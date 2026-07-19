# Constitutional Promotion Gates — SRE v0.1

Mandatory tests SRE must pass before promotion from **Substrate → Substration → Promotion**.

Grouped by constitutional domain:

| Domain | IDs |
|--------|-----|
| FAC-E (Evidence) | FAC-E1–E4 |
| FAC-V (Reconstruction Validation) | FAC-V1–V5 |
| FRA (Nine-Stage Reconstruction) | FRA-01–04 |
| AI (Evidence-constrained intelligence) | AI-01–04 |
| CIH (Governance) | CIH-01–05 |

**Promotion rule:** SRE v0.1 **cannot be promoted** until `tests/test_constitutional.py` (`ConstitutionalPromotionTests`) passes for all gates. Substrate may ship with FAC-V / FRA / AI / CIH marked `expectedFailure` until Substration implements those layers.

Machine-readable suite: `tests/test_constitutional.py`.

---

## II. FAC-E Test Cases (Evidence Validation)

### FAC-E1 — Authenticity

| | |
|--|--|
| **Invariant** | Evidence must originate from a verifiable source. |
| **Test case** | Submit evidence with missing or invalid `source_reference`. |
| **Expected** | EvidenceRegistry rejects with FAC-E1 failure (`ConstitutionalStatus.REJECTED`; `failed_checks` contains `FAC-E1`). |

### FAC-E2 — Integrity

| | |
|--|--|
| **Invariant** | Evidence must have a correct SHA256 hash. |
| **Test case** | Submit evidence, then tamper with content and revalidate; or submit with mismatched `claimed_sha256`. |
| **Expected** | Hash mismatch detected; FAC-E2 failure. |

### FAC-E3 — Provenance

| | |
|--|--|
| **Invariant** | Provenance chain must be unbroken and non-forged. |
| **Test case** | Submit evidence with empty / `BREAK` / `TAMPERED` provenance entries. |
| **Expected** | FAC-E3 failure. |

### FAC-E4 — Constitutional Fit

| | |
|--|--|
| **Invariant** | Evidence must satisfy domain scope and governance tags. |
| **Test case** | Submit evidence with forbidden constitutional tags (e.g. `UNCONSTITUTIONAL`) or empty `submitted_by`. |
| **Expected** | FAC-E4 failure. |

---

## III. FAC-V Test Cases (Reconstruction Validation)

### FAC-V1 — Coverage

| | |
|--|--|
| **Invariant** | Reconstruction must be supported by sufficient linked evidence. |
| **Test case** | Validate reconstruction with empty / insufficient evidence set. |
| **Expected** | FAC-V1 failure. |

### FAC-V2 — Consistency

| | |
|--|--|
| **Invariant** | Linked evidence must not contradict the proto-model. |
| **Test case** | Inject mutually inconsistent lexical glosses for the same form. |
| **Expected** | FAC-V2 failure. |

### FAC-V3 — Drift Control

| | |
|--|--|
| **Invariant** | Measured drift must remain within certificate constraints. |
| **Test case** | Force drift above `max_drift` threshold. |
| **Expected** | FAC-V3 failure. |

### FAC-V4 — Alignment

| | |
|--|--|
| **Invariant** | Proto-forms must align with reference families / MCRL maps. |
| **Test case** | Align against empty or conflicting reference set. |
| **Expected** | FAC-V4 failure. |

### FAC-V5 — Governance Fit

| | |
|--|--|
| **Invariant** | Reconstruction must remain within approved project scope. |
| **Test case** | Reconstruct outside certified domains. |
| **Expected** | FAC-V5 failure. |

*(Substration: implement via `EvidenceRegistry.validate_reconstruction`.)*

---

## IV. FRA Test Cases (Nine-Stage Reconstruction)

### FRA-01 — Stage completion

| | |
|--|--|
| **Invariant** | Every reconstruction run completes OBSERVE→ARCHIVE (or fails constitutionally). |
| **Test case** | Run FRA on `data/fra_corpus_v01.json` Phase I. |
| **Expected** | All nine stages reported; terminal CERTIFY/ARCHIVE or governed failure. |

### FRA-02 — Evidence-constrained iteration

| | |
|--|--|
| **Invariant** | REFINE may not invent forms without evidence links. |
| **Test case** | Attempt refinement with empty pattern set. |
| **Expected** | Iteration blocked; no unconstrained proto-forms. |

### FRA-03 — Drift detection

| | |
|--|--|
| **Invariant** | Drift metrics are measured each TEST/REFINE cycle. |
| **Test case** | Run reconstruction and inspect drift payload. |
| **Expected** | Drift metrics present and comparable to threshold. |

### FRA-04 — Progressive refinement

| | |
|--|--|
| **Invariant** | Quality improves or run halts at quality gate. |
| **Test case** | Multi-iteration refine on Mythar Phase I–II. |
| **Expected** | Monotonic quality improvement or constitutional halt. |

---

## V. AI Test Cases (Evidence-constrained intelligence)

### AI-01 — Evidence anchoring

| | |
|--|--|
| **Invariant** | Every AI hypothesis cites evidence IDs. |
| **Test case** | `predict_proto_forms` on corpus analysis. |
| **Expected** | Each hypothesis includes non-empty evidence links. |

### AI-02 — Cognate detection

| | |
|--|--|
| **Invariant** | Cognate groups respect attested forms (e.g. `ma` / `mah`). |
| **Test case** | Analyze Mythar + Related Branch Phase I. |
| **Expected** | Cognate group linking `ma`↔`mah`. |

### AI-03 — Phonological evolution

| | |
|--|--|
| **Invariant** | Predicted shifts must match corpus rules when present. |
| **Test case** | Phase II rule `a → ah / _r`. |
| **Expected** | Phonological shift entry consistent with rule. |

### AI-04 — Constitutional validation

| | |
|--|--|
| **Invariant** | AI refine path invokes EvidenceRegistry validation. |
| **Test case** | `refine_reconstruction` returns validation payload. |
| **Expected** | `constitutional_validation` present and typed. |

---

## VI. CIH Test Cases (Governance)

### CIH-01 — Project registration

| | |
|--|--|
| **Invariant** | Projects receive stable `project_id` and UNDER_REVIEW status. |
| **Test case** | Register Mythar Phase I project. |
| **Expected** | Status `UNDER_REVIEW`. |

### CIH-02 — Evidence baseline

| | |
|--|--|
| **Invariant** | Approval requires FAC-E baseline over linked evidence. |
| **Test case** | Approve with only REJECTED evidence. |
| **Expected** | Approval blocked. |

### CIH-03 — Architecture review

| | |
|--|--|
| **Invariant** | Pipeline must declare FRA + AI + Evidence topology. |
| **Test case** | Submit project_spec missing FRA stage list. |
| **Expected** | REQUEST_CHANGES / reject. |

### CIH-04 — Certificate issuance

| | |
|--|--|
| **Invariant** | APPROVE yields Sovereign Certificate conforming to schema. |
| **Test case** | Happy-path approval with valid baseline. |
| **Expected** | Certificate validates against `schemas/sovereign_certificate.schema.json`. |

### CIH-05 — Governance trace

| | |
|--|--|
| **Invariant** | Every approval produces append-only governance trace. |
| **Test case** | Approve and export trace. |
| **Expected** | Trace validates against `schemas/governance_trace.schema.json`. |

---

## Substrate vs Substration expectations

| Gate family | Substrate (v0.1 now) | Substration |
|-------------|----------------------|-------------|
| FAC-E1–E4 | **Must pass** (minimal implementation) | Full trusted-registry / Dantomax |
| FAC-V1–V5 | `expectedFailure` until `validate_reconstruction` ships | Must pass |
| FRA-01–04 | `expectedFailure` | Must pass on corpus |
| AI-01–04 | `expectedFailure` | Must pass |
| CIH-01–05 | `expectedFailure` | Must pass + schema validation |

See also: [PromotionPlan_v01.md](../governance/PromotionPlan_v01.md).
