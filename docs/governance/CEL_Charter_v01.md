# Constitutional Evidence Ledger (CEL) — Charter v0.1

## Preamble

The **Constitutional Evidence Ledger (CEL)** is the unified constitutional evidence fabric of the Sovereign Reconstruction Engine (SRE). It unifies **Dantomax** (integrity oracle), **FRA** (reconstruction pipeline), and **CIH** (governance) under one append-only, queryable, constitutionally-typed audit trail.

CEL does not replace Dantomax. Dantomax remains the cryptographic substrate (HMAC-signed, hash-chained integrity). CEL is the **semantic constitutional layer** that records *what happened*, *under which article*, and *how it links* to attestations, correspondences, hypotheses, validations, and certifications.

This charter ratifies CEL as a first-class constitutional subsystem for SRE v0.2 promotion.

---

## Article I — Purpose & Scope

### §1 Purpose

CEL exists to satisfy Constitutional Specification Article V §2:

> Every reconstruction run must produce a constitutional trace; every decision must be reconstructable.

CEL makes that requirement **machine-enforceable** by:

1. Recording all constitutional events in a single ledger
2. Anchoring each entry to Dantomax when cryptographic attestation applies
3. Enabling lineage queries from attestation → correspondence → hypothesis → validation → certification
4. Supplying real `ledger_entry_id` values for Sovereign Certificates (replacing placeholders)

### §2 Scope

CEL records five primary entry classes plus two supporting classes:

| Entry type | Source subsystem | Constitutional article |
|------------|------------------|----------------------|
| `evidence` | EvidenceRegistry (FAC-E) | Article II |
| `attestation` | Dantomax historical attestations | Article II §2 |
| `correspondence` | Linguistics / FRA ALIGN | Article III |
| `hypothesis` | FRA INFER / HLRMAIAgent | Article III §2 |
| `validation` | EvidenceRegistry (FAC-V) | Article III §3 |
| `governance` | CIH governance traces | Article V §2 |
| `certification` | CIH Sovereign Certificate | Article V §1 |

---

## Article II — Architectural Position

```
┌─────────────────────────────────────────────────────────────┐
│                    Constitutional Layer                      │
│  ┌─────────┐    ┌─────────┐    ┌─────────────────────────┐  │
│  │   FRA   │───▶│   CEL   │◀───│          CIH          │  │
│  │ pipeline│    │ fabric  │    │  approval + certs     │  │
│  └────┬────┘    └────┬────┘    └───────────┬───────────┘  │
│       │              │                      │              │
│  ┌────▼──────────────▼──────────────────────▼──────────┐  │
│  │              EvidenceRegistry (FAC-E / FAC-V)         │  │
│  └────────────────────────┬────────────────────────────┘  │
│                           │                                │
│  ┌────────────────────────▼────────────────────────────┐  │
│  │         Dantomax (integrity oracle / hash chain)    │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Invariants

1. **CEL is append-only.** Corrections create superseding entries; existing entries are never mutated.
2. **Dantomax anchors crypto.** When an event has a Dantomax receipt, CEL stores `dantomax_record_id` and `dantomax_ledger_hash`.
3. **Single write facade.** Production code appends to CEL via `EvidenceRegistry.cel` or `ConstitutionalEvidenceLedger` methods — not by reaching into `_dantomax` from higher layers.
4. **Certificate anchoring.** Every issued Sovereign Certificate MUST reference a real CEL entry ID in `signatures.ledger_entry_id`.
5. **No certification without lineage.** CEL lineage for a reconstruction MUST include at least one `validation` entry before a `certification` entry is appended.

---

## Article III — Entry Model

Each CEL entry contains:

| Field | Description |
|-------|-------------|
| `cel_entry_id` | Unique identifier (`cel_{type}_{subject}_{position}`) |
| `entry_type` | One of seven constitutional types |
| `subject_id` | Primary subject (evidence_id, attestation_id, recon_id, cert_id, trace_id) |
| `payload` | Typed event body (validation report, hypothesis, certificate, etc.) |
| `links` | Related IDs (evidence, attestation, reconstruction, trace) |
| `checksum` | SHA-256 of canonical payload (tamper detection) |
| `prev_cel_hash` / `cel_hash` | Hash chain within CEL |
| `dantomax_record_id` | Optional anchor to Dantomax record |
| `dantomax_ledger_hash` | Dantomax head at write time |
| `constitutional_article` | Normative article reference |

Schema: `schemas/cel_entry.schema.json`

---

## Article IV — Write Protocol

### §1 Evidence acceptance (FAC-E)

When `EvidenceRegistry.add_evidence()` accepts evidence:

```
CEL.record_evidence(evidence_id, sha256_hash, validation_report, dantomax_receipt)
```

### §2 Attestation registration (Dantomax)

When `DantomaxClient.register_attestation()` succeeds:

```
CEL.record_attestation(attestation_id, attestation_dict, dantomax_receipt)
```

### §3 Correspondence discovery (FRA ALIGN)

When correspondence engine produces ranked hypotheses per cognate set:

```
CEL.record_correspondence(cognate_set_id, {hypotheses, correspondence_sets, flags})
```

### §4 Reconstruction hypothesis (FRA INFER)

When proto-forms are ranked:

```
CEL.record_hypothesis(reconstruction_id, {proto_forms, confidence, attestation_ids})
```

### §5 Validation outcome (FAC-V)

When `EvidenceRegistry.validate_reconstruction()` completes:

```
CEL.record_validation(reconstruction_id, {is_valid, failed_checks, report})
```

### §6 Governance events (CIH)

On each CIH trace milestone (baseline, lineage verified, certificate issued):

```
CEL.record_governance(trace_id, {event_type, payload, evidence_links})
```

### §7 Certification artifact (CIH)

When `SovereignCertificate.issue()` completes:

```
CEL.record_certification(certificate_id, certificate_dict, trace_id=...)
→ certificate.signatures.ledger_entry_id = cel_entry.cel_entry_id
```

---

## Article V — Query Protocol

| Operation | Method | Returns |
|-----------|--------|---------|
| Entry lookup | `get_entry(cel_entry_id)` | Single `CELEntry` |
| Type filter | `query_by_type(CELEntryType)` | All entries of type |
| Subject filter | `query_by_subject(subject_id)` | All entries for subject |
| Reconstruction lineage | `query_lineage(reconstruction_id)` | Constitutional path |
| Fabric integrity | `verify_integrity()` | Chain + Dantomax check |
| Fabric root | `fabric_root_hash` | Merkle root over checksums |
| Export | `export_ledger()` | Full append-only dump |

---

## Article VI — Relationship to Existing Subsystems

### Dantomax

- **Role:** Cryptographic integrity oracle (HMAC, hash chain, attestation supersession)
- **CEL relationship:** CEL indexes Dantomax events with constitutional typing; stores anchor references
- **Migration:** Existing `DantomaxClient` API unchanged; CEL wraps receipts

### FRA

- **Role:** 10-stage reconstruction pipeline
- **CEL relationship:** FRA stages INGEST→ARCHIVE append typed CEL entries at ATTEST, ALIGN, INFER, VALIDATE, GOVERN, CERTIFY
- **Migration:** `ChronologicalReconstruction` uses `registry.cel` when present

### CIH

- **Role:** Project approval, Sovereign Certificate issuance, governance traces
- **CEL relationship:** CIH anchors traces and certificates to CEL; replaces in-memory-only traces as source of constitutional truth
- **Migration:** `FAECLanguageReconstructionService` records governance + certification entries

### Sovereign Certificate

- **New subject fields:** `corpus_hash`, `attestation_root_hash`, `fabric_root_hash`, `rule_set_version`, `reconstruction_ids`
- **Real ledger anchor:** `signatures.ledger_entry_id` = CEL entry ID (not placeholder)

---

## Article VII — Promotion Gates (CEL-specific)

| Gate | Requirement | Test |
|------|-------------|------|
| CEL-01 | CEL append-only; verify_integrity passes | `test_cel_integrity` |
| CEL-02 | Evidence acceptance creates CEL entry | `test_cel_evidence_record` |
| CEL-03 | Attestation registration creates CEL entry | `test_cel_attestation_record` |
| CEL-04 | FRA pipeline creates correspondence + hypothesis entries | `test_cel_fra_integration` |
| CEL-05 | FAC-V validation creates CEL entry | `test_cel_validation_record` |
| CEL-06 | CIH certificate anchored to CEL entry | `test_cel_certification_anchor` |
| CEL-07 | Lineage query returns full constitutional path | `test_cel_lineage_query` |
| CEL-08 | fabric_root_hash included in Sovereign Certificate | `test_cel_fabric_root_on_cert` |

---

## Article VIII — Future Work (v0.2 → v1.0)

1. **Persistence** — file-backed or remote CIEMS registry append log
2. **Sovereign Ledger Explorer** — read model over CEL + Dantomax export
3. **OpenAPI endpoints** — `GET /api/v1/cel/head`, `GET /api/v1/cel/entries`, `GET /api/v1/cel/lineage/{recon_id}`
4. **Constitutional logging** — wire `docs/specs/ConstitutionalLogging.md` streams to CEL
5. **Remote Dantomax / KMS** — production signing keys; CEL unchanged at API boundary
6. **Schema alignment** — extend `sovereign_certificate.schema.json` with CEL fields

---

## Ratification

CEL Charter v0.1 is ratified as the normative specification for the Constitutional Evidence Ledger subsystem. Implementation: `src/sre/evidence/cel.py`. All SRE components operating with Dantomax attached SHOULD append constitutional events to CEL.

**Effective:** SRE v0.2 promotion path  
**Supersedes:** ad-hoc in-memory governance traces as sole audit mechanism  
**Authority:** HYFAL Executive Council / CIH Governance Service
