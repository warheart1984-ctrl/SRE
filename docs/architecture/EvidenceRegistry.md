# EvidenceRegistry

Constitutional Evidence Engine (CEE) for SRE v0.1.

## Responsibilities

- FAC-E1 Authenticity
- FAC-E2 Integrity (SHA256)
- FAC-E3 Provenance
- FAC-E4 Constitutional Fit
- Optional Dantomax registration

## Models

- `EvidenceType`: inscription, lexical_item, phonological_rule, corpus_sample
- `ConstitutionalStatus`: pending, accepted, rejected, revoked
- `LinguisticEvidence`: immutable evidence record with hash + provenance
- `ConstitutionalValidationResult`: structured FAC report

## Public API

| Method | Wire target |
|--------|-------------|
| `add_evidence(evidence_data)` | `POST /api/v1/evidence` |
| `get_evidence(evidence_id)` | `GET /api/v1/evidence/{id}` |
| `get_validation_report(evidence_id)` | `GET /api/v1/evidence/{id}/validation` |
| `validate_reconstruction(reconstruction_id)` | FAC-V1–V5 for FRA / CIH |

## Pipeline (summary)

1. Canonicalize input
2. Compute SHA256
3. FAC-E1 → E4 checks
4. Persist store / status / report
5. Optional Dantomax attestation

See also: [ConstitutionalValidationPipeline.md](./ConstitutionalValidationPipeline.md), [DantomaxIntegration.md](./DantomaxIntegration.md).

## Implementation status

v0.1 ships typed stubs (`NotImplementedError`). Promotion requires full FAC enforcement on real workloads.
