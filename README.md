# Sovereign Reconstruction Engine (SRE) — v0.1

A Constitutional Computing System for Evidence-Constrained Linguistic Reconstruction

The Sovereign Reconstruction Engine (SRE) is a constitutional, evidence-governed system implementing the CIEMS Sovereignty Stack for historical, linguistic, and proto-form reconstruction. Every component operates under constitutional constraints, evidence validation, and governance oversight.

## Constitutional substrate (FAE)

SRE vendors the **Factual Alignment Engine (FAE)** under `packages/fae` and exposes it as the `fae` package plus `sre.substrate`.

| Layer | Package | Role (evidenced) |
|-------|---------|------------------|
| Substrate | `fae` / `sre.substrate` | Generic FAC evidence registry, FRA cycle, drift, validation, CSR, MCRL Rosetta — **importable** after `pip install -e .` |
| Domain | `sre.evidence`, `sre.fra`, … | Linguistic EvidenceRegistry, ChronologicalReconstruction, CEL/Dantomax, Mythar + IE corpora |

**Wired today:** when `EvidenceRegistry` is constructed with a FAE registry (API `AppState` does this), ACCEPTED linguistic evidence is mirrored into the FAE substrate (`validation.report["fae_substrate"]`). Linguistic wire APIs are unchanged.

**Not claimed:** replacing SRE FRA/MCRL domain engines with FAE `FRACycle` / FAE Rosetta end-to-end (parallel stacks remain; composition is prepared via `sre.substrate`).

Standalone FAE tree at `G:\fae` remains an upstream mirror until cutover is declared.

See [`docs/architecture/FAESubstrate.md`](docs/architecture/FAESubstrate.md).

## Constitutional Foundations

SRE adheres to the CIEMS constitutional invariants:

1. No constitutional decision without constitutional evidence.
2. All evidence must pass FAC-E1 → FAC-E4 validation.
3. All reconstructions must pass FAC-V1 → FAC-V5 validation.
4. All AI outputs must be evidence-constrained and governance-traceable.
5. All services must operate under Sovereign Certificate authority.

## Promotion status

**Constitutional promotion gates:** FAC-E, FAC-V, FRA, AI, and CIH are live. Remaining work is real-world scale (larger corpora, stronger algorithms, ledger anchoring).

| Gate family | Status |
|-------------|--------|
| FAC-E1–E4 | Live |
| FAC-V1–V5 | Live |
| FRA-01–04 | Live (Mythar + IE mini-corpus) |
| AI-01–04 | Live (rule-based, evidence-anchored) |
| CIH-01–05 | Live (approval, certificate, governance trace) |

See [`docs/governance/PromotionPlan_v01.md`](docs/governance/PromotionPlan_v01.md).

## Corpora

| ID | File | Notes |
|----|------|--------|
| `mythar` | `data/fra_corpus_v01.json` | Synthetic FRA fixture |
| `mythar-lex` | `data/mythar_lexicon_v01.json` | Living lexicon clusters **12–48** + atomic roots ([MytharGapFill](docs/architecture/MytharGapFill.md)) |
| `ie` | `data/ie_cognate_mini_v01.json` | Latin / Spanish / French / Sanskrit — kin, numbers 1–5, body parts, verbs (Fortson / Beekes) |

## Quick demo

```powershell
pip install -e ".[dev]"
python scripts/generate_mythar_lexicon.py
python scripts/run_local.py --corpus mythar
python scripts/run_local.py --corpus mythar-lex
python scripts/run_local.py --corpus ie --dantomax --with-cih
pytest -q
```

Dantomax (`--dantomax`) attaches a local HMAC-signed, hash-chained attestation ledger to every ACCEPTED evidence record.

## Core Components

- **FAE Substrate** — `packages/fae`, `sre.substrate` (mirror path for ACCEPTED evidence)
- **Evidence Layer** — EvidenceRegistry, SHA256 integrity, Dantomax hooks, FAC-E1–E4
- **FRA Layer** — ChronologicalReconstruction, nine-stage methodology
- **AI Layer** — HLRMAIAgent pattern / proto-form / refine stubs
- **Governance Layer** — FAECLanguageReconstructionService (CIH), Sovereign Certificate
- **Enterprise Layer** — config / deployment / monitoring stubs
- **Temporal Layer** — MCRLRosettaEngine, TemporalMapping

## Development Status

SRE v0.1 implements:

- Full constitutional documentation and OpenAPI contracts
- FAC-E Substrate behavior on EvidenceRegistry
- FAE package vendored and importable; evidence mirror into FAE registry (tested)
- Typed stubs for FRA / AI / CIH / MCRL
- Constitutional promotion gate suite

## Running tests

```bash
pip install -e ".[dev]"
pytest -q
```

On Windows (PowerShell):

```powershell
pip install -e ".[dev]"
pytest -q
```

## License

Constitutional Computing License v1.0 (placeholder)
