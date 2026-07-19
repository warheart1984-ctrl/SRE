# Promotion Plan v0.1

Substrate → Substration → Promotion for SRE constitutional maturity.

## Substrate (Week 1–3: Foundational, non-promoted)

Code artifacts + **FAC-E1–E4 rejection paths** on EvidenceRegistry:

- EvidenceRegistry with SHA256 hashing and FAC-E authenticity / integrity / provenance / fit checks
- ChronologicalReconstruction skeleton + FRA stage scaffolding
- HLRMAIAgent skeleton
- CIH service skeleton
- JSON Schemas (certificate, governance trace)
- FRA corpus v0.1 (Phase I–IV)
- Constitutional promotion gate suite (`docs/specs/ConstitutionalPromotionGates.md`, `tests/test_constitutional.py`)

**Goal:** compile, test, and lint cleanly. FAC-E gates must pass. FAC-V / FRA / AI / CIH gates may remain `expectedFailure`.

**Hard rule:** SRE v0.1 **cannot be promoted** until all `ConstitutionalPromotionTests` pass (see Constitutional Promotion Gates).

## Substration (Week 4–8: Experimental, governed by local contracts)

**Vertical slice (done):**

- FRA engine runs full 9-stage cycle on Mythar (`fra_corpus_v01`) and IE (`ie_cognate_mini_v01`)
- HLRMAIAgent: evidence-anchored lexical / phonological / cognate analysis
- EvidenceRegistry: FAC-V1–V5 validation
- CIH: project registration, evidence baseline, architecture review, Sovereign Certificate, governance traces
- Demo: `python scripts/run_local.py --corpus ie --with-cih`

**Still pending for Promotion:**

- Larger published comparative datasets / stronger probabilistic phonological models
- Remote Dantomax / KMS-backed signing (local HMAC ledger is live)
- Ledger anchoring of certificates and traces in CIEMS registry

**Goal:** all constitutional promotion tests pass (no `expectedFailure`).

**Done in this slice:** local Dantomax attestations; expanded IE corpus (numbers, body, verbs); pairwise sound-change induction.

## Promotion (Week 9–14: Constitutional, CIEMS-aligned)

### Criteria

- EvidenceRegistry passes FAC-E1–E4 on real workloads
- FRA engine produces stable, repeatable reconstructions with bounded drift
- AI agent never emits unconstrained outputs (all linked to evidence IDs)
- CIH issues Sovereign Certificates with full governance trace
- Traces validate against schema and are ledger-anchored

### Actions

- Tag SRE v0.1 as Promoted Constitutional Execution Environment
- Register certificate + governance trace schemas in CIEMS registry
- Enable CI/CD gates: no merge without constitutional tests; no deploy without certificate issuance path

### Outcome

SRE v0.1 becomes a constitutional substrate for future versions. Subsequent changes must preserve:

> No constitutional decision without constitutional evidence

Chain: Evidence → FRA → AI → CIH → Certificate → Ledger → Trace.
