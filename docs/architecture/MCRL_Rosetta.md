# MCRL Rosetta

Mythar Cross-Language Rosetta Layer (MCRL) — temporal mapping for FRA ALIGN.

## Responsibilities

- Cross-period reconstruction alignment
- Mythar ↔ Related Branch mapping
- Temporal store integration

## Components

| Component | Path |
|-----------|------|
| `MCRLRosettaEngine` | `src/sre/mcrl/rosetta_engine.py` |
| `TemporalMapping` | `src/sre/mcrl/temporal_mapping.py` |

## Method

`map_temporal(evidence)` → alignment record for FRA stage ALIGN.

## Corpus targets

See `data/fra_corpus_v01.json` Phase I–IV for diachronic and cross-branch alignment fixtures.
