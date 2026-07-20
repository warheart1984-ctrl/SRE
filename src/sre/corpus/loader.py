"""Load FRA / IE corpora into EvidenceRegistry."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..evidence.models import LinguisticEvidence
from ..evidence.registry import EvidenceRegistry

_DATA = Path(__file__).resolve().parents[3] / "data"
DEFAULT_CORPUS = _DATA / "fra_corpus_v01.json"
IE_CORPUS = _DATA / "ie_cognate_mini_v01.json"
IE_EXPANDED = _DATA / "ie_cognate_expanded_v01.json"
MYTHAR_LEXICON = _DATA / "mythar_lexicon_v01.json"

CORPUS_CATALOG: dict[str, Path] = {
    "mythar": DEFAULT_CORPUS,
    "fra_test_v01": DEFAULT_CORPUS,
    "ie": IE_CORPUS,
    "ie_cognate_mini_v01": IE_CORPUS,
    "ie-expanded": IE_EXPANDED,
    "ie_expanded": IE_EXPANDED,
    "ie_cognate_expanded_v01": IE_EXPANDED,
    "mythar-lex": MYTHAR_LEXICON,
    "mythar_lexicon_v01": MYTHAR_LEXICON,
}


def resolve_corpus_path(name_or_path: Path | str | None = None) -> Path:
    if name_or_path is None:
        return DEFAULT_CORPUS
    raw = Path(name_or_path) if not isinstance(name_or_path, Path) else name_or_path
    key = str(name_or_path).lower()
    if key in CORPUS_CATALOG:
        return CORPUS_CATALOG[key]
    if raw.exists():
        return raw
    raise FileNotFoundError(f"unknown corpus: {name_or_path}")


def load_corpus(path: Path | str | None = None) -> dict[str, Any]:
    corpus_path = resolve_corpus_path(path)
    return json.loads(corpus_path.read_text(encoding="utf-8"))


def corpus_item_to_evidence_data(
    item: dict[str, Any],
    *,
    language_code: str,
    language_name: str,
    period: str,
    submitted_by: str = "corpus_loader",
) -> dict[str, Any]:
    """Normalize a corpus evidence item into EvidenceSubmission shape."""
    evidence_type = str(item.get("type") or item.get("evidence_type") or "corpus_sample")
    content: dict[str, Any] = {
        "language_code": language_code,
        "language_name": language_name,
        "period": period,
        "metadata": dict(item.get("metadata") or {}),
    }
    for key in ("text", "gloss", "form", "meaning", "rule"):
        if key in item:
            content[key] = item[key]

    meta = item.get("metadata") or {}
    source_reference = (
        meta.get("source")
        or meta.get("site")
        or f"{language_name} {period} corpus"
    )
    return {
        "evidence_id": item["evidence_id"],
        "evidence_type": evidence_type,
        "source_reference": str(source_reference),
        "content": content,
        "submitted_by": submitted_by,
        "provenance_chain": list(item.get("provenance_chain") or []),
        "constitutional_tags": list(item.get("constitutional_tags") or ["FAC-E", "FRA"]),
    }


def iter_corpus_evidence(
    corpus: dict[str, Any] | None = None,
    *,
    path: Path | str | None = None,
    period: str | None = None,
    language_code: str | None = None,
    evidence_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    data = corpus or load_corpus(path)
    wanted = set(evidence_ids) if evidence_ids else None
    out: list[dict[str, Any]] = []
    for lang in data.get("languages", []):
        code = lang.get("code", "")
        name = lang.get("name", code)
        if language_code and code != language_code:
            continue
        for per in lang.get("periods", []):
            pname = per.get("name", "")
            if period and pname != period:
                continue
            for item in per.get("evidence", []):
                eid = item["evidence_id"]
                if wanted is not None and eid not in wanted:
                    continue
                out.append(
                    corpus_item_to_evidence_data(
                        item,
                        language_code=code,
                        language_name=name,
                        period=pname,
                    )
                )
    return out


def seed_registry_from_corpus(
    registry: EvidenceRegistry,
    *,
    path: Path | str | None = None,
    period: str | None = None,
    language_code: str | None = None,
    evidence_ids: list[str] | None = None,
    search_catalog: bool = True,
) -> list[LinguisticEvidence]:
    """
    Add matching corpus items to the registry; skip IDs already present.
    If evidence_ids remain missing and search_catalog is True, try all known corpora.
    """
    paths: list[Path] = [resolve_corpus_path(path)]
    if search_catalog:
        for catalog_path in CORPUS_CATALOG.values():
            if catalog_path not in paths:
                paths.append(catalog_path)

    seeded: list[LinguisticEvidence] = []
    remaining = set(evidence_ids) if evidence_ids else None

    for corpus_path in paths:
        payloads = iter_corpus_evidence(
            path=corpus_path,
            period=period,
            language_code=language_code,
            evidence_ids=list(remaining) if remaining is not None else None,
        )
        if not payloads and remaining is None and corpus_path != paths[0]:
            continue
        for payload in payloads:
            eid = payload["evidence_id"]
            if registry.get_evidence(eid) is not None:
                existing = registry.get_evidence(eid)
                assert existing is not None
                seeded.append(existing)
            else:
                seeded.append(registry.add_evidence(payload))
            if remaining is not None:
                remaining.discard(eid)
        if remaining is not None and not remaining:
            break
        if remaining is None:
            # Full corpus seed only from first path
            break
    return seeded


def list_evidence_ids(path: Path | str | None = None) -> list[str]:
    return [p["evidence_id"] for p in iter_corpus_evidence(path=path)]
