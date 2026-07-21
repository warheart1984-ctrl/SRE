"""FastAPI application — SRE constitutional API v1.0."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

from ..corpus.ingest import ingest_records
from .auth import ApiKeyMiddleware
from .handlers.cel import get_cel_head, get_cel_lineage, list_cel_entries
from .handlers.cih import approve_project, get_certificate, register_project
from .handlers.evidence import (
    get_evidence_record,
    get_evidence_validation,
    submit_evidence,
)
from .handlers.explorer import (
    get_conformance_summary,
    get_explorer_entry,
    get_explorer_reconstruction,
    get_fabric_overview,
    search_explorer_entries,
)
from .handlers.reconstruction import (
    get_reconstruction,
    get_reconstruction_validation,
    start_reconstruction,
)
from .schemas import (
    CIHProjectApprove,
    CIHProjectRequest,
    CorpusIngestRequest,
    EvidenceSubmission,
    ReconstructionRequest,
)
from .state import AppState, get_app_state

API_VERSION = "1.0.0"
_STATIC = Path(__file__).parent / "static"


def create_app(state: AppState | None = None) -> FastAPI:
    """Build FastAPI app with optional injected state (testing)."""
    app = FastAPI(
        title="Sovereign Reconstruction Engine API",
        version=API_VERSION,
        description="Constitutional evidence, FRA reconstruction, CIH governance, and CEL fabric.",
    )
    app.state.sre = state or get_app_state()
    app.add_middleware(ApiKeyMiddleware)

    # --- Evidence ---
    @app.post("/api/v1/evidence", status_code=201, tags=["evidence"])
    def post_evidence(body: EvidenceSubmission) -> dict[str, Any]:
        try:
            return submit_evidence(app.state.sre.registry, body.model_dump())
        except (ValueError, KeyError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/evidence/{evidence_id}", tags=["evidence"])
    def get_evidence(evidence_id: str) -> dict[str, Any]:
        record = get_evidence_record(app.state.sre.registry, evidence_id)
        if record is None:
            raise HTTPException(status_code=404, detail="evidence_not_found")
        return record

    @app.get("/api/v1/evidence/{evidence_id}/validation", tags=["evidence"])
    def evidence_validation(evidence_id: str) -> dict[str, Any]:
        report = get_evidence_validation(app.state.sre.registry, evidence_id)
        if report is None:
            raise HTTPException(status_code=404, detail="evidence_not_found")
        return report

    @app.post("/api/v1/corpus/ingest", status_code=201, tags=["corpus"])
    def post_corpus_ingest(body: CorpusIngestRequest) -> dict[str, Any]:
        try:
            return ingest_records(app.state.sre.registry, body.records)
        except (ValueError, KeyError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    # --- FRA reconstruction ---
    @app.post("/api/v1/reconstruction", status_code=202, tags=["reconstruction"])
    def post_reconstruction(body: ReconstructionRequest) -> dict[str, Any]:
        sources = body.evidence_sources or body.evidence_ids
        if not sources:
            raise HTTPException(status_code=400, detail="evidence_sources required")
        return start_reconstruction(
            app.state.sre.registry,
            app.state.sre.agent,
            body.model_dump(),
            reconstruction_cache=app.state.sre.reconstruction_cache,
        )

    @app.get("/api/v1/reconstruction/{reconstruction_id}", tags=["reconstruction"])
    def reconstruction_detail(reconstruction_id: str) -> dict:
        detail = get_reconstruction(app.state.sre.reconstruction_cache, reconstruction_id)
        if detail is None:
            raise HTTPException(status_code=404, detail="reconstruction_not_found")
        return detail

    @app.get("/api/v1/reconstruction/{reconstruction_id}/validation", tags=["reconstruction"])
    def reconstruction_validation(reconstruction_id: str) -> dict:
        return get_reconstruction_validation(app.state.sre.registry, reconstruction_id)

    # --- CIH ---
    @app.post("/api/v1/cih/projects", status_code=201, tags=["cih"])
    def post_cih_project(body: CIHProjectRequest) -> dict[str, Any]:
        return register_project(
            app.state.sre.cih,
            body.model_dump(),
            project_registry=app.state.sre.project_registry,
        )

    @app.post("/api/v1/cih/projects/{project_id}/approve", tags=["cih"])
    def post_cih_approve(project_id: str, body: CIHProjectApprove | None = None) -> dict[str, Any]:
        return approve_project(
            app.state.sre.cih,
            project_id,
            body.model_dump() if body else None,
            project_registry=app.state.sre.project_registry,
        )

    @app.get("/api/v1/certificates/{certificate_id}", tags=["cih"])
    def certificate_detail(certificate_id: str) -> dict[str, Any]:
        cert = get_certificate(app.state.sre.cih, certificate_id)
        if cert is None:
            raise HTTPException(status_code=404, detail="certificate_not_found")
        return cert

    # --- CEL ---
    @app.get("/api/v1/cel/head", tags=["cel"])
    def cel_head() -> dict[str, Any]:
        cel = app.state.sre.require_cel()
        return get_cel_head(cel)

    @app.get("/api/v1/cel/entries", tags=["cel"])
    def cel_entries(
        entry_type: str | None = Query(default=None),
        subject_id: str | None = Query(default=None),
        limit: int = Query(default=100, ge=1, le=500),
        offset: int = Query(default=0, ge=0),
    ) -> dict[str, Any]:
        cel = app.state.sre.require_cel()
        return list_cel_entries(
            cel,
            entry_type=entry_type,
            subject_id=subject_id,
            limit=limit,
            offset=offset,
        )

    @app.get("/api/v1/cel/lineage/{reconstruction_id}", tags=["cel"])
    def cel_lineage(reconstruction_id: str) -> dict[str, Any]:
        cel = app.state.sre.require_cel()
        return get_cel_lineage(cel, reconstruction_id)

    # --- Explorer read model ---
    @app.get("/api/v1/explorer/fabric", tags=["explorer"])
    def explorer_fabric() -> dict[str, Any]:
        return get_fabric_overview(app.state.sre.explorer)

    @app.get("/api/v1/explorer/entries", tags=["explorer"])
    def explorer_entries(
        entry_type: str | None = Query(default=None),
        subject_id: str | None = Query(default=None),
        limit: int = Query(default=100, ge=1, le=500),
        offset: int = Query(default=0, ge=0),
    ) -> dict[str, Any]:
        return search_explorer_entries(
            app.state.sre.explorer,
            entry_type=entry_type,
            subject_id=subject_id,
            limit=limit,
            offset=offset,
        )

    @app.get("/api/v1/explorer/entry/{cel_entry_id}", tags=["explorer"])
    def explorer_entry(cel_entry_id: str) -> dict[str, Any]:
        detail = get_explorer_entry(app.state.sre.explorer, cel_entry_id)
        if detail is None:
            raise HTTPException(status_code=404, detail="cel_entry_not_found")
        return detail

    @app.get("/api/v1/explorer/reconstruction/{reconstruction_id}", tags=["explorer"])
    def explorer_reconstruction(reconstruction_id: str) -> dict[str, Any]:
        return get_explorer_reconstruction(app.state.sre.explorer, reconstruction_id)

    @app.get("/api/v1/explorer/conformance", tags=["explorer"])
    def explorer_conformance() -> dict[str, Any]:
        return get_conformance_summary()

    # --- UI ---
    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def explorer_ui() -> str:
        path = _STATIC / "explorer.html"
        if not path.is_file():
            return "<h1>SRE Explorer UI not found</h1>"
        return path.read_text(encoding="utf-8")

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, Any]:
        cel = app.state.sre.cel
        return {
            "status": "ok",
            "api_version": API_VERSION,
            "cel_length": cel.cel_length if cel else 0,
            "signing_mode": app.state.sre.dantomax.signing_mode,
            "persist_backend": app.state.sre.summary()["persist_backend"],
        }

    return app


app = create_app()
