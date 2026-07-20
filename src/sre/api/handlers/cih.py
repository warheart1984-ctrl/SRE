"""CIH governance API handlers."""

from __future__ import annotations

from typing import Any

from ...governance.cih_service import FAECLanguageReconstructionService


def register_project(
    cih: FAECLanguageReconstructionService,
    body: dict[str, Any],
    *,
    project_registry: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Wire to POST /api/v1/cih/projects — register or early-review."""
    project_id = str(body.get("project_id") or "").strip()
    if not project_id:
        return {
            "project_id": "",
            "status": "REJECTED",
            "reason": "missing project_id",
        }
    project_registry[project_id] = dict(body)
    # Partial registration delegates to CIH (may return UNDER_REVIEW)
    return cih.approve_reconstruction_project(body)


def approve_project(
    cih: FAECLanguageReconstructionService,
    project_id: str,
    body: dict[str, Any] | None,
    *,
    project_registry: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Wire to POST /api/v1/cih/projects/{project_id}/approve."""
    stored = dict(project_registry.get(project_id) or {})
    merged = {**stored, **(body or {})}
    merged["project_id"] = project_id
    if "spec" not in merged and stored.get("spec"):
        merged["spec"] = stored["spec"]
    return cih.approve_reconstruction_project(merged)


def get_certificate(
    cih: FAECLanguageReconstructionService,
    certificate_id: str,
) -> dict[str, Any] | None:
    """Wire to GET /api/v1/certificates/{certificate_id}."""
    return cih.get_certificate(certificate_id)
