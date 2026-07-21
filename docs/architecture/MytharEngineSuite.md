# Mythar Expansion Architecture

**Complete future charter — Reconstruction + Construction engines**  
**Status:** Architecture (Drive-G bound) — **not** a claim that all engines are shipped  
**Lexicon baseline:** Living Lexicon v1.3 — **210 roots**, **84 clusters** (IDs 12–95)  
**Documentation law:** [`DriveG_DocumentationEvidenceLaw.md`](../governance/DriveG_DocumentationEvidenceLaw.md)  
**Companions:** [`MytharWhitePaper.md`](MytharWhitePaper.md) · [`MytharGapFill.md`](MytharGapFill.md)

> **Drive G.** Capability lists below are the **full target architecture**. Each capability is tagged **Evidenced** / **Partial** / **Intent**. Presence in this charter does not mean a runtime module exists under that name.

---

## You now have the full architecture

| Set | Role | Engines |
|-----|------|---------|
| **SET I — Reconstruction** | Reach **backward** into deep time; proto-world structures | **PWRM** · **SDS** · **LTG** |
| **SET II — Construction** | Move **forward** into a complete linguistic ecosystem | **GSD** · **GE1** · **CDS** |

This is the **complete Mythar Expansion Architecture** — the intended future of the system — constrained by the v1.3 core freeze (no routine root admission) and by Drive G (docs ≤ evidence).

```
                         ┌─────────────────────────────────┐
                         │  CDS — Constitutional kernel    │
                         │  (strongest evidenced layer)    │
                         └───────────────┬─────────────────┘
         SET I ◄─────────────────────────┼─────────────────────────► SET II
    PWRM → SDS → LTG                     │                    GSD → GE1
    (backward / proto)                   │                 (forward / ecosystem)
                                         ▼
                    Mythar Living Lexicon v1.3 (expansion frozen)
```

Inventory note: legacy “207 roots / 83 clusters” is superseded by **210 / 84** after PGC v1.3.

---

## SET I — The Reconstruction Engines

Engines that recreate lost languages and generate proto-forms for hypothetical ancestral cultures. Unlabeled “proto” output without FAC-E tags or explicit invention status violates LRL-INV-01 / Drive G.

---

### 1. Proto-World Reconstruction Mode (PWRM)

**Purpose:** Recreate lost languages and generate proto-forms for hypothetical ancestral cultures.

#### Capabilities

| Capability | Status | Evidence / gap |
|------------|--------|----------------|
| Generate proto-roots from semantic universals | **Partial** | 210 Living Lexicon roots + `proto_world_comparisons`; no dedicated proto-root generator |
| Reconstruct proto-clusters from force-phonology | **Intent** | PGC-3 force language is design constraint only |
| Produce proto-world lexicons | **Intent** | Comparison table ≠ generated lexicon |
| Model pre-family linguistic states | **Intent** | — |
| Generate mythic proto-texts | **Partial** | Invocation / ritual phrases in lexicon JSON |
| Produce ceremonial proto-registers | **Partial** | Publishable ritual / cosmology docs |
| Create proto-script variants | **Partial** | `Mythar_ProtoScript_FontSpec_v1.md` + writing system docs |

#### Governance

| Control | Status |
|---------|--------|
| CEL lineage | **Partial** — deferred `cel_lineage` on roots/clusters |
| Evidence dependencies | **Evidenced** — `cra_governance.evidence_dependency` |
| Assurance levels | **Evidenced** |
| Ratification workflow | **Partial** — lifecycle states present; promotion not automated |
| Artifact lifecycle states | **Evidenced** — Draft → Review → Ratified → Active |

---

### 2. Semantic Drift Simulation (SDS)

**Purpose:** Simulate how languages evolve over centuries or millennia.

#### Capabilities

| Capability | Status | Evidence / gap |
|------------|--------|----------------|
| Phonological drift vectors | **Intent** | — |
| Semantic broadening / narrowing | **Intent** | — |
| Polysemy expansion rules | **Partial** | PGC constrains *allowed* polysemy; does not time-evolve it |
| Cluster divergence models | **Intent** | — |
| Sound-change laws | **Partial** | Publishable `Mythar_SoundChangeLaws_v1.md`; `sre.ai.sound_change` is generic FRA/AI helper |
| Dialect formation | **Intent** | — |
| Historical layering (Old → Middle → Modern Mythar) | **Intent** | No layered lexicon eras in data |

#### Outputs (target)

| Output | Status |
|--------|--------|
| Daughter languages | **Intent** |
| Dialect families | **Intent** |
| Drift timelines | **Intent** |
| Evolutionary maps | **Intent** |
| Proto-to-modern lineage | **Intent** |

#### Governance

| Control | Status |
|---------|--------|
| Drift constraints | **Intent** |
| Stability classes | **Intent** (assurance levels ≠ SDS stability classes) |
| Evidence tracking | **Partial** — base lexicon CRA/FAC-E only |
| Revision history | **Evidenced** on PGC-corrected forms; not drift-event history |

---

### 3. Lineage Tree Generation (LTG)

**Purpose:** Build genealogical trees for roots, clusters, dialects, and entire language families.

#### Capabilities

| Capability | Status | Evidence / gap |
|------------|--------|----------------|
| Root inheritance graphs | **Intent** | — |
| Cluster evolution graphs | **Intent** | — |
| Semantic axis lineage | **Partial** | Axes on polysemous roots; no graph export |
| Drift-based branching | **Intent** | Depends on SDS |
| Proto-to-daughter mapping | **Intent** | — |
| CEL lineage integration | **Partial** | Deferred fields + `linguistics/lineage.format_human_lineage` for FRA traces |

#### Outputs (target)

| Output | Status |
|--------|--------|
| Full lineage trees | **Intent** |
| Semantic ancestry maps | **Intent** |
| Drift timelines | **Intent** |
| Proto-world → Mythar → dialects → descendants | **Intent** |

#### Governance

| Control | Status |
|---------|--------|
| Artifact lifecycle states | **Evidenced** (lexicon entries) |
| Constitutional lineage registry | **Intent** — CEL charter exists; Mythar entries not bound |
| Ratification workflow | **Partial** |
| Versioning | **Partial** — `lexicon_version` 1.3 |

---

## SET II — The Construction Engines

Engines that let Mythar move **forward** and become a complete linguistic ecosystem.

---

### 4. Glyph System Design (GSD)

**Purpose:** Create Mythar’s writing system and visual semantic geometry.

#### Capabilities

| Capability | Status | Evidence / gap |
|------------|--------|----------------|
| Root glyphs (210 target; not 207) | **Intent** | No per-root glyph registry in code |
| Cluster glyphs (84 target; not 83) | **Intent** | — |
| Axis glyphs | **Partial** | Axis graphemes in writing-system docs |
| Stroke order rules | **Partial** | Writing system / poster specs |
| Semantic geometry | **Partial** | Same |
| Proto-script variants | **Partial** | ProtoScript font spec |
| Ceremonial glyph families | **Partial** | Ritual / cosmology publishables |
| Directionality rules | **Partial** | Writing system docs |

#### Outputs (target)

| Output | Status |
|--------|--------|
| Full Mythar script | **Partial** (spec, not GSD module) |
| Proto-glyphs / ritual glyphs | **Partial** (docs) |
| Semantic glyph maps | **Partial** (docs) |
| Glyph lineage registry | **Intent** |

#### Governance

| Control | Status |
|---------|--------|
| Glyph lifecycle | **Intent** |
| Revision history | **Intent** (for glyphs) |
| Ratification workflow | **Intent** |
| Evidence dependencies | **Intent** for glyphs; CDS fields cover lexicon only |

**Drive G:** Publishable writing docs must not claim CEL-anchored / certified glyphs until ledger IDs and certification exist.

---

### 5. Grammar Engine v1.0 (GE1)

**Purpose:** Turn Mythar into a fully functional language.

#### Capabilities

| Capability | Status | Evidence / gap |
|------------|--------|----------------|
| Morphology | **Partial** | `Mythar_Grammar_v1.md` |
| Syntax | **Partial** | Same |
| Case system | **Partial** / **Intent** | Spec prose depth varies |
| Aspect | **Partial** / **Intent** | Spec prose |
| Evidentiality | **Partial** / **Intent** | Spec prose |
| Derivational logic | **Partial** | Compound clusters + grammar doc |
| Compounding rules | **Partial** | Living Lexicon compounds |
| Sentence formation | **Partial** | Ritual phrases; no parser |
| Poetic and ceremonial registers | **Partial** | Publishable ritual syntax |

#### Outputs (target)

| Output | Status |
|--------|--------|
| Mythar Grammar v1.0 | **Partial** — markdown, not `src/sre/mythar/grammar*` |
| Syntax Specification | **Partial** |
| Morphology Tables | **Partial** |
| Poetic / Ceremonial Register | **Partial** |
| Conformance tests | **Intent** for GE1 (lexicon CRA tests ≠ grammar engine tests) |

#### Governance

| Control | Status |
|---------|--------|
| Grammar lifecycle | **Intent** |
| Evidence dependencies | **Intent** |
| Ratification workflow | **Intent** |
| Versioning | **Partial** — document version labels only |

---

### 6. Constitutional Documentation Suite (CDS)

**Purpose:** Govern Mythar like a constitutional system, not a dictionary.

**Note:** Strongest suite member relative to current implementation evidence.

#### Capabilities

| Capability | Status | Evidence / gap |
|------------|--------|----------------|
| Root artifact template | **Evidenced** | `cra_governance` on every root |
| Cluster artifact template | **Evidenced** | `cra_governance` on every cluster |
| Identity | **Evidenced** | `mythar:root:…` / `mythar:cluster:…` |
| Justification dependency | **Evidenced** | |
| Evidence dependency | **Evidenced** | |
| Assurance level | **Evidenced** | experimental \| candidate \| validated |
| Lifecycle state | **Evidenced** | Draft → Review → Ratified → Active |
| CEL lineage | **Partial** | deferred placeholders |
| Revision history | **Evidenced** (PGC v1.3 corrections) | |
| Ratification workflow | **Partial** | states yes; workflow automation no |
| Conformance rules | **Partial** | `validate_governance_record` + tests; JSON Schema unused by CI |
| PGC (polysemy law) | **Evidenced** | PGC-1…5 |
| Drive G (doc evidence law) | **Evidenced** | governance doc |
| Expansion freeze | **Evidenced** as declarative metadata | not a runtime gate |

#### Outputs (target)

| Output | Status |
|--------|--------|
| Mythar Lexicon Constitution | **Partial** — White paper + GapFill + PGC + CRA model |
| Mythar Artifact Registry | **Partial** — lexicon JSON as root/cluster registry |
| Mythar Evidence Layer | **Partial** — FAC-E seed; CEL deferred |
| Mythar Governance Kernel | **Partial** — `governance.py` + CIH/CEL docs |
| Stability Class definitions | **Intent** as named CDS/SDS classes |
| Constitutional review process | **Partial** / **Intent** |

#### Governance

| Control | Status |
|---------|--------|
| Constitutional ratification | **Partial** |
| Artifact lifecycle | **Evidenced** (fields) |
| Versioning | **Partial** — lexicon 1.3 |
| Deprecation rules | **Intent** |
| Evidence governance | **Partial** — CRA + FAC-E; CEL bind open |

---

## Suite evidence matrix

| Engine | Code today | Docs today | Overall |
|--------|------------|------------|---------|
| **PWRM** | FRA + Mythar lexicon + proto_world table | White paper | **Partial scaffold** |
| **SDS** | Generic sound_change helper | SoundChangeLaws publishable | **Mostly intent** |
| **LTG** | Lineage formatter | CRA/CEL charters | **Mostly intent** |
| **GSD** | — | Writing / ProtoScript publishables | **Docs only** |
| **GE1** | — | Grammar / RitualSyntax publishables | **Docs only** |
| **CDS** | `governance.py`, `data.py`, tests | White paper, GapFill, Drive G, CRA | **Strongest evidenced** |

---

## Expansion under freeze

Core lexicon **root/cluster expansion is frozen** (declared policy). The Expansion Architecture advances by building **engines and conformance**, not by admitting more roots.

**Recommended order**

1. **CDS** — schema-in-CI, CEL bind, optional freeze gate  
2. **PWRM** thin slice — invention vs comparison modes; FAC-E1-only emitters  
3. **LTG** thin slice — graphs from existing CRA/axis/revision fields  
4. **GE1** — conformance tests against lexicon before “engine” claim  
5. **GSD** — glyph registry under CDS fields; Drive-G scrub of writing claims  
6. **SDS** — last; requires fixtures before Old/Middle/Modern labels  

---

## Non-claims

- Engine names are architecture IDs, not proof of `src/sre/mythar/pwrm.py` (etc.).
- Proto-World comparison rows are not PWRM lexicons.
- Publishable grammar/script markdown is not GE1/GSD runtime.
- Deferred CEL lineage is not completed constitutional anchoring.
- “Complete architecture” means **complete charter**, not complete implementation.

---

## References

- [`MytharWhitePaper.md`](MytharWhitePaper.md)  
- [`MytharGapFill.md`](MytharGapFill.md)  
- [`DriveG_DocumentationEvidenceLaw.md`](../governance/DriveG_DocumentationEvidenceLaw.md)  
- [`CRA_ReferenceArchitecture_v1.md`](CRA_ReferenceArchitecture_v1.md)  
- [`CEL_Charter_v01.md`](../governance/CEL_Charter_v01.md)  
- `src/sre/mythar/{data,governance,lexicon}.py`  
- `src/sre/fra/reconstruction_engine.py`  
- `docs/mythar/publishable/`  

---

*Document class: Mythar Expansion Architecture · Baseline: v1.3 · Sets I–II complete as charter · Drive G: bound*
