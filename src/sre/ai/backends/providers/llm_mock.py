"""In-process / local OpenAI-compatible mock LLM (deterministic, evidence-anchored)."""

from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler
from typing import Any


def forms_from_card(card: dict[str, Any]) -> list[str]:
    forms = list(card.get("forms") or [])
    if forms:
        return [str(f) for f in forms]
    gloss = str(card.get("gloss") or "").strip()
    return [gloss.split()[0].lower()] if gloss else []


def analyze_from_user_content(content: str) -> dict[str, Any]:
    """Parse evidence cards embedded in the user prompt and emit anchored JSON."""
    match = re.search(r"evidence:\s*(\[[\s\S]*)", content)
    if not match:
        return {
            "lexical_clusters": [],
            "cognate_groups": [],
            "phonological_shifts": [],
        }
    blob = match.group(1).strip()
    depth = 0
    end = 0
    for i, ch in enumerate(blob):
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    cards = json.loads(blob[:end] if end else blob)
    by_gloss: dict[str, list[dict[str, Any]]] = {}
    for card in cards:
        key = str(card.get("gloss") or "general").lower().strip() or "general"
        by_gloss.setdefault(key, []).append(card)

    clusters: list[dict[str, Any]] = []
    cognates: list[dict[str, Any]] = []
    for gloss, group in by_gloss.items():
        evidence_ids = [str(c["evidence_id"]) for c in group if c.get("evidence_id")]
        forms: list[str] = []
        members: list[dict[str, Any]] = []
        for card in group:
            for form in forms_from_card(card):
                forms.append(form)
                members.append(
                    {
                        "form": form,
                        "evidence_id": card.get("evidence_id"),
                        "language": card.get("language"),
                    }
                )
        root = forms[0][:4] if forms else "x"
        clusters.append(
            {
                "cluster_id": f"mock:{gloss}",
                "root": root,
                "domain": gloss.split()[0] if gloss else "general",
                "forms": list(dict.fromkeys(forms)),
                "evidence_ids": evidence_ids,
            }
        )
        cognates.append(
            {
                "group_id": f"mock_cog_{gloss.replace(' ', '_')}",
                "meanings": [gloss],
                "evidence_ids": evidence_ids,
                "members": members,
            }
        )
    return {
        "lexical_clusters": clusters,
        "cognate_groups": cognates,
        "phonological_shifts": [],
    }


class MockLlmHandler(BaseHTTPRequestHandler):
    """HTTP handler implementing POST /v1/chat/completions."""

    def do_POST(self) -> None:  # noqa: N802
        if self.path.rstrip("/") not in {
            "/v1/chat/completions",
            "/chat/completions",
        }:
            self.send_error(404, "not found")
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            req = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self.send_error(400, "invalid json")
            return
        messages = req.get("messages") or []
        user = ""
        for msg in messages:
            if msg.get("role") == "user":
                user = str(msg.get("content") or "")
        analysis = analyze_from_user_content(user)
        body = json.dumps(
            {
                "id": "chatcmpl-sre-mock",
                "object": "chat.completion",
                "model": req.get("model") or "sre-mock-llm",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": json.dumps(analysis),
                        },
                        "finish_reason": "stop",
                    }
                ],
            }
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return
