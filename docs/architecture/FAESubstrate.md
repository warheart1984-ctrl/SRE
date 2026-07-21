# FAE Constitutional Substrate in SRE

**Status:** Partial integration (Drive-G bound)  
**Layout:** `packages/fae` (vendored FAE) · `src/sre/substrate/` (import boundary)

## Evidenced

- `pip install -e .` discovers both `fae` and `sre` (`pyproject.toml` `packages.find` where `src` + `packages`).
- `import fae` and `from sre.substrate import FactualAlignmentEngine, …` succeed (see `tests/test_substrate.py`).
- `EvidenceRegistry(..., fae_registry=…)` mirrors ACCEPTED linguistic evidence into FAE (`validation.report["fae_substrate"]`).
- API `AppState` constructs FAE via `create_fae()` and attaches `fae_registry` to the domain registry.
- IE / Mythar corpora remain under SRE `data/` and `sre.corpus` (unchanged by this merge).
- Default `pytest` runs `tests/` (SRE + substrate). FAE self-tests under `packages/fae/tests` are present but not claimed green (pre-existing FAE compliance/MCRL failures).

## Not claimed

- End-to-end substitution of `ChronologicalReconstruction` by FAE `FRACycle`.
- Substitution of SRE `MCRLRosettaEngine.map_temporal` by FAE Rosetta alignments.
- Deletion of parallel SRE `evidence` / `fra` / `mcrl` modules.
- Cutover of `G:\fae` as read-only mirror (still a separate git root).
- Green FAE package self-test suite (`packages/fae/tests`, `packages/fae/mcr/tests`).

## Import rule

Prefer `from sre.substrate import …` for constitutional symbols when writing SRE domain code. Prefer `sre.evidence.registry.EvidenceRegistry` for linguistic wire APIs. Do not import `fae.EvidenceRegistry` under the bare name `EvidenceRegistry` in domain modules — the APIs are incompatible.
