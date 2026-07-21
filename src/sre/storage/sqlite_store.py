"""SQLite persistence for evidence and reconstructions."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
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


class SqliteStore:
    """SQLite-backed durable store (stdlib only)."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS evidence (
                evidence_id TEXT PRIMARY KEY,
                evidence_type TEXT NOT NULL,
                source_reference TEXT NOT NULL,
                content_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                submitted_by TEXT NOT NULL,
                sha256_hash TEXT NOT NULL,
                provenance_chain_json TEXT NOT NULL,
                constitutional_tags_json TEXT NOT NULL,
                status TEXT NOT NULL,
                validation_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS reconstruction_meta (
                reconstruction_id TEXT PRIMARY KEY,
                data_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS reconstruction_results (
                reconstruction_id TEXT PRIMARY KEY,
                result_json TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

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
        self._conn.execute(
            """
            INSERT INTO evidence (
                evidence_id, evidence_type, source_reference, content_json,
                created_at, submitted_by, sha256_hash, provenance_chain_json,
                constitutional_tags_json, status, validation_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(evidence_id) DO UPDATE SET
                evidence_type=excluded.evidence_type,
                source_reference=excluded.source_reference,
                content_json=excluded.content_json,
                created_at=excluded.created_at,
                submitted_by=excluded.submitted_by,
                sha256_hash=excluded.sha256_hash,
                provenance_chain_json=excluded.provenance_chain_json,
                constitutional_tags_json=excluded.constitutional_tags_json,
                status=excluded.status,
                validation_json=excluded.validation_json
            """,
            (
                evidence.evidence_id,
                evidence.evidence_type.value,
                evidence.source_reference,
                json.dumps(evidence.content, sort_keys=True),
                _dt_to_iso(evidence.created_at),
                evidence.submitted_by,
                evidence.sha256_hash,
                json.dumps(evidence.provenance_chain),
                json.dumps(evidence.constitutional_tags),
                status.value,
                json.dumps(validation_payload, sort_keys=True),
            ),
        )
        self._conn.commit()

    def load_evidence(
        self,
    ) -> list[tuple[LinguisticEvidence, ConstitutionalStatus, ConstitutionalValidationResult]]:
        rows = self._conn.execute("SELECT * FROM evidence").fetchall()
        out: list[
            tuple[LinguisticEvidence, ConstitutionalStatus, ConstitutionalValidationResult]
        ] = []
        for row in rows:
            validation_payload = json.loads(row["validation_json"])
            evidence = LinguisticEvidence(
                evidence_id=row["evidence_id"],
                evidence_type=EvidenceType(row["evidence_type"]),
                source_reference=row["source_reference"],
                content=json.loads(row["content_json"]),
                created_at=_dt_from_iso(row["created_at"]),
                submitted_by=row["submitted_by"],
                sha256_hash=row["sha256_hash"],
                provenance_chain=json.loads(row["provenance_chain_json"]),
                constitutional_tags=json.loads(row["constitutional_tags_json"]),
            )
            validation = ConstitutionalValidationResult(
                evidence_id=validation_payload["evidence_id"],
                is_valid=bool(validation_payload["is_valid"]),
                failed_checks=list(validation_payload.get("failed_checks") or []),
                report=dict(validation_payload.get("report") or {}),
                validated_at=_dt_from_iso(validation_payload["validated_at"]),
            )
            out.append((evidence, ConstitutionalStatus(row["status"]), validation))
        return out

    def save_reconstruction_meta(self, reconstruction_id: str, data: dict[str, Any]) -> None:
        self._conn.execute(
            """
            INSERT INTO reconstruction_meta (reconstruction_id, data_json)
            VALUES (?, ?)
            ON CONFLICT(reconstruction_id) DO UPDATE SET data_json=excluded.data_json
            """,
            (reconstruction_id, json.dumps(data, sort_keys=True)),
        )
        self._conn.commit()

    def load_reconstruction_meta(self, reconstruction_id: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT data_json FROM reconstruction_meta WHERE reconstruction_id = ?",
            (reconstruction_id,),
        ).fetchone()
        if row is None:
            return None
        return json.loads(row["data_json"])

    def load_all_reconstruction_meta(self) -> dict[str, dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT reconstruction_id, data_json FROM reconstruction_meta"
        ).fetchall()
        return {row["reconstruction_id"]: json.loads(row["data_json"]) for row in rows}

    def save_reconstruction_result(self, reconstruction_id: str, result: dict[str, Any]) -> None:
        self._conn.execute(
            """
            INSERT INTO reconstruction_results (reconstruction_id, result_json)
            VALUES (?, ?)
            ON CONFLICT(reconstruction_id) DO UPDATE SET result_json=excluded.result_json
            """,
            (reconstruction_id, json.dumps(result, sort_keys=True, default=str)),
        )
        self._conn.commit()

    def load_reconstruction_result(self, reconstruction_id: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT result_json FROM reconstruction_results WHERE reconstruction_id = ?",
            (reconstruction_id,),
        ).fetchone()
        if row is None:
            return None
        return json.loads(row["result_json"])

    def load_all_reconstruction_results(self) -> dict[str, dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT reconstruction_id, result_json FROM reconstruction_results"
        ).fetchall()
        return {row["reconstruction_id"]: json.loads(row["result_json"]) for row in rows}

    def close(self) -> None:
        self._conn.close()
