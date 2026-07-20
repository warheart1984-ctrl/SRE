# CIH Constitutional Kernel v1.0

**Related:** `docs/specs/CIH_ConstitutionalSpecification_v1.md` · `docs/specs/LRL_Specification_v1.md` · `docs/architecture/CRA_ReferenceArchitecture_v1.md`

---

## 1. Purpose

The CIH Constitutional Kernel defines the normative entities, lifecycle, and executable invariants that govern constitutionally supervised domains. It is implementation-neutral and serves as the portable constitutional standard for conformant runtimes.

This document specifies:

- Constitutional actors
- Normative entities
- Lifecycle stages
- Executable invariants (CIH-INV-01..05)
- Conformance gates (CIH-01..05)
- The Linguistic Reconstruction Layer (LRL) as a governed domain

---

## 2. Constitutional actors

- **Project Sponsor** — initiates reconstruction projects.
- **Reconstruction Architect** — designs FRA pipelines and domain topology.
- **HYFAL Executive Council** — deliberative governance body.
- **Sovereign Certificate Authority** — issues constitutional certificates.
- **EvidenceRegistry** — validates and records evidence.
- **Conformant Runtime** — executes governed processes under CIH.

---

## 3. Normative entities

- **ProjectSpec** — defines target language, time period, scope, constraints.
- **EvidenceBaseline** — validated initial evidence set (FAC-E1..E4).
- **ReconstructionArtifact** — proto-forms, lexicon, correspondence models.
- **CouncilDecision** — APPROVE / REJECT / REQUEST_CHANGES.
- **SovereignCertificate** — attested approval of a reconstruction project.
- **GovernanceTrace** — end-to-end record of decisions, evidence, and lineage.

---

## 4. Lifecycle

1. **Registration** — ProjectSpec created and linked to CIH context.
2. **Evidence Baseline** — EvidenceRegistry validates initial corpus.
3. **Architecture Review** — FRA pipeline and runtime topology evaluated.
4. **Governance Hearing** — HYFAL Council deliberates and decides.
5. **Certification** — SovereignCertificate issued or denied.
6. **Execution** — Conformant runtime performs governed reconstruction.
7. **Oversight** — GovernanceTrace and CEL lineage inspected.
8. **Renewal / Revocation** — certificates renewed or revoked as needed.

---

## 5. Executable invariants (CIH-INV-01..05)

- **CIH-INV-01 — No decision without evidence.**  
  All governance decisions must be backed by validated evidence entries.

- **CIH-INV-02 — No certification without lineage.**  
  Certificates must be anchored to hash-chained CEL records.

- **CIH-INV-03 — Evidence must be constitutionally fit.**  
  FAC-E1..E4 must pass for evidence to be admissible.

- **CIH-INV-04 — Reconstruction must remain within declared scope.**  
  Runtime behavior must conform to ProjectSpec constraints.

- **CIH-INV-05 — Governance must be inspectable.**  
  GovernanceTrace must be reconstructable from CEL and runtime logs.

---

## 6. Conformance gates (CIH-01..05)

Normative gate definitions (constitutional semantics):

- **CIH-01 — Evidence Gate**  
  Project may not proceed without an EvidenceBaseline.

- **CIH-02 — Architecture Gate**  
  FRA pipeline and runtime topology must be reviewed and accepted.

- **CIH-03 — Governance Gate**  
  HYFAL Council must approve before certification.

- **CIH-04 — Certification Gate**  
  Certificates must be anchored to CEL lineage.

- **CIH-05 — Oversight Gate**  
  GovernanceTrace must be available for audit.

### Gate ID mapping (normative ↔ operational)

SRE promotion tests use operational gate IDs that align with normative semantics but differ in numbering for historical reasons. Both naming schemes refer to the same constitutional obligations.

| Normative gate | Normative name | Operational ID (tests) | Operational test | Lifecycle step |
|----------------|----------------|------------------------|------------------|----------------|
| CIH-01 | Evidence Gate | **CIH-02** | `test_cih_02_evidence_baseline_blocks_rejected` | Evidence Baseline |
| CIH-02 | Architecture Gate | **CIH-03** | `test_cih_03_architecture_review` | Architecture Review |
| CIH-03 | Governance Gate | **CIH-04** (in approval path) | `test_cih_04_certificate_issuance` | Governance Hearing |
| CIH-04 | Certification Gate | **CIH-04** + **CEL-06** | `test_cih_04_certificate_issuance`, `test_cel_certification_anchor` | Certification |
| CIH-05 | Oversight Gate | **CIH-05** | `test_cih_05_governance_trace` | Oversight |
| *(prerequisite)* | Registration | **CIH-01** | `test_cih_01_project_registration` | Registration |

**Note:** Operational **CIH-01** (registration) is a prerequisite to the normative Evidence Gate, not a separate constitutional obligation. New conformant runtimes SHOULD document their gate-ID mapping in their conformance profile.

Detail: `docs/specs/CIH_ConformanceRequirements_v1.md`, `docs/specs/ConstitutionalPromotionGates.md`

---

## 7. Linguistic Reconstruction Layer (LRL)

### 7.1 Role

The **Linguistic Reconstruction Layer (LRL)** is the primary governed domain under CIH in SRE v1.0. CIH does not define specific languages; it defines how reconstruction projects earn constitutional authority.

Full domain specification: `docs/specs/LRL_Specification_v1.md`

### 7.2 Domain scope

The LRL encompasses:

- **Reconstruction languages**
  - Mythar — synthetic + living lexicon (clusters 12–80), inscription evidence, sound change.
  - Indo-European corpus — Latin/Spanish/French/Sanskrit cognate families.
- **FRA pipeline**
  - Evidence → proto-model → alignment → validation (`ChronologicalReconstruction`, 10 stages).
- **Linguistics engine**
  - Sound change, correspondence, alignment, tokenization.
- **Evidence-bound AI**
  - HLRMAIAgent — hypothesis generation and refinement constrained by evidence and CIH.

### 7.3 Relationship to CIH

- CIH governs **how** reconstruction is performed (invariants, gates, evidence).
- LRL defines **what** is reconstructed (languages, proto-forms, lexicon).
- CEL evidences **the path** from evidence to reconstruction to certification.

Independent runtimes may implement different reconstruction languages while conforming to the same CIH kernel.

---

## 8. Conformance

Runtimes demonstrate CIH conformance via:

- A **CIH Conformance Profile** (JSON) mapping:
  - `entities[]` → runtime components
  - `invariants[]` → enforcement points
  - `evidence_bindings[]` → CEL entry types and tests
  - `extensions[]` → non-core features
- A **conformance test suite** validating:
  - profile integrity
  - gate→test mapping
  - CEL bindings
  - invariant enforcement

CIH remains implementation-neutral; runtimes remain architecturally independent.

**SRE reference profile:** `docs/conformance/SRE_ConformanceProfile_v1.json`  
**CRA context:** `docs/architecture/CRA_ReferenceArchitecture_v1.md`

---

## Appendix A — Kernel topology (vertical stack)

```
                +-------------------------------------------+
                |           CIH Constitution                |
                |   (Normative Text, Articles, Principles)  |
                +-------------------------+------------------+
                                          |
                                          v
                +-------------------------------------------+
                |         CIH Constitutional Kernel          |
                |  Normative Entities + Executable Invariants|
                +-------------------------+------------------+
                                          |
                                          v
                +-------------------------------------------+
                |        CIH Conformance Requirements        |
                |        (CIH-01..05 Gates + Evidence)       |
                +-------------------------+------------------+
                                          |
                                          v
                +-------------------------------------------+
                |      Linguistic Reconstruction Layer       |
                |      (LRL — Domain Under Governance)       |
                +-------------------------+------------------+
                                          |
                                          v
                +-------------------------------------------+
                |         Conformant Runtime (SRE)           |
                |   Implements CIH entities + invariants     |
                |   Emits CEL evidence + certificates        |
                +-------------------------+------------------+
                                          |
                                          v
                +-------------------------------------------+
                |        Evidence Plane (CEL + Registry)     |
                |   FAC-E / FAC-V / Hash-chained lineage     |
                +-------------------------+------------------+
                                          |
                                          v
                +-------------------------------------------+
                |           Governance Layer (HYFAL)         |
                |   Approval, Certification, Trace Review    |
                +-------------------------------------------+
```

---

## Appendix B — Why this diagram is correct

1. **CIH governs a domain, not a runtime** — CIH is about how reconstruction earns constitutional authority; the domain is linguistic reconstruction.
2. **The LRL is the center of the system** — constitutional infrastructure exists to constrain, validate, certify, and make reconstruction inspectable.
3. **Independent runtimes can reconstruct different languages** — Proto-Semitic, Proto-Uralic, Proto-Bantu, and others may share the same CIH kernel.
4. **CEL evidences the LRL** — the Evidence Plane proves what evidence was used, which gates passed, and what lineage exists.
5. **SRE is the reference implementation** — declared via conformance profile, not embedded in the specification.
