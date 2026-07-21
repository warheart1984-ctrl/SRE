"""API key authentication for SRE HTTP endpoints."""

from __future__ import annotations

import os
import secrets
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


def _parse_api_keys(raw: str) -> frozenset[str]:
    return frozenset(k.strip() for k in raw.split(",") if k.strip())


def api_keys_from_env() -> frozenset[str]:
    return _parse_api_keys(os.environ.get("SRE_API_KEYS", ""))


def api_auth_required() -> bool:
    return os.environ.get("SRE_API_AUTH_REQUIRED", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }


def extract_api_key(request: Request) -> str | None:
    header = request.headers.get("X-API-Key", "").strip()
    if header:
        return header
    auth = request.headers.get("Authorization", "").strip()
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None


def validate_api_key(provided: str | None, *, allowed: frozenset[str]) -> bool:
    if not allowed:
        return False
    if not provided:
        return False
    for key in allowed:
        if secrets.compare_digest(provided, key):
            return True
    return False


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Require API key on mutating/read routes when auth is enabled."""

    def __init__(
        self,
        app,
        *,
        allowed_keys: frozenset[str] | None = None,
        required: bool | None = None,
        exempt_paths: frozenset[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.allowed_keys = allowed_keys if allowed_keys is not None else api_keys_from_env()
        self.required = api_auth_required() if required is None else required
        self.exempt_paths = exempt_paths or frozenset(
            {"/health", "/docs", "/openapi.json", "/redoc"}
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.required:
            return await call_next(request)
        path = request.url.path.rstrip("/") or "/"
        if path in self.exempt_paths or path == "/":
            return await call_next(request)
        if not self.allowed_keys:
            return JSONResponse(
                status_code=503,
                content={
                    "detail": "api_auth_misconfigured: SRE_API_KEYS required when auth enabled"
                },
            )
        provided = extract_api_key(request)
        if not validate_api_key(provided, allowed=self.allowed_keys):
            return JSONResponse(status_code=401, content={"detail": "invalid_or_missing_api_key"})
        return await call_next(request)
