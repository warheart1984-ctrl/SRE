"""Seed Dantomax attestations from corpus evidence metadata."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..evidence.dantomax_client import DantomaxClient


def extract_attestation_payloads(evidence_list: list[Any]) -> list[dict[str, Any]]:
    """Pull embedded attestation dicts from evidence content/metadata."""
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for ev in evidence_list:
        content = getattr(ev, "content", None) or {}
        meta = content.get("metadata") or {}
        payloads: list[dict[str, Any]] = []
        if isinstance(meta.get("attestation"), dict):
            payloads.append(meta["attestation"])
        for aid_payload in meta.get("attestations") or []:
            if isinstance(aid_payload, dict):
                payloads.append(aid_payload)
        for payload in payloads:
            aid = str(payload.get("attestation_id") or "")
            if not aid or aid in seen:
                continue
            seen.add(aid)
            out.append(payload)
    return out


def seed_attestations_from_evidence(
    dantomax: DantomaxClient,
    evidence_list: list[Any],
    cel: Any | None = None,
) -> dict[str, Any]:
    """
    Register all embedded attestations into the append-only ledger.
    Returns summary with registered IDs and errors (non-fatal skips for dupes).
    """
    registered: list[str] = []
    skipped: list[str] = []
    errors: list[str] = []
    for payload in extract_attestation_payloads(evidence_list):
        aid = payload.get("attestation_id", "?")
        try:
            receipt = dantomax.register_attestation(payload)
            registered.append(str(aid))
            if cel is not None:
                att = receipt.get("attestation") or payload
                cel.record_attestation(str(aid), att, dantomax_receipt=receipt)
        except ValueError as exc:
            msg = str(exc)
            if "duplicate" in msg:
                skipped.append(str(aid))
            else:
                errors.append(f"{aid}: {msg}")
    return {
        "registered": registered,
        "skipped_duplicates": skipped,
        "errors": errors,
        "attestation_root_hash": dantomax.attestation_root_hash,
        "count": len(registered),
    }


def collect_attestation_ids(evidence_list: list[Any]) -> list[str]:
    ids: list[str] = []
    for ev in evidence_list:
        content = getattr(ev, "content", None) or {}
        meta = content.get("metadata") or {}
        for aid in meta.get("attestation_ids") or []:
            ids.append(str(aid))
        att = meta.get("attestation")
        if isinstance(att, dict) and att.get("attestation_id"):
            ids.append(str(att["attestation_id"]))
        # provenance_chain may hold attestation ids
        for p in getattr(ev, "provenance_chain", None) or content.get("provenance_chain") or []:
            if str(p).startswith("att_"):
                ids.append(str(p))
    return list(dict.fromkeys(ids))


def evidence_flags_by_lang(evidence_list: list[Any]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for ev in evidence_list:
        content = getattr(ev, "content", None) or {}
        lang = str(content.get("language_code") or "?").lower()
        meta = content.get("metadata") or {}
        flags = list(meta.get("flags") or [])
        att = meta.get("attestation") or {}
        flags.extend(att.get("flags") or [])
        if flags:
            out.setdefault(lang, [])
            for f in flags:
                if f not in out[lang]:
                    out[lang].append(f)
    return out
