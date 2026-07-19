# Constitutional Validation Pipeline

Pipeline: **ConstitutionalEvidenceValidation** (FAC-E1 → FAC-E4)

## Stages

1. **Canonicalization** — normalize fields, remove non-essential metadata, deterministic ordering
2. **Integrity hashing (FAC-E2)** — SHA256 over canonical payload
3. **Authenticity (FAC-E1)** — source_reference + principal authorization
4. **Provenance (FAC-E3)** — provenance_chain + optional Dantomax cross-check
5. **Constitutional fit (FAC-E4)** — domain scope, ethics, governance policies; tags
6. **Aggregation & decision** — all pass → ACCEPTED; any fail → REJECTED
7. **Dantomax registration** — optional external attestation
8. **Persistence** — EvidenceRegistry store, status, validation report

## Outputs

- Evidence object (`LinguisticEvidence`)
- Validation report (`ConstitutionalValidationResult`)
- Constitutional status
- Optional Dantomax attestation

## Reconstruction validation (FAC-V1–V5)

`EvidenceRegistry.validate_reconstruction` aggregates linked evidence and evaluates coverage, consistency, drift, alignment, and governance fit.
