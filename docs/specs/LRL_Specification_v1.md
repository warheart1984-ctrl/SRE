# Linguistic Reconstruction Layer (LRL) Specification v1.0

**Governed by:** `docs/specs/CIH_ConstitutionalSpecification_v1.md`  
**Kernel:** `docs/architecture/CIH_ConstitutionalKernel_v1.md`  
**Architecture:** `docs/architecture/CRA_ReferenceArchitecture_v1.md`

---

## 1. Purpose

The Linguistic Reconstruction Layer (LRL) defines the domain core governed by CIH in SRE v1.0: linguistic reconstruction of proto-forms, cognate structures, and governed lexica from evidence.

This specification is implementation-neutral and describes:

- Reconstruction languages
- FRA pipeline
- Linguistics engine
- Evidence-bound AI
- Domain invariants

---

## 2. Reconstruction languages

### 2.1 Mythar

- **Type:** Synthetic + living proto-language.
- **Artifacts:**
  - Lexicon clusters 12–80 (roots, compounds, semantic axes).
  - Inscription evidence (e.g., `ma taru en`).
  - Sound change patterns (e.g., `ma` → `mah`).
  - Evidence-tagged gap-fill entries.
- **Role:**  
  First fully worked reconstruction language in SRE, demonstrating:
  - emergent lexicon
  - heart/soul/light/blessing axes
  - cross-family convergence (Egyptian ba/ka, IE roots).

**Data:** `data/fra_corpus_v01.json`, `data/mythar_lexicon_v01.json`  
**Documentation:** `docs/architecture/MytharGapFill.md`

### 2.2 Indo-European corpus

- **Type:** Comparative reconstruction set.
- **Artifacts:**
  - Latin, Spanish, French, Sanskrit cognate families.
  - Correspondence tables.
  - Proto-form hypotheses.
- **Role:**  
  First real-world comparative reconstruction domain under CIH.

**Data:** `data/ie_cognate_expanded_v01.json`

---

## 3. FRA pipeline

### 3.1 Stages

The FRA (Formal Reconstruction Architecture) pipeline is defined as:

1. **OBSERVE** — collect evidence (inscriptions, lexicon, phonology).
2. **EXTRACT** — derive lexical, phonological, morphological, syntactic patterns.
3. **BUILD** — initialize proto-language models.
4. **TEST** — run reconstruction tests against evidence.
5. **REFINE** — iteratively reduce drift and improve fit.
6. **ALIGN** — align with known language families and historical data.
7. **VALIDATE** — run FAC-V1..V5 via EvidenceRegistry.
8. **CERTIFY** — issue reconstruction certificates via CIH.
9. **ARCHIVE** — record models, certificates, and evidence in CEL.

### 3.2 Implementation reference

- **ChronologicalReconstruction** — SRE's 10-stage implementation of FRA (`src/sre/fra/reconstruction_engine.py`, `src/sre/fra/stages.py`).
- **Methodology:** `docs/architecture/FRA_Methodology.md`

---

## 4. Linguistics engine

### 4.1 Components

- **`correspondence_engine.py`**
  - Sound correspondences across languages.
  - Cognate detection.
- **`alignment.py`**
  - Alignment of forms across corpora.
  - Temporal and phonological mapping.
- **Tokenization / normalization** (`tokenization.py`, `features.py`, `lineage.py`)
  - Canonicalization of forms.
  - Deterministic representation for hashing and evidence.

### 4.2 Responsibilities

- Maintain reproducible, inspectable transformations.
- Provide inputs to FRA and HLRMAIAgent.
- Operate strictly within CIH-defined scope.

**Package:** `src/sre/linguistics/`

---

## 5. Evidence-bound AI

### 5.1 HLRMAIAgent

- **Role:**
  - Analyze evidence patterns.
  - Generate proto-form hypotheses.
  - Refine reconstructions under FRA guidance.
- **Constraints:**
  - No free invention.
  - All hypotheses must be traceable to evidence.
  - All refinements must pass CIH gates and FAC-V validation.

**Module:** `src/sre/ai/hlrm_agent.py`

### 5.2 Domain invariants

- AI must not introduce forms without evidence lineage.
- AI outputs must be subject to the same validation as human-authored reconstructions.
- AI must be auditable via CEL entries and GovernanceTrace.

---

## 6. Domain invariants

- **LRL-INV-01 — Evidence-first reconstruction.**  
  No proto-form may exist without linked evidence.

- **LRL-INV-02 — Transparent transformation.**  
  All sound changes and alignments must be reproducible and documented.

- **LRL-INV-03 — Scope fidelity.**  
  Reconstruction must remain within declared language/time scope.

- **LRL-INV-04 — AI constraint.**  
  AI must operate as an evidence-bound assistant, not an unconstrained generator.

- **LRL-INV-05 — Lexicon governance.**  
  Lexicon entries must be evidence-tagged and lineage-anchored.

---

## 7. Relationship to CIH and CEL

- CIH defines **how** LRL is governed (invariants, gates, actors).
- LRL defines **what** is reconstructed (languages, forms, lexicon).
- CEL records **the path** from evidence to reconstruction to certification.

| LRL event | CEL entry type |
|-----------|----------------|
| Evidence accepted | `evidence` |
| Attestation registered | `attestation` |
| Correspondence found | `correspondence` |
| Hypothesis ranked | `hypothesis` |
| FAC-V validation complete | `validation` |
| Certificate issued | `certification` |
| Governance milestone | `governance` |

SRE v1.0 provides a reference implementation of LRL; other runtimes may implement different reconstruction domains while conforming to CIH.
