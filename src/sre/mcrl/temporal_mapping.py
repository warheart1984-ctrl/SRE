"""Temporal mapping record."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TemporalMapping:
    """Cross-period alignment between Mythar and related branches."""

    source_period: str = ""
    target_period: str = ""
    alignments: list[dict[str, Any]] = field(default_factory=list)

    def validate(self) -> bool:
        """True when mapping is well-formed (empty alignments allowed for single-period)."""
        if self.alignments is None:
            return False
        for item in self.alignments:
            if not isinstance(item, dict):
                return False
        return True
