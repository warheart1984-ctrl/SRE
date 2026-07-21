"""Ingest external datasets into EvidenceRegistry (beyond static JSON fixtures)."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from ..evidence.models import LinguisticEvidence
from ..evidence.registry import EvidenceRegistry
from .loader import corpus_item_to_evidence_data


def _normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    if "evidence_id" not in record:
        raise ValueError("each record requires evidence_id")
    if "content" in record and isinstance(record["content"], dict):
        return dict(record)
    language_code = str(record.get("language_code") or record.get("language") or "und")
    language_name = str(record.get("language_name") or language_code)
    period = str(record.get("period") or record.get("time_period") or "unknown")
    item = {
        "evidence_id": record["evidence_id"],
        "type": record.get("evidence_type") or record.get("type") or "corpus_sample",
        "text": record.get("text"),
        "gloss": record.get("gloss"),
        "form": record.get("form"),
        "meaning": record.get("meaning"),
        "metadata": dict(record.get("metadata") or {}),
        "provenance_chain": list(record.get("provenance_chain") or []),
        "constitutional_tags": list(record.get("constitutional_tags") or ["FAC-E", "ingested"]),
    }
    if record.get("source_reference"):
        item["metadata"]["source"] = record["source_reference"]
    payload = corpus_item_to_evidence_data(
        item,
        language_code=language_code,
        language_name=language_name,
        period=period,
        submitted_by=str(record.get("submitted_by") or "corpus_ingest"),
    )
    if record.get("source_reference"):
        payload["source_reference"] = str(record["source_reference"])
    return payload


def ingest_records(
    registry: EvidenceRegistry,
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Ingest inline evidence submissions; returns summary counts."""
    accepted = 0
    rejected = 0
    ids: list[str] = []
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("records must be objects")
        payload = _normalize_record(record)
        evidence = registry.add_evidence(payload)
        ids.append(evidence.evidence_id)
        status = registry.get_status(evidence.evidence_id)
        if status and status.value == "accepted":
            accepted += 1
        else:
            rejected += 1
    return {
        "ingested": len(ids),
        "accepted": accepted,
        "rejected": rejected,
        "evidence_ids": ids,
    }


def ingest_jsonl(
    registry: EvidenceRegistry,
    path: Path | str,
) -> list[LinguisticEvidence]:
    """Load one JSON object per line as evidence submissions."""
    records: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        records.append(json.loads(line))
    summary = ingest_records(registry, records)
    out: list[LinguisticEvidence] = []
    for eid in summary["evidence_ids"]:
        ev = registry.get_evidence(eid)
        if ev is not None:
            out.append(ev)
    return out


def ingest_csv(
    registry: EvidenceRegistry,
    path: Path | str,
    *,
    column_map: dict[str, str] | None = None,
    language_code: str = "und",
    language_name: str = "Unknown",
    period: str = "corpus",
) -> list[LinguisticEvidence]:
    """
    Ingest CSV rows as lexical/corpus evidence.

    Default columns: evidence_id, form, gloss, source_reference, evidence_type.
    """
    mapping = {
        "evidence_id": "evidence_id",
        "form": "form",
        "gloss": "gloss",
        "source_reference": "source_reference",
        "evidence_type": "evidence_type",
    }
    if column_map:
        mapping.update(column_map)
    records: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            record: dict[str, Any] = {
                "language_code": language_code,
                "language_name": language_name,
                "period": period,
            }
            for target, source_col in mapping.items():
                if source_col in row and row[source_col]:
                    record[target] = row[source_col]
            if not record.get("evidence_id"):
                continue
            records.append(record)
    summary = ingest_records(registry, records)
    out: list[LinguisticEvidence] = []
    for eid in summary["evidence_ids"]:
        ev = registry.get_evidence(eid)
        if ev is not None:
            out.append(ev)
    return out


def ingest_file(
    registry: EvidenceRegistry,
    path: Path | str,
    *,
    format: str | None = None,
) -> dict[str, Any]:
    """Auto-detect JSONL vs CSV vs SRE corpus JSON and ingest."""
    p = Path(path)
    fmt = (format or p.suffix.lstrip(".")).lower()
    if fmt in {"jsonl", "ndjson"}:
        rows = ingest_jsonl(registry, p)
        return {"format": fmt, "ingested": len(rows), "evidence_ids": [r.evidence_id for r in rows]}
    if fmt == "csv":
        rows = ingest_csv(registry, p)
        return {"format": fmt, "ingested": len(rows), "evidence_ids": [r.evidence_id for r in rows]}
    if fmt == "json":
        data = json.loads(p.read_text(encoding="utf-8"))
        if "languages" in data:
            from .loader import seed_registry_from_corpus

            seeded = seed_registry_from_corpus(registry, path=p, search_catalog=False)
            return {
                "format": "corpus_json",
                "ingested": len(seeded),
                "evidence_ids": [e.evidence_id for e in seeded],
            }
        if isinstance(data, list):
            return ingest_records(registry, data)
        raise ValueError("unsupported JSON shape for ingest")
    raise ValueError(f"unsupported ingest format: {fmt}")
