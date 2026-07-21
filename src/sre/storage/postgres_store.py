"""Postgres persistence (optional psycopg dependency)."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from ..evidence.models import (
    ConstitutionalStatus,
    ConstitutionalValidationResult,
    EvidenceType,
    LinguisticEvidence,
)


def _dt_to_iso(value: datetime) -> str:
    return value.isoformat()


def _dt_from_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


class PostgresStore:
    """Postgres-backed store; requires ``psycopg[binary]`` (``sre[postgres]`` extra)."""

    def __init__(self, dsn: str) -> None:
        import importlib.util

        if importlib.util.find_spec("psycopg") is None:  # pragma: no cover
            raise RuntimeError(
                "Postgres store requires psycopg. Install with: pip install 'sovereign-reconstruction-engine[postgres]'"
            )
        self._dsn = dsn
        self._init_schema()

    def _connect(self):
        import psycopg

        return psycopg.connect(self._dsn)

    def _init_schema(self) -> None:
        ddl = """
        CREATE TABLE IF NOT EXISTS evidence (
            evidence_id TEXT PRIMARY KEY,
            evidence_type TEXT NOT NULL,
            source_reference TEXT NOT NULL,
            content_json JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL,
            submitted_by TEXT NOT NULL,
            sha256_hash TEXT NOT NULL,
            provenance_chain_json JSONB NOT NULL,
            constitutional_tags_json JSONB NOT NULL,
            status TEXT NOT NULL,
            validation_json JSONB NOT NULL
        );
        CREATE TABLE IF NOT EXISTS reconstruction_meta (
            reconstruction_id TEXT PRIMARY KEY,
            data_json JSONB NOT NULL
        );
        CREATE TABLE IF NOT EXISTS reconstruction_results (
            reconstruction_id TEXT PRIMARY KEY,
            result_json JSONB NOT NULL
        );
        """
        with self._connect() as conn:
            conn.execute(ddl)
            conn.commit()

    def save_evidence(
        self,
        evidence: LinguisticEvidence,
        status: ConstitutionalStatus,
        validation: ConstitutionalValidationResult,
    ) -> None:
        validation_payload = {
            "evidence_id": validation.evidence_id,
            "is_valid": validation.is_valid,
            "failed_checks": list(validation.failed_checks),
            "report": validation.report,
            "validated_at": _dt_to_iso(validation.validated_at),
        }
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO evidence (
                    evidence_id, evidence_type, source_reference, content_json,
                    created_at, submitted_by, sha256_hash, provenance_chain_json,
                    constitutional_tags_json, status, validation_json
                ) VALUES (%s, %s, %s, %s::jsonb, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s::jsonb)
                ON CONFLICT (evidence_id) DO UPDATE SET
                    evidence_type = EXCLUDED.evidence_type,
                    source_reference = EXCLUDED.source_reference,
                    content_json = EXCLUDED.content_json,
                    created_at = EXCLUDED.created_at,
                    submitted_by = EXCLUDED.submitted_by,
                    sha256_hash = EXCLUDED.sha256_hash,
                    provenance_chain_json = EXCLUDED.provenance_chain_json,
                    constitutional_tags_json = EXCLUDED.constitutional_tags_json,
                    status = EXCLUDED.status,
                    validation_json = EXCLUDED.validation_json
                """,
                (
                    evidence.evidence_id,
                    evidence.evidence_type.value,
                    evidence.source_reference,
                    json.dumps(evidence.content, sort_keys=True),
                    evidence.created_at,
                    evidence.submitted_by,
                    evidence.sha256_hash,
                    json.dumps(evidence.provenance_chain),
                    json.dumps(evidence.constitutional_tags),
                    status.value,
                    json.dumps(validation_payload, sort_keys=True),
                ),
            )
            conn.commit()

    def load_evidence(
        self,
    ) -> list[tuple[LinguisticEvidence, ConstitutionalStatus, ConstitutionalValidationResult]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM evidence").fetchall()
        out: list[
            tuple[LinguisticEvidence, ConstitutionalStatus, ConstitutionalValidationResult]
        ] = []
        for row in rows:
            (
                evidence_id,
                evidence_type,
                source_reference,
                content_json,
                created_at,
                submitted_by,
                sha256_hash,
                provenance_chain_json,
                constitutional_tags_json,
                status,
                validation_json,
            ) = row
            content = content_json if isinstance(content_json, dict) else json.loads(content_json)
            provenance_chain = (
                provenance_chain_json
                if isinstance(provenance_chain_json, list)
                else json.loads(provenance_chain_json)
            )
            constitutional_tags = (
                constitutional_tags_json
                if isinstance(constitutional_tags_json, list)
                else json.loads(constitutional_tags_json)
            )
            validation_payload = (
                validation_json
                if isinstance(validation_json, dict)
                else json.loads(validation_json)
            )
            evidence = LinguisticEvidence(
                evidence_id=evidence_id,
                evidence_type=EvidenceType(evidence_type),
                source_reference=source_reference,
                content=content,
                created_at=created_at
                if isinstance(created_at, datetime)
                else _dt_from_iso(str(created_at)),
                submitted_by=submitted_by,
                sha256_hash=sha256_hash,
                provenance_chain=provenance_chain,
                constitutional_tags=constitutional_tags,
            )
            validation = ConstitutionalValidationResult(
                evidence_id=validation_payload["evidence_id"],
                is_valid=bool(validation_payload["is_valid"]),
                failed_checks=list(validation_payload.get("failed_checks") or []),
                report=dict(validation_payload.get("report") or {}),
                validated_at=_dt_from_iso(validation_payload["validated_at"]),
            )
            out.append((evidence, ConstitutionalStatus(status), validation))
        return out

    def save_reconstruction_meta(self, reconstruction_id: str, data: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO reconstruction_meta (reconstruction_id, data_json)
                VALUES (%s, %s::jsonb)
                ON CONFLICT (reconstruction_id) DO UPDATE SET data_json = EXCLUDED.data_json
                """,
                (reconstruction_id, json.dumps(data, sort_keys=True)),
            )
            conn.commit()

    def load_reconstruction_meta(self, reconstruction_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT data_json FROM reconstruction_meta WHERE reconstruction_id = %s",
                (reconstruction_id,),
            ).fetchone()
        if row is None:
            return None
        payload = row[0]
        return payload if isinstance(payload, dict) else json.loads(payload)

    def load_all_reconstruction_meta(self) -> dict[str, dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT reconstruction_id, data_json FROM reconstruction_meta"
            ).fetchall()
        out: dict[str, dict[str, Any]] = {}
        for recon_id, payload in rows:
            out[recon_id] = payload if isinstance(payload, dict) else json.loads(payload)
        return out

    def save_reconstruction_result(self, reconstruction_id: str, result: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO reconstruction_results (reconstruction_id, result_json)
                VALUES (%s, %s::jsonb)
                ON CONFLICT (reconstruction_id) DO UPDATE SET result_json = EXCLUDED.result_json
                """,
                (reconstruction_id, json.dumps(result, sort_keys=True, default=str)),
            )
            conn.commit()

    def load_reconstruction_result(self, reconstruction_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT result_json FROM reconstruction_results WHERE reconstruction_id = %s",
                (reconstruction_id,),
            ).fetchone()
        if row is None:
            return None
        payload = row[0]
        return payload if isinstance(payload, dict) else json.loads(payload)

    def load_all_reconstruction_results(self) -> dict[str, dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT reconstruction_id, result_json FROM reconstruction_results"
            ).fetchall()
        out: dict[str, dict[str, Any]] = {}
        for recon_id, payload in rows:
            out[recon_id] = payload if isinstance(payload, dict) else json.loads(payload)
        return out
