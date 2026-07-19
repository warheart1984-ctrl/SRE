# Dantomax Integration

External integrity oracle at the Evidence Layer boundary.

## Responsibilities

- Register evidence hashes and validation reports
- Verify integrity and cryptographic attestations
- Maintain provenance chain
- Integrate with Sovereign Ledger Explorer

## Key methods

| Method | Purpose |
|--------|---------|
| `register_evidence(evidence_id, sha256_hash, validation_report)` | Create ledger record; return id, signature, position |
| `verify_evidence(evidence_id, sha256_hash)` | Confirm existence, hash match, signature |
| `get_provenance_chain(evidence_id)` | Ordered attestation history |
| `verify_ledger_integrity()` | Walk full hash chain |
| `export_ledger()` | Dump append-only ledger |

## Implementation (Substration)

`src/sre/evidence/dantomax_client.py` provides a **local hash-chained, HMAC-signed ledger**:

- Append-only records with `prev_ledger_hash` + `ledger_hash`
- HMAC-SHA256 signatures over `(evidence_id, hash, timestamp, prev, position)`
- Default signing key: `sre-dantomax-dev-key` (override via constructor for tests / deployment)
- `EvidenceRegistry(dantomax_client=...)` attaches receipts to validation reports on ACCEPTED evidence
- `EvidenceRegistry.verify_with_dantomax(evidence_id)` re-checks attestations
- FAC-E3 can cross-check `dantomax:*` provenance entries when a client is configured

## Architectural position

- Called by `EvidenceRegistry` during `add_evidence` and provenance checks
- Higher layers (FRA, CIH) access Dantomax only via EvidenceRegistry
- Coupled to Governance Consensus Map and Sovereign Ledger Explorer
- Production swap: replace local HMAC key with KMS / remote Dantomax without changing registry call sites
