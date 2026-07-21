# SRE / Mythar — Maturity Scorecard

**Drive-G-2 scorecard**  
**Canonical standard:** [`G:\docs\governance\DriveG_MaturityDimensionsStandard.md`](../../../../docs/governance/DriveG_MaturityDimensionsStandard.md)  
**Companion:** Drive-G-1 — [`DriveG_DocumentationEvidenceLaw.md`](./DriveG_DocumentationEvidenceLaw.md)

---

## Snapshot

| Field | Value |
|-------|-------|
| Project ID | `sovereign-reconstruction-engine` / Mythar vertical |
| Repository path | `G:\sovereign-reconstruction-engine` |
| Review date | 2026-07-21 |
| Evidence anchor | v1.0.0 tag; 134 pytest pass; production-hardening pass (storage, auth, CEL bind, ingest) |

---

## Dimension ratings

| Dimension | Rating | One-line justification |
|-----------|--------|------------------------|
| Constitutional model | **High** | FAC-E/V, CEL, FRA+CIH, FAE composition, Mythar CRA governance — tested invariants |
| Governance methodology | **High** | Drive-G-1/2, promotion gates, deferred vs bound lineage, scorecard discipline |
| Reference implementation | **Moderate** | Full local vertical slice + API; not multi-tenant product |
| Platform engineering | **Early** | SQLite/Postgres opt-in, API keys, KMS contract, TLS examples — no HA/obs stack |
| Commercial operations | **Early** | PyPI-packaged v1.0.0; no signup, billing, or SLA surface |

---

## Evidence by dimension

### Constitutional model

- **Claims:** Evidence-constrained reconstruction with constitutional gates and ledger lineage.
- **Evidence:** `src/sre/evidence/`, `src/sre/governance/`, `src/sre/substrate/`, `tests/test_constitutional.py`, `tests/test_fra_mcrl_composition.py`, `tests/test_mythar_lexicon.py`.
- **Gaps:** Enterprise stubs (`NotImplementedError`); some JSON policy fields remain declarative.

### Governance methodology

- **Claims:** Documentation evidence-bound; promotion and CEL charter aligned.
- **Evidence:** `G:\DRIVE_G_LAWS.md`, `docs/governance/`, Mythar `binding_status` runtime bind in `tests/test_mythar_cel_binding.py`.
- **Gaps:** Cross-repo scorecard adoption still rolling out (Drive-G-2).

### Reference implementation

- **Claims:** Mythar lexicon seed → reconstruct → validate → CEL lineage; HTTP API v1.
- **Evidence:** `python -m pytest` (134 tests); `tests/test_api_v1.py`, `tests/test_smoke.py`.
- **Gaps:** No hosted demo environment; IE/Mythar corpora curated not open-web scale.

### Platform engineering

- **Claims:** Optional durable store, API auth, remote KMS hook, corpus ingest.
- **Evidence:** `src/sre/storage/`, `src/sre/api/auth.py`, `scripts/kms_sign_server.py`, `deploy/*.example`, `.env.example`.
- **Gaps:** Monitoring, backup runbooks, Postgres ops in production, secrets rotation automation.

### Commercial operations

- **Claims:** Open-source release artifacts exist.
- **Evidence:** `pyproject.toml` v1.0.0, GitHub release, Apache-2.0.
- **Gaps:** No commercial tier, support, or self-serve product.

---

## Audience readiness

| Audience | Assessment | Notes |
|----------|------------|-------|
| Operators (deploy & run) | **Partial** | Careful team can run API behind TLS proxy with SQLite + API keys |
| Users (signup & self-serve) | **Not ready** | Requires product/tenant layer not in repo |

---

## Overall framing

> **This project is substantiated at the constitutional layer** (model + methodology + reference loop in tests), and **early at the platform/commercial layer** (factory pieces started, not a operated product).

The engine exists. The factory around the engine is under construction.

---

## Non-claims

- Not a production SaaS or multi-tenant hosted Mythar product.
- Not full ML/statistical phonology — stdlib cognate scoring only.
- Postgres durability declared; production Postgres not continuously verified in CI.
- JSON lexicon `cel_lineage.deferred` placeholders are not runtime-bound until seed + CEL.

---

## Verification commands

```bash
cd G:\sovereign-reconstruction-engine
python -m pytest -q
python -m ruff check src packages tests
```

---

## Changelog

| Date | Change | Reviewer |
|------|--------|----------|
| 2026-07-21 | Initial Drive-G-2 scorecard | Agent review |
