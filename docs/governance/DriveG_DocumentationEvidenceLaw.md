# Drive G Law — Documentation Evidence Bound

**ID:** Drive-G-1  
**Scope:** Entire Drive `G:\` (all projects — not Mythar-only)  
**Canonical ledger:** [`G:\DRIVE_G_LAWS.md`](../../../DRIVE_G_LAWS.md)  
**Companion standard:** Drive-G-2 — [`DriveG_MaturityDimensionsStandard.md`](./DriveG_MaturityDimensionsStandard.md)  
**Status:** Standing law

## Law

> **No documentation claim may exceed the implementation evidence behind it.**

This file is a **project mirror** for SRE/Mythar editors. Authority and scope live in the Drive G ledger. Do not restate this law as Mythar-scoped.

## Meaning

1. **Assert only what code, tests, schemas, or ledger rows prove.**  
   Policy intent, roadmaps, and call-to-action language must be labeled as such.
2. **Prefer weaker verbs when evidence is partial.**  
   Use *aligns with*, *declares*, *prepares*, *tests* — not *implements*, *enforces*, or *binds* — unless those stronger states are demonstrated.
3. **Separate layers of evidence.**

   | Evidence | May support claims about |
   |----------|--------------------------|
   | Source module + regenerator | Data shape, counts, exported fields |
   | Unit / integration tests | Checked invariants at test time |
   | JSON Schema file alone | Intended contract (not runtime enforcement unless loaded) |
   | CI workflow | Continuous enforcement |
   | CEL / Dantomax receipts | Ledger lineage / binding |

4. **Deferred or placeholder state is not completion.**  
   Example: `cel_lineage.binding_status=deferred` supports “lineage-prepared,” not “lineage-anchored” or “CEL-bound.”
5. **Freeze / ratification / exception gates** stated only in docs or JSON policy metadata are **declarative** until a runtime or CI gate rejects violations.

## Application in Mythar docs (example, not limit)

When editing Mythar architecture docs (`MytharWhitePaper.md`, `MytharGapFill.md`, CRA/CEL cross-refs):

- Inventory counts and field presence → cite `data.py` / regenerated JSON / `tests/test_mythar_lexicon.py`.
- PGC rules → cite `PGC_CONTRACT` + tests that assert axes / splits.
- CRA fields → cite `governance.py` + `validate_governance_record` in tests.
- CEL binding → cite deferred placeholders unless a bound `cel_entry_id` exists in evidence.
- Expansion freeze → cite `cra_governance_model.expansion_policy`; do not claim CEL exception gating is enforced unless implemented.

The same evidence-bound standard applies to every other project on `G:\`.

## Remediation

If a doc claim outruns evidence: downgrade the claim, move it to a roadmap section, or add the missing implementation/test before restoring the stronger wording.
