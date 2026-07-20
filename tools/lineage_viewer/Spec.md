# Mythar CEL Lineage Viewer Specification

**Version:** 1.0  
**Status:** Design specification

A tool for visualizing Mythar's constitutional evidence lineage.

Related runtime: Sovereign Ledger Explorer (`src/sre/api/static/explorer.html`)  
Read model: `src/sre/evidence/ledger_explorer.py`

---

## 1. Purpose

The CEL Lineage Viewer displays:

- Reconstruction lineage
- Evidence anchors
- Certificates
- GovernanceTrace
- FRA stage transitions
- Semantic axis evolution
- Lexicon cluster emergence

---

## 2. Features

### 2.1 Evidence timeline

- Chronological view of CEL entries
- FAC-E and FAC-V validation markers
- Certificate issuance points

### 2.2 Lexicon lineage

- Cluster evolution
- Proto-form derivation
- Sound change transitions
- Ritual variant emergence

### 2.3 GovernanceTrace

- CIH gate transitions
- Council decisions
- Certificate anchors

### 2.4 Semantic axis map

- Axis-based lexicon visualization
- Mandala overlay
- Ritual syntax mapping

---

## 3. Architecture

- **Frontend:** React + D3
- **Backend:** SRE read-model
- **Data Source:** CEL entries (`GET /api/v1/explorer/*`, `GET /api/v1/cel/*`)
- **Security:** Read-only, no mutation

---

## 4. Output formats

- Timeline view
- Mandala view
- Lexicon lineage graph
- Certificate lineage chain

---

## 5. Integration

The viewer integrates with:

- Mythar IDE
- SRE Explorer (`/`)
- CIH governance dashboard
- Academic research tools

Conformance context: `docs/conformance/SRE_ConformanceProfile_v1.md`

---

## 6. Summary

The CEL Lineage Viewer makes Mythar's reconstruction **inspectable**, **auditable**, and **constitutionally transparent**.

---

## Related

- `docs/governance/CEL_Charter_v01.md`
- `docs/architecture/FRA_Methodology.md`
- `docs/ip/README.md`
