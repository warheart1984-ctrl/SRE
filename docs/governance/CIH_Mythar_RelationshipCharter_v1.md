# CIH–Mythar Relationship Charter v1.0

**Ratified:** Draft v1.0  
**Mythar owner:** Jon Halstead

This charter defines the boundary between the **open constitutional stack** and **proprietary Mythar language IP**.

---

## 1. Separation of concerns

| Layer | Role | Status |
|-------|------|--------|
| **CIH** | Constitutional governance | Open standard |
| **LRL** | Reconstruction domain specification | Open standard |
| **CEL** | Evidence plane | Open specification |
| **SRE** | Reference runtime | Open implementation |
| **Mythar** | Proprietary reconstruction language | **Licensed IP** |

Mythar is **governed by** CIH. Mythar is **not part of** CIH.

---

## 2. Governance relationship

```
Evidence → FRA/LRL reconstruction → CEL lineage → CIH approval → Sovereign Certificate
                                              ↑
                                         Mythar scope
                                         (ProjectSpec.target_language)
```

| Actor / system | Mythar relationship |
|----------------|---------------------|
| CIH | Governs Mythar reconstruction **projects** |
| CEL | Anchors Mythar lexicon and certification **evidence** |
| SRE | Executes Mythar reconstruction in reference runtime |
| HYFAL / Certificate Authority | Issues certificates scoped to Mythar projects |
| **Mythar content** | **Owned separately; licensed for use** |

---

## 3. Ownership

| Asset | Owner / license |
|-------|-----------------|
| **Mythar** (lexicon, cosmology, ritual syntax, writing system) | Jon Halstead — proprietary |
| **CIH** | Open constitutional standard |
| **LRL, CRA, FRA, CEL specs** | Open |
| **SRE** | Reference implementation (open) |

No CIH document grants Mythar IP rights to implementers or academic partners.

---

## 4. Academic access

| Open | Closed |
|------|--------|
| CIH Constitutional Kernel | Mythar lexicon (commercial) |
| LRL Specification | Mythar branded publications |
| FRA methodology | Mythar IDE (commercial) |
| CEL Charter | Unlicensed derivative Mythar works |

Academic partners may study CIH and build independent runtimes for **other** languages without Mythar license.  
See: `docs/submissions/Cambridge_SubmissionPackage_v1.md`

---

## 5. Conformance without IP transfer

A runtime may declare CIH conformance (`docs/conformance/SRE_ConformanceProfile_v1.json`) while using Mythar only as a **reference language** in development. Commercial Mythar use requires separate license: `docs/commercial/Mythar_LicensingModel_v1.md`.

---

## Related documents

- `docs/commercial/Mythar_CommercializationPlan_v1.md`
- `docs/commercial/Mythar_IPProtectionStrategy_v1.md`
- `docs/architecture/CIH_ConstitutionalKernel_v1.md` §7 (LRL — Mythar as reference, not normative)
