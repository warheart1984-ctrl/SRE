# Changelog

All notable changes to the Sovereign Reconstruction Engine are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] - 2026-07-21

### Added

- Vendored **Factual Alignment Engine (FAE)** under `packages/fae` with `sre.substrate` import boundary.
- **FRA/MCRL composition**: `FRAComposedReconstruction`, `ComposedRosettaEngine`, governed FRA cycle wiring (`SREGovernedFRACycle`).
- SRE→FAE nine-stage mapping with incremental `ChronologicalReconstruction` stage methods.
- FAC-E1-compliant domain evidence anchoring (`fac_evidence.py`) for build/reason/update stages.
- Integration tests for composition path including FAC-V2–V4 validation (`tests/test_fra_mcrl_composition.py`).
- HTTP API entry point: `sre-api` / `python -m sre.api`.
- Constitutional docs bundle, OpenAPI spec, JSON schemas, and CIH conformance profile.

### Fixed

- Vendored FAE drift detection and Rosetta root validation bugs blocking composition.
- Frozen `CycleContext` updates via `dataclasses.replace`.
- Measurement evidence shape for FAC-V3 calibration in composed cycles.

### Documentation

- `docs/architecture/FAESubstrate.md` — evidence-bound substrate integration status.
- Drive-G documentation evidence law referenced in governance docs.

## [0.1.0] - 2026 (pre-release)

- Initial constitutional framework: evidence registry, FRA pipeline stubs, Mythar + IE mini-corpora.
- Dantomax attestation hooks, CIH governance service, promotion gate test suite.

[1.0.0]: https://github.com/warheart1984-ctrl/mythar-sre/releases/tag/v1.0.0
[0.1.0]: https://github.com/warheart1984-ctrl/mythar-sre/releases/tag/v0.1.0
