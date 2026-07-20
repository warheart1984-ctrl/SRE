# Constitutional Integration Hub (CIH) — Constitutional Specification v1.0

## Preamble

The **Constitutional Integration Hub (CIH)** defines the implementation-neutral constitutional environment for **governed linguistic reconstruction** within the CIEMS Sovereignty Stack.

**Primary domain:** the Linguistic Reconstruction Layer (LRL) — recovering proto-forms, cognate structure, and lexicon from evidence. CIH governs reconstruction projects; it does not perform reconstruction itself.

CIH is a **specification**, not a runtime. It defines:

- Normative entities and actors
- Constitutional invariants and conformance requirements
- Approval lifecycle and required outputs
- Evidence expectations for audit and interoperability

Executable runtimes (for example, the Sovereign Reconstruction Engine) **implement** CIH requirements. They do not substitute for this specification.

**Authority:** HYFAL Executive Council  
**Status:** Ratified v1.0  
**Supersedes:** governance sections embedded in runtime-specific specifications  
**Kernel architecture:** `docs/architecture/CIH_ConstitutionalKernel_v1.md`  
**Domain specification (LRL):** `docs/specs/LRL_Specification_v1.md`  
**Reference architecture (CRA):** `docs/architecture/CRA_ReferenceArchitecture_v1.md`

---

## Article I — Purpose & Scope

### §1 Purpose

CIH exists to make constitutional governance **inspectable, portable, and enforceable** across independent implementations.

Every conformant runtime MUST be able to demonstrate:

1. How projects enter constitutional review
2. How evidence baselines gate approval
3. How architecture and scope are validated
4. How sovereign authority is issued and anchored
5. How governance decisions remain reconstructable

### §2 Scope

CIH governs **project approval, certification, and governance traceability**.

CIH does **not** define:

- Evidence ingestion mechanics (see FAC-E specifications)
- Reconstruction algorithms (see FRA specifications)
- AI inference methods (see constitutional AI constraints)
- Runtime deployment topology (see enterprise layer specifications)

CIH **consumes** outputs from reconstruction and evidence layers and **requires** that certification rest on validated evidence and traceable decisions.

See **Reconstruction Plane (LRL):** `docs/architecture/CIH_ConstitutionalKernel_v1.md` §3.2

### §3 Relationship to runtimes

| Layer | Role |
|-------|------|
| **CIH (this document)** | Normative constitutional standard |
| **Conformance profile** | Runtime declaration of how CIH is implemented |
| **Reference runtime (e.g. SRE)** | Executable demonstration of conformance |
| **CEL / ledger substrates** | Evidence artifacts that demonstrate conformance |

---

## Article II — Constitutional Environment

### §1 Sovereignty stack position

CIH sits in the **governance layer** of the CIEMS Sovereignty Stack:

```
Evidence (FAC-E) ──► Reconstruction (FRA / FAC-V) ──► Governance (CIH) ──► Certification
```

No constitutional decision MAY proceed without constitutional evidence. No service MAY operate outside sovereign certificate authority.

### §2 Global invariants (CIH-relevant)

These invariants bind all conformant implementations:

| ID | Invariant |
|----|-----------|
| **CIH-INV-01** | No approval without an evidence baseline satisfying FAC-E1–E4 over linked evidence. |
| **CIH-INV-02** | No certificate without completed architecture review. |
| **CIH-INV-03** | Every approval produces an append-only governance trace. |
| **CIH-INV-04** | Every sovereign certificate references a ledger anchor (not a placeholder). |
| **CIH-INV-05** | Every governance decision MUST be reconstructable from trace + ledger evidence. |

---

## Article III — Normative Entities

### §1 Actors

| Actor | Responsibility |
|-------|----------------|
| **Project Sponsor** | Initiates reconstruction project; supplies ProjectSpec |
| **Reconstruction Architect** | Declares pipeline topology (evidence, FRA, AI integration) |
| **EvidenceRegistry** (logical) | Supplies evidence baseline report (FAC-E1–E4) |
| **CIH Service** (logical) | Orchestrates approval lifecycle |
| **HYFAL Executive Council** | Constitutional approval authority |
| **Sovereign Certificate Authority** | Issues and signs Sovereign Certificates |
| **Governance Trace Engine** (logical) | Records append-only governance events |
| **Ledger Explorer** (logical) | Read model for certificates, traces, and lineage |

Actors MAY be human, institutional, or automated services. CIH defines **roles**, not implementations.

### §2 Entity model

| Entity | Description | Required fields (normative) |
|--------|-------------|----------------------------|
| **ProjectSpec** | Declared reconstruction scope | `project_id`, `target_language`, `time_period`, `evidence_sources`, `architecture` |
| **EvidenceBaseline** | FAC-E validation summary over linked evidence | per-evidence status, aggregate pass/fail |
| **ArchitectureReview** | Pipeline topology validation | FRA stage coverage, evidence + AI bindings |
| **CIHApproval** | Governance decision | `status`, `project_id`, `reason` (if not approved) |
| **SovereignCertificate** | Issued constitutional authority | schema: `schemas/sovereign_certificate.schema.json` |
| **GovernanceTrace** | Append-only decision log | schema: `schemas/governance_trace.schema.json` |

### §3 Approval lifecycle

Conformant implementations MUST support this lifecycle (states MAY be named differently; semantics MUST match):

1. **Project Registration** — stable `project_id`, initial review status
2. **Evidence Baseline** — FAC-E1–E4 over all linked evidence
3. **Architecture Review** — pipeline topology declared and validated
4. **Council Hearing** — approval decision with constraints
5. **Certificate Issuance** — sovereign certificate conforming to schema
6. **Service Activation** — certified scope becomes operable
7. **Continuous Oversight** — traceable governance events during operation
8. **Renewal / Revocation** — certificate lifecycle management

### §4 Required outputs

Every approval attempt MUST produce:

- **CIH Approval** (status + rationale)
- **Governance Trace** (append-only events)
- **Sovereign Certificate** (only on APPROVED path)

---

## Article IV — Conformance Requirements

Normative gate definitions: `docs/specs/CIH_ConformanceRequirements_v1.md`

| Gate | Requirement |
|------|-------------|
| **CIH-01** | Project registration yields stable `project_id` and review status |
| **CIH-02** | Approval blocked when evidence baseline contains REJECTED evidence |
| **CIH-03** | Incomplete architecture yields REQUEST_CHANGES or REJECTED |
| **CIH-04** | APPROVED path yields Sovereign Certificate validating against schema |
| **CIH-05** | Every approval produces governance trace validating against schema |

Implementations MUST map each gate to automated tests or auditable procedures documented in their conformance profile.

---

## Article V — Evidence & Audit

### §1 Conformance evidence

Independent auditors MUST be able to answer:

| Question | Evidence source |
|----------|-----------------|
| Which CIH entities are implemented? | Conformance profile `entities[]` |
| Which invariants are enforced? | Conformance profile `invariants[]` + gate tests |
| What demonstrates conformance? | CEL entries, certificates, traces, test results |
| What goes beyond core CIH? | Conformance profile `extensions[]` |

### §2 Ledger anchoring

When a constitutional evidence ledger (CEL) is present, conformant runtimes SHOULD record:

| CEL entry type | CIH milestone |
|----------------|---------------|
| `governance` | Baseline verified, council events, approval decisions |
| `certification` | Sovereign certificate issued |

Certificates MUST reference a real ledger entry in `signatures.ledger_entry_id` when ledger anchoring is supported.

### §3 Consensus topology

Normative actor flows: `docs/governance/GovernanceConsensusMap_v01.md`

---

## Article VI — API Surface (informative)

CIH does not mandate wire formats. Reference bindings for interoperability:

| Operation | Reference endpoint |
|-----------|-------------------|
| Register / submit project | `POST /api/v1/cih/projects` |
| Approve project | `POST /api/v1/cih/projects/{project_id}/approve` |
| Retrieve certificate | `GET /api/v1/certificates/{certificate_id}` |

OpenAPI reference: `docs/specs/openapi.yaml`

---

## Article VII — Versioning & Conformance Profiles

### §1 Specification versioning

CIH specifications use semantic versioning. Breaking changes to normative entities or gates require a major version bump.

### §2 Conformance profiles

Each runtime publishes a machine-readable profile:

- Schema: `schemas/cih_conformance_profile.schema.json`
- Reference profile: `docs/conformance/SRE_ConformanceProfile_v1.json`

Profiles MUST declare:

- CIH specification version claimed
- Entity → implementation mapping
- Invariant → enforcement mapping
- Gate → test mapping
- CEL evidence bindings (if applicable)
- Extensions beyond core CIH

---

## Ratification

CIH Constitutional Specification v1.0 is ratified as the implementation-neutral governance standard for the CIEMS Sovereignty Stack.

Runtime-specific specifications (for example, `ConstitutionalSpecification_v01.md`) MUST reference this document for governance normative content and MUST NOT redefine CIH entities or invariants in conflicting terms.
