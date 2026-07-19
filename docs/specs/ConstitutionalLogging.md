# Constitutional Logging Specification

## Log streams

| Stream | Source |
|--------|--------|
| `evidence.log` | EvidenceRegistry operations |
| `fra.log` | FRA stage transitions |
| `ai.log` | HLRMAIAgent operations |
| `cih.log` | CIH governance events |

## Log record shape (common envelope)

```json
{
  "timestamp": "2026-07-19T16:00:00",
  "service": "FRA_ENGINE",
  "actor": "system",
  "principal": "architect_001",
  "correlation_id": "corr_abc123",
  "event_type": "FRA_STAGE_COMPLETED",
  "severity": "INFO",
  "payload": {},
  "evidence_links": ["evid_001", "evid_002"],
  "constitutional_context": {
    "fac_e_status": "PASSED",
    "fac_v_status": "PENDING"
  }
}
```

## Invariants

1. Every reconstruction event must be logged.
2. Every governance decision must be logged.
3. Every log record must be linkable to evidence and/or certificate.
4. Logs must be immutable and exportable into governance traces.

## Related schemas

- `schemas/governance_trace.schema.json` — append-only per-run trace
- Governance Consensus Map — Trace Engine → Ledger
