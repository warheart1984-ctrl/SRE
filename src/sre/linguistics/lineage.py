"""Human-readable provenance / lineage formatting."""

from __future__ import annotations

from typing import Any


def format_human_lineage(trace: dict[str, Any] | list[dict[str, Any]]) -> str:
    """
    Render attestation → cognate → correspondence → sound shift → proto → certification.
    Accepts either a structured lineage dict or a list of step dicts.
    """
    if isinstance(trace, list):
        lines = ["Evidence lineage"]
        for i, step in enumerate(trace, 1):
            kind = step.get("stage") or step.get("kind") or step.get("event") or "step"
            detail = step.get("summary") or step.get("detail") or step.get("id") or ""
            lines.append(f"  {i}. {kind}: {detail}")
        return "\n".join(lines)

    lines = ["Evidence lineage (attestation → certification)"]
    order = [
        ("attestations", "ATTEST"),
        ("cognate_set", "CLUSTER"),
        ("correspondences", "ALIGN"),
        ("sound_shifts", "INFER"),
        ("proto_form", "PROTO"),
        ("validation", "VALIDATE"),
        ("governance", "GOVERN"),
        ("certification", "CERTIFY"),
    ]
    for key, label in order:
        val = trace.get(key)
        if val is None:
            continue
        if isinstance(val, list):
            preview = ", ".join(_brief(x) for x in val[:6])
            if len(val) > 6:
                preview += f" … (+{len(val) - 6})"
            lines.append(f"  {label}: {preview or '(none)'}")
        elif isinstance(val, dict):
            lines.append(f"  {label}: {_brief(val)}")
        else:
            lines.append(f"  {label}: {val}")
    if "path" in trace and isinstance(trace["path"], list):
        lines.append("  PATH: " + " → ".join(str(p) for p in trace["path"]))
    return "\n".join(lines)


def _brief(x: Any) -> str:
    if isinstance(x, dict):
        for k in ("attestation_id", "id", "proto_form", "pattern", "rule", "status"):
            if k in x:
                return str(x[k])
        return str({k: x[k] for k in list(x)[:3]})
    return str(x)
