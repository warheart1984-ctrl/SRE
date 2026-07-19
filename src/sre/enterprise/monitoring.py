"""Monitoring system stub — OpenTelemetry / Prometheus hooks."""

from __future__ import annotations

from typing import Any


class MonitoringSystem:
    """Platform observability stub for SRE services."""

    def emit(self, event: dict[str, Any]) -> None:
        raise NotImplementedError

    def health(self) -> dict[str, Any]:
        raise NotImplementedError
