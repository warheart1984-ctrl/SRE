"""Historical attestation records — evidence substrate for Dantomax."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class EvidenceClass(str, Enum):
    """Distinction between attestation kinds — never collapse these."""

    DIRECTLY_ATTESTED = "directly_attested"
    NORMALIZED = "normalized"
    SCHOLARLY_RECONSTRUCTION = "scholarly_reconstruction"
    SYSTEM_HYPOTHESIS = "system_hypothesis"


class AttestationStatus(str, Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"
    APPROVED = "approved"
    PENDING = "pending"


@dataclass
class HistoricalAttestation:
    """
    Production-shaped attestation of a linguistic form in a published source.
    Immutable once registered; corrections create superseding records.
    """

    attestation_id: str
    language: str
    normalized_form: str
    original_form: str
    gloss: str
    grammatical_category: str
    source_id: str
    source_title: str
    source_author: str
    publication_year: int
    page_or_entry: str = ""
    edition: str = ""
    manuscript_or_inscription: str = ""
    approximate_date: str = ""
    geographic_origin: str = ""
    confidence: float = 1.0
    evidence_class: EvidenceClass = EvidenceClass.DIRECTLY_ATTESTED
    notes: str = ""
    checksum: str = ""
    ingestion_timestamp: str = ""
    status: AttestationStatus = AttestationStatus.ACTIVE
    supersedes: str | None = None
    superseded_by: str | None = None
    flags: list[str] = field(default_factory=list)
    # disputed | analogical | borrowed | unattested | uncertain

    def __post_init__(self) -> None:
        if isinstance(self.evidence_class, str):
            self.evidence_class = EvidenceClass(self.evidence_class)
        if isinstance(self.status, str):
            self.status = AttestationStatus(self.status)
        if not self.ingestion_timestamp:
            self.ingestion_timestamp = datetime.now(timezone.utc).isoformat()
        if not self.checksum:
            self.checksum = compute_attestation_checksum(self)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["evidence_class"] = self.evidence_class.value
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HistoricalAttestation:
        payload = dict(data)
        payload.pop("checksum", None)  # recompute
        return cls(**{k: v for k, v in payload.items() if k in cls.__dataclass_fields__})


def _canonical_payload(att: HistoricalAttestation) -> dict[str, Any]:
    return {
        "attestation_id": att.attestation_id,
        "language": att.language,
        "normalized_form": att.normalized_form,
        "original_form": att.original_form,
        "gloss": att.gloss,
        "grammatical_category": att.grammatical_category,
        "source_id": att.source_id,
        "source_title": att.source_title,
        "source_author": att.source_author,
        "publication_year": att.publication_year,
        "page_or_entry": att.page_or_entry,
        "edition": att.edition,
        "manuscript_or_inscription": att.manuscript_or_inscription,
        "approximate_date": att.approximate_date,
        "geographic_origin": att.geographic_origin,
        "confidence": att.confidence,
        "evidence_class": att.evidence_class.value
        if isinstance(att.evidence_class, EvidenceClass)
        else att.evidence_class,
        "notes": att.notes,
        "flags": list(att.flags),
        "supersedes": att.supersedes,
    }


def compute_attestation_checksum(att: HistoricalAttestation) -> str:
    blob = json.dumps(_canonical_payload(att), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def validate_attestation_fields(data: dict[str, Any]) -> list[str]:
    """Return list of validation errors (empty = ok)."""
    errors: list[str] = []
    required = (
        "attestation_id",
        "language",
        "normalized_form",
        "original_form",
        "gloss",
        "grammatical_category",
        "source_id",
        "source_title",
        "source_author",
        "publication_year",
    )
    for key in required:
        val = data.get(key)
        if val is None or (isinstance(val, str) and not str(val).strip()):
            errors.append(f"missing_or_empty:{key}")
    year = data.get("publication_year")
    if year is not None:
        try:
            y = int(year)
            if y < 1500 or y > 2100:
                errors.append("malformed_citation:publication_year")
        except (TypeError, ValueError):
            errors.append("malformed_citation:publication_year")
    source_id = str(data.get("source_id") or "").strip().lower()
    if source_id in {"", "unknown", "n/a", "none", "unresolved", "tbd"}:
        errors.append("unresolved_source:source_id")
    author = str(data.get("source_author") or "").strip().lower()
    if author in {"", "unknown", "n/a", "none"}:
        errors.append("malformed_citation:source_author")
    title = str(data.get("source_title") or "").strip().lower()
    if title in {"", "unknown", "n/a", "none"}:
        errors.append("malformed_citation:source_title")
    conf = data.get("confidence", 1.0)
    try:
        if not 0.0 <= float(conf) <= 1.0:
            errors.append("invalid_confidence")
    except (TypeError, ValueError):
        errors.append("invalid_confidence")
    ec = data.get("evidence_class", EvidenceClass.DIRECTLY_ATTESTED.value)
    try:
        EvidenceClass(ec)
    except ValueError:
        errors.append("invalid_evidence_class")
    return errors
