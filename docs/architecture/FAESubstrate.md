# FAE Constitutional Substrate in SRE

**Status:** Partial integration (Drive-G bound)  
**Layout:** `packages/fae` (vendored FAE) · `src/sre/substrate/` (import boundary)

## Evidenced

- `pip install -e .` discovers both `fae` and `sre` (`pyproject.toml` `packages.find` where `src` + `packages`).
- `import fae` and `from sre.substrate import FactualAlignmentEngine, …` succeed (see `tests/test_substrate.py`).
- `EvidenceRegistry(..., fae_registry=…)` mirrors ACCEPTED linguistic evidence into FAE (`validation.report["fae_substrate"]`).
- API `AppState` constructs FAE via `create_fae()` and attaches `fae_registry` to the domain registry.
- IE / Mythar corpora remain under SRE `data/` and `sre.corpus` (unchanged by this merge).
- `FRAComposedReconstruction.run_recursive()` drives `SREGovernedFRACycle` with SRE→FAE stage mapping and automatic re-looping (see `tests/test_fra_mcrl_composition.py`).
- `ChronologicalReconstruction` exposes incremental stage methods (`stage_observe_ingest` … `stage_archive`) for FAE hook composition.
- Composed governed cycles record FAC-E1-compliant evidence for build/reason/update stages (`sre.substrate.fac_evidence.SREAnchoredEvidenceMixin` remaps domain inference to `EXTERNAL_DATABASE` with SRE validator id).
- `tests/test_fra_mcrl_composition.py::TestGovernedFRACycleRecursive::test_run_recursive_single_converged_cycle` asserts FAC-V2–V4 and `overall_passed` on a real-corpus recursive run (FAC-V1/V5 included in overall).
- Default `pytest` runs `tests/` (SRE + substrate). FAE self-tests under `packages/fae/tests` are present but not claimed green (pre-existing FAE compliance/MCRL failures).

## SRE → FAE stage mapping

| FAE stage | SRE stages |
|-----------|------------|
| OBSERVE | OBSERVE, INGEST |
| EXTRACT_FACTS | ATTEST |
| BUILD_MODEL | ALIGN, CLUSTER |
| REASON | INFER |
| ACT | VALIDATE |
| MEASURE_REALITY | GOVERN |
| COMPARE | CERTIFY |
| UPDATE_MODEL | ARCHIVE |
| RECURSE | auto re-loop on drift/quality |

Canonical map: `sre.fra.reconstruction_state.SRE_TO_FAE_STAGE_MAP`.

## Not claimed

- Universal FAC-V1–V5 pass on *every* composed cycle variant (only the integration test corpus path above is evidenced).
- Substitution of SRE `MCRLRosettaEngine.map_temporal` by FAE Rosetta alignments for all reconstruction paths.
- Deletion of parallel SRE `evidence` / `fra` / `mcrl` modules.
- Cutover of `G:\fae` as read-only mirror (still a separate git root).
- Green FAE package self-test suite (`packages/fae/tests`, `packages/fae/mcr/tests`).

## Import rule

Prefer `from sre.substrate import …` for constitutional symbols when writing SRE domain code. Prefer `sre.evidence.registry.EvidenceRegistry` for linguistic wire APIs. Do not import `fae.EvidenceRegistry` under the bare name `EvidenceRegistry` in domain modules — the APIs are incompatible.
