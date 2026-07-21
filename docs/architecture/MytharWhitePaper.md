# Mythar Living Lexicon — Technical White Paper

**Version:** 1.3 (PGC era)  
**Status:** Core lexicon freeze *(declared policy)* · documentation / conformance / tooling priority  
**Canonical engine:** Sovereign Reconstruction Engine (SRE)  
**Repository:** https://github.com/warheart1984-ctrl/mythar-sre  
**Companion inventory:** [`MytharGapFill.md`](MytharGapFill.md)  
**Engine suite charter:** [`MytharEngineSuite.md`](MytharEngineSuite.md) (Mythar Expansion Architecture — SET I PWRM/SDS/LTG · SET II GSD/GE1/CDS — Drive-G ranked)  
**Documentation bound:** [`DriveG_DocumentationEvidenceLaw.md`](../governance/DriveG_DocumentationEvidenceLaw.md) — no claim may exceed implementation evidence

| Artifact | Path | Evidence role |
|----------|------|----------------|
| Canonical source | `src/sre/mythar/data.py` | Authoritative lexicon + PGC |
| CRA governance | `src/sre/mythar/governance.py` | Field builders + `validate_governance_record` |
| Query API | `src/sre/mythar/lexicon.py` | Load / query / seed FAC-E |
| Generated JSON | `data/mythar_lexicon_v01.json` | Regenerated export |
| CRA schema | `schemas/mythar_cra_governance.schema.json` | Published contract *(not yet loaded in CI)* |
| Regenerator | `scripts/generate_mythar_lexicon.py` | Deterministic write path |
| Tests | `tests/test_mythar_lexicon.py` | PGC + CRA field checks |

---

## 0. Drive G — evidence bound

Per **Drive-G-1**, every assertive sentence below is limited to what implementation evidence supports. Roadmap and ratification language is labeled **intent**. Deferred CEL placeholders are **not** treated as completed lineage binding.

---

## 1. Abstract

Mythar is a **living lexicon** inside the Sovereign Reconstruction Engine: an evidence-constrained invented language whose roots, clusters, and polysemy axes are exported with machine-readable CRA fields and checked by unit tests. Lexicon **v1.3** declares core expansion **frozen** at **210 roots** and **84 clusters** (IDs 12–95), adopts the **Polysemy Governance Contract (PGC-1…PGC-5)** in source and JSON, and attaches **CRA governance metadata** to every root and cluster—identity, justification and evidence dependencies, assurance level, lifecycle state, CEL lineage *placeholders*, and revision history.

This paper synthesizes the philosophical stance, stack position, lexicon design, growth history (Proposals A–M), PGC audit outcomes, CRA alignment as implemented, inventory snapshot, and a post-freeze roadmap (**intent**). It is the freeze *document* for the core lexicon; runtime freeze enforcement and CEL binding remain open work.

**Non-claim (stated once):** Proto-World and IE-shaped notes in the lexicon are **comparisons and design constraints**, not proven reconstructions or established cognate sets.

---

## 2. Mission and philosophical stance

### 2.1 What Mythar is for

Mythar exists so that SRE can exercise reconstruction pathways—EvidenceRegistry (FAC-E), FRA, optional CEL/Dantomax configuration—against a language that is:

1. **Internally coherent** (axial semantics, domain coverage, compound morphology — evidenced in lexicon data + gap-fill tests);
2. **Externally honest** (tagged as invention / Gap-Fill Draft, not as recovered proto-forms);
3. **Governable at data level** (PGC in `data.py`; CRA fields via `governance.py`; both exercised in tests).

It is the primary **reference reconstruction language** for LRL *as used in this SRE tree*, while remaining **proprietary IP** governed by—but not constitutive of—CIH ([`CIH_Mythar_RelationshipCharter_v1.md`](../governance/CIH_Mythar_RelationshipCharter_v1.md)).

### 2.2 Evidence-constrained invention

Gap-fill admission is **evidence-constrained invention**, not free coinage:

- Roots and clusters carry FAC-E1-tagged source reference `Mythar Living Lexicon / Gap-Fill Draft` in the exported document.
- They may feed FRA / cognate *analysis* pipelines while remaining distinguishable from external corpora (e.g. IE mini-set).
- Proto-World rows (`proto_world_comparisons`) are design analogies; they do not certify historical relatedness.

This stance **aligns with** LRL invariants ([`LRL_Specification_v1.md`](../specs/LRL_Specification_v1.md)):

| Invariant | Mythar evidence today | Not yet evidenced |
|-----------|----------------------|-------------------|
| **LRL-INV-01** (no proto-form without linked evidence) | Invented forms are FAC-E1-tagged drafts, not unlabeled “proto” claims | Full FRA gate blocking untagged forms in all paths |
| **LRL-INV-05** (evidence-tagged and lineage-anchored) | Evidence IDs + CRA fields + deferred `cel_lineage.subject_id` | Bound `cel_entry_id` on ledger rows |

### 2.3 Axial semantics

Mythar semantics are **axial**, not flat categorical labels. Stable polysemy is allowed only where senses share a documented continuum (intensity→purity, flow→life-flow, etc.), recorded in `ALLOWED_POLYSEMY`. Broader cosmology lives in publishable axial materials; the Living Lexicon operationalizes PGC axes on roots. PGC-3’s vowel-core / consonant-force language is a **constitutional design constraint** documented with the contract—not a separate morphophonological engine.
---

## 3. Constitutional architecture

### 3.1 Stack position *(normative docs + this SRE tree)*

```
CIH (normative rules — docs)
  └─ LRL (reconstruction domain — Mythar + peer corpora)
       └─ SRE runtime (EvidenceRegistry, FRA, HLRMAIAgent; CEL when configured)
            └─ CEL (append-only evidence plane; Dantomax as optional crypto substrate)
                 └─ Governance (certificates, promotion gates — doc + partial runtime)
```

CRA separates graphs ([`CRA_ReferenceArchitecture_v1.md`](CRA_ReferenceArchitecture_v1.md)). Mythar **exports** the following fields today:

| Graph | Question | Mythar fields (exported) |
|-------|----------|---------------------------|
| **Justification** | Why may this entry exist? | `identity`, `justification_dependency` |
| **Evidence** | Why trust it operationally? | `evidence_dependency`, `assurance_level`, `cel_lineage` *(deferred)* |
| **Governance** | Where is it in the lifecycle? | `lifecycle_state`, `revision_history` |

### 3.2 Vowel-core / consonant-force

PGC-3 requires axes to be **constitutional** in Mythar’s design language—roughly vowel-core and consonant-force continuums. Failure of a shared axis triggers PGC-5 (split or drop). Evidence: PGC text + audited root glosses + `PGC_CORRECTIONS` / revision history—not an automated axis classifier.

### 3.3 FRA and Dantomax

- **FRA** ([`FRA_Methodology.md`](FRA_Methodology.md)): methodology doc; Mythar is a corpus target in SRE demos/tests.
- **FAC-E**: EvidenceRegistry acceptance path used by `MytharLexicon.seed_registry`.
- **Dantomax**: optional integrity client in tests when configured.
- **CEL**: charter and writer exist in the stack; Mythar entries ship **`binding_status=deferred`** until a seed writes ledger IDs and code updates lineage (not automatic today).

Mythar is governed by CIH policy docs; Mythar content is not an open CIH artifact.
---

## 4. Lexicon design

### 4.1 Units

| Unit | Role |
|------|------|
| **Root** | Atomic (or named compound) form with domain, meaning, optional polysemy axis, `evidence_id`, `cra_governance` |
| **Cluster** | Ordered forms + ritual/domain phrase + interpretation; IDs 12–95 |
| **Compound** | Morphological products (e.g. `lmakra`, `yuckara`, ritual compounds on clusters 47+) |
| **Domain** | `kinship` · `body` · `motion` · `abstract` · `nature` |

### 4.2 Identity and evidence IDs

| Kind | Identity | Evidence subject |
|------|----------|------------------|
| Root | `mythar:root:{form}` | `evid_myt_root_{form}` |
| Cluster | `mythar:cluster:{id:02d}` | `evid_myt_cluster_{id:02d}` |

### 4.3 Engine surface

```python
from sre.mythar import MytharLexicon

lex = MytharLexicon()
lex.cluster_ids()         # 12..95
lex.gap_fill()            # domain coverage
lex.compare_proto_world() # comparison table (not cognate proof)
lex.seed_registry(reg)    # FAC-E seed
# Per-entry CRA:
lex.roots()[0]["cra_governance"]
lex.get_cluster(12)["cra_governance"]
```

Canonical write path: edit `data.py` → `python scripts/generate_mythar_lexicon.py` → JSON + tests.

---

## 5. Growth history (Proposals A–M)

Expansion proceeded as governed proposals, not an open vocabulary dump.

| Proposal | Focus | Cluster range (approx.) |
|----------|--------|-------------------------|
| **A** | Kinship triad gaps (`pa` / `ma` / `ti` / `ne` / `bro`) | 12–22 |
| **B** | Body–sense inventory | 13, 23–28 |
| **C** | Motion verbs | 14, 29–34 |
| **D** | Knowing–spirit set | 15, 35–40 |
| **E** | Nature triad + light | 16, 41–46 |
| **F** | Kra-axis compounds (`lmakra` / `yuckara`) | 47 |
| **G** | Blessing / birth triad | 48 |
| **H** | Naming / blessing / sealing | 49–60 |
| **I** | Ritual invocation lines | 61–64 |
| **J** | Extended ritual triads | 65–80 |
| **K** | Proto-World universal mini-clusters | 81–87 |
| **L** | Social / body / action / nature / logic / spatial gap-fill | 88–94 |
| **M** | PGC corrections and axis validation | 95 |

Proposals **K–L** remain at **candidate / Review** until explicit ratification. Proposal **M** admits cluster `95` (`pu hu duma`) and records PGC-5 splits (`duma`, `taga`, `alo`, stone at `ska`/`krato`). Full cluster tables live in [`MytharGapFill.md`](MytharGapFill.md); this paper does not duplicate them.

---

## 6. Polysemy Governance Contract (PGC)

Adopted in v1.3 as constitutional law for multi-sense roots (`polysemy_governance` in the lexicon document; source: `PGC_CONTRACT` in `data.py`).

### 6.1 Rules

| ID | Rule |
|----|------|
| **PGC-1** | Polysemy requires a shared semantic axis |
| **PGC-2** | Axes must be explicit in the lexicon entry |
| **PGC-3** | Axes must be constitutional (vowel-core / consonant-force semantics) |
| **PGC-4** | Axes must be testable (≥1 cluster where both senses appear without contradiction) |
| **PGC-5** | No axis → no polysemy (split or remove the weaker sense) |

### 6.2 Stable polysemy (post-audit)

| Root | Axis | Senses (abbrev.) |
|------|------|------------------|
| fi | intensity → purity | fire · sacred-verity |
| ru | flow → life-flow | rest-flow · blood |
| pu | motion → living motion | move · animal |
| vi | perception → awareness → life | knowing-see · living |
| ra | scale → magnitude | intensify · great/big/many |
| ma | origin → life → mother | mother · life/origin |
| ka | weight → authority → age | force · elder |
| la | elevation → illumination | light · sky/above |
| nu | sense-aperture | nose/breath · ear |
| to | agency | hand · give/take |
| ta | deixis | this/that only |
| du | burden | bad/heavy only |
| ti | diminutive | small / sacred diminutive |

Register hygiene: `ver` = cognitive truth; `kor` = anatomical heart vs `rama` = feeling-heart; child as independent root `chi` (not overloaded on `ti`).

### 6.3 PGC-5 corrections (Proposal M)

| Root | Violation | Disposition |
|------|-----------|-------------|
| to | stone ≠ agency | stone → `ska` / `krato` |
| ta | foot/stand ≠ deixis | foot/stand → `pe` / `taga` |
| du | two ≠ burden | two → `duma` |

Revision history for these forms (and companions `alo`, `pe`, cluster 95) is append-only under `cra_governance.revision_history` (version `1.3`, dated 2026-07-20 in governance module).

---

## 7. Evidence governance and CRA alignment

### 7.1 Per-entry record (`mythar.cra_governance.v1`)

**Implemented:** builders in `src/sre/mythar/governance.py`; export on every root/cluster via `build_lexicon_document()`; structural checks via `validate_governance_record` in `tests/test_mythar_lexicon.py`.

**Published but not runtime-enforced:** `schemas/mythar_cra_governance.schema.json` (no CI step currently loads this schema).

| Field | Meaning | Evidence |
|-------|---------|----------|
| `identity` | `mythar:root:…` / `mythar:cluster:…` | Exported + tested |
| `justification_dependency` | Why entitled to exist | Exported + tested |
| `evidence_dependency` | FAC-E1 / Proto-World / test clusters text | Exported + tested |
| `assurance_level` | experimental \| candidate \| validated | Classifier + tests |
| `lifecycle_state` | Draft → Review → Ratified → Active | Classifier + tests |
| `cel_lineage` | `binding_status` + `subject_id` | Deferred placeholders; `cel_entry_id` absent until bound |
| `revision_history` | Append-only change log | PGC v1.3 entries tested on corrected forms |

### 7.2 Classification defaults

| Class | Assurance | Lifecycle | Evidence |
|-------|-----------|-----------|----------|
| Core clusters 12–46 | validated | Active | `classify_cluster_governance` + tests |
| Compound / ritual 47–80 | validated | Active | same |
| Proposals K–L (81–94) | candidate | Review | same |
| Proposal M (95) | candidate | Review | same + revision history |
| PGC-stable polysemy | validated | Active | polysemy map + tests |
| PGC v1.3 corrections / splits | validated | Active | revision map + tests |

### 7.3 CEL binding *(intent protocol; deferred today)*

As shipped, `cel_lineage.binding_status` is **`deferred`**, with `subject_id` equal to the Mythar `evidence_id`. **No Mythar export currently sets `bound`.** Intended binding sequence (**roadmap**):

1. `MytharLexicon.seed_registry` → EvidenceRegistry;
2. CEL `record_evidence` with that `subject_id` (when CEL is configured);
3. update export / binder so `cel_entry_id` is set and `binding_status=bound`.

Charter: [`CEL_Charter_v01.md`](../governance/CEL_Charter_v01.md).
---

## 8. Current inventory snapshot

| Metric | Value | Evidence |
|--------|-------|----------|
| Lexicon ID | `mythar_lexicon_v01` | JSON / `build_lexicon_document` |
| Version | **1.3** | `lexicon_version` field |
| Roots | **210** | `root_count` + tests |
| Clusters | **84** (IDs **12–95**) | `cluster_count` + tests |
| Domains | kinship, body, motion, abstract, nature | gap-fill thresholds in tests |
| PGC rules | 5 | `PGC_CONTRACT` + tests |
| Stable polysemy entries | 13 | `ALLOWED_POLYSEMY` length |
| Expansion policy | **`frozen`** *(declared in JSON model)* | `cra_governance_model.expansion_policy` — **not** a runtime reject gate |
| CRA model schema id | `mythar.cra_governance.v1` | governance module + tests |
| CEL binding | deferred placeholders | all exports `binding_status=deferred` |

Strategic posture (**policy**): prefer documentation, conformance, and tooling over more roots. Claiming that freeze exceptions *require* a CEL governance record is **intent** until a gate enforces it.

---

## 9. Conformance, tooling, and reproducibility roadmap

*(All rows below are **intent** unless marked **evidenced**.)*

| Priority | Work | Status |
|----------|------|--------|
| **Docs** | Keep this paper + GapFill + CRA/CEL charters aligned under Drive G | Ongoing |
| **Conformance** | `validate_governance_record` on all entries | **Evidenced** in `tests/test_mythar_lexicon.py` |
| **Conformance** | Load JSON Schema in CI | **Intent** — schema file exists, unused by CI |
| **Conformance** | Automated PGC-4 “both senses in cluster” checker | **Intent** — axes + `test_clusters` listed; not auto-proven |
| **Tooling** | Single regenerator path | **Evidenced** |
| **Tooling** | Assurance dashboards / Explorer CEL UX | **Intent** |
| **Reproducibility** | Deterministic JSON from `build_lexicon_document()` | **Evidenced** by regenerator + tests |
| **Ratification** | Promote K–L–M Review → Ratified → Active | **Intent** — classifiers still emit Review for K–L–M |
| **CEL** | Clear deferred bindings | **Intent** |
| **Freeze gate** | Reject new roots without CEL exception | **Intent** — policy metadata only |

Demo loop (**evidenced** commands in-repo):

```powershell
python scripts/generate_mythar_lexicon.py
python scripts/run_local.py --corpus mythar-lex --dantomax
pytest -q tests/test_mythar_lexicon.py
```

---

## 10. What Mythar is not

- **Not** a claim that listed Proto-World or IE-shaped forms are proven cognates or recovered proto-language.
- **Not** an unconstrained conlang sandbox; entries are expected to carry FAC-E tags and PGC/CRA fields as exported.
- **Not** part of the open CIH standard; frameworks may cite Mythar as reference language without receiving Mythar IP ([Cambridge package](../submissions/Cambridge_SubmissionPackage_v1.md) excludes proprietary lexicon).
- **Not** a substitute for FRA validation or Sovereign Certificates—those remain pipeline/governance outputs when run.
- **Not** CEL-bound by default in v1.3 exports (deferred lineage only).
- **Not** runtime-frozen: expansion freeze is declared policy, not an admissions lock in code.

Commercial positioning documents (`docs/commercial/Mythar_Whitepaper_v1.md` and brand materials) are separate from this **architecture** white paper and must also obey Drive G when they assert engineering facts.

---

## 11. Conclusion — freeze document, mature governance

Mythar v1.3 closes a coherent *data* arc: domain triads → compound/ritual morphology → Proto-World gap-fill → polysemy law → CRA metadata fields. Treat the core lexicon as **frozen for expansion as declared policy**, and treat open work as **governance maturity**—Drive-G-honest docs, schema-in-CI, CEL binding, and selective ratification of candidate K–L–M material.

**Call to action (intent):** Keep `data.py` as sole canonical source; bind deferred CEL lineages when the seed→ledger path is wired; measure progress by assurance transitions and reproducible tooling, not by root count; never restore stronger doc claims without stronger evidence ([Drive G](../governance/DriveG_DocumentationEvidenceLaw.md)).

---

## References (in-repo)

- [`docs/architecture/MytharEngineSuite.md`](MytharEngineSuite.md) — Reconstruction (PWRM/SDS/LTG) + Construction (GSD/GE1/CDS) charter  
- [`docs/governance/DriveG_DocumentationEvidenceLaw.md`](../governance/DriveG_DocumentationEvidenceLaw.md) — documentation evidence bound  
- [`docs/architecture/MytharGapFill.md`](MytharGapFill.md) — living inventory and cluster tables  
- [`docs/architecture/CRA_ReferenceArchitecture_v1.md`](CRA_ReferenceArchitecture_v1.md) — Justification vs Evidence graphs  
- [`docs/governance/CEL_Charter_v01.md`](../governance/CEL_Charter_v01.md) — evidence plane  
- [`docs/governance/CIH_Mythar_RelationshipCharter_v1.md`](../governance/CIH_Mythar_RelationshipCharter_v1.md) — open stack vs Mythar IP  
- [`docs/specs/LRL_Specification_v1.md`](../specs/LRL_Specification_v1.md) — LRL-INV-01 / LRL-INV-05  
- [`docs/architecture/FRA_Methodology.md`](FRA_Methodology.md) — reconstruction stages  
- `src/sre/mythar/{data,governance,lexicon}.py` — executable lexicon + CRA field builders  

---

*Document class: architecture white paper · Lexicon era: v1.3 PGC · Expansion: frozen (declared) · Drive G: bound*
