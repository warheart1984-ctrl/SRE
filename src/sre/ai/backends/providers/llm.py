"""OpenAI-compatible LLM analyzer provider — FAC-E1 evidence anchoring required."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any

from sre.evidence.models import LinguisticEvidence

from ...analysis_modules import PhonologicalAnalyzer, forms_from_evidence, gloss_blob
from ..base import AnalysisBundle, enforce_evidence_anchors, evidence_id_set
from .ngram_ml import CharacterNgramMlProvider

_JSON_FENCE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    fence = _JSON_FENCE.search(text)
    if fence:
        text = fence.group(1).strip()
    # Prefer first object span
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    # Tiny local models often emit trailing commas
    text = re.sub(r",\s*([}\]])", r"\1", text)
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("LLM response JSON must be an object")
    return payload


def _evidence_cards(evidence_list: list[Any]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for evidence in evidence_list:
        if not isinstance(evidence, LinguisticEvidence):
            continue
        forms = forms_from_evidence(evidence)
        cards.append(
            {
                "evidence_id": evidence.evidence_id,
                "forms": forms,
                "gloss": gloss_blob(evidence),
                "language": evidence.content.get("language_code"),
                "period": evidence.content.get("period"),
                "type": evidence.evidence_type.value,
            }
        )
    return cards


def _system_prompt() -> str:
    return (
        "You are a historical-linguistics analysis assistant inside a constitutional "
        "reconstruction engine. You MUST only cite evidence_id values from the provided "
        "evidence list. Never invent evidence IDs, forms without IDs, or unsupported claims. "
        "Respond with a single JSON object only (no markdown commentary) using this shape:\n"
        "{\n"
        '  "lexical_clusters": [{"cluster_id": str, "root": str, "domain": str, '
        '"forms": [str], "evidence_ids": [str]}],\n'
        '  "cognate_groups": [{"group_id": str, "meanings": [str], "evidence_ids": [str], '
        '"members": [{"form": str, "evidence_id": str, "language": str|null}]}],\n'
        '  "phonological_shifts": [{"rule": str, "evidence_ids": [str], "score": number}]\n'
        "}\n"
        "Every cluster, group, and shift MUST include non-empty evidence_ids drawn only "
        "from the input. If unsure, omit the row rather than invent IDs."
    )


def _user_prompt(cards: list[dict[str, Any]]) -> str:
    return (
        "Analyze these linguistic evidence records and return JSON only.\n\n"
        f"evidence:\n{json.dumps(cards, ensure_ascii=False, indent=2)}"
    )


HttpPost = Callable[[str, dict[str, str], bytes, float], bytes]

# Free / no-paid-cloud presets. Explicit SRE_LLM_URL / MODEL / API_KEY always win.
# Drive-G-1: these are local or free-tier endpoints — not a production LLM claim.
LLM_PRESETS: dict[str, dict[str, str]] = {
    "ollama": {
        "url": "http://127.0.0.1:11434/v1/chat/completions",
        # 1B often breaks JSON; 3B is still free/local and more reliable for structured output.
        "model": "llama3.2:3b",
        "api_key": "ollama",
    },
    "openrouter-free": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "openrouter/free",
        # Key from SRE_LLM_API_KEY or OPENROUTER_API_KEY (required by OpenRouter).
    },
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "model": "llama-3.1-8b-instant",
        # Key from SRE_LLM_API_KEY or GROQ_API_KEY (free-tier signup).
    },
}


def resolve_llm_settings(
    *,
    url: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
    preset: str | None = None,
) -> tuple[str, str | None, str]:
    """
    Resolve URL / API key / model from explicit args, env, and optional preset.

    Precedence: explicit args → env overrides → preset defaults → empty.
    """
    preset_name = (preset or "").strip().lower() or os.environ.get(
        "SRE_LLM_PRESET", ""
    ).strip().lower()
    base = dict(LLM_PRESETS.get(preset_name, {})) if preset_name else {}

    resolved_url = (
        (url or "").strip() or os.environ.get("SRE_LLM_URL", "").strip() or base.get("url", "")
    )
    resolved_model = (
        (model or "").strip()
        or os.environ.get("SRE_LLM_MODEL", "").strip()
        or base.get("model", "")
        or "gpt-4o-mini"
    )

    if api_key is not None:
        resolved_key: str | None = api_key.strip() or None
    else:
        resolved_key = (
            os.environ.get("SRE_LLM_API_KEY", "").strip()
            or os.environ.get("OPENROUTER_API_KEY", "").strip()
            or os.environ.get("GROQ_API_KEY", "").strip()
            or base.get("api_key", "")
            or None
        )
        if resolved_key == "":
            resolved_key = None

    if preset_name and preset_name not in LLM_PRESETS:
        raise ValueError(
            f"unknown SRE_LLM_PRESET={preset_name!r}; expected one of {sorted(LLM_PRESETS)}"
        )
    if not resolved_url:
        raise ValueError(
            "SRE_LLM_URL is required for the llm provider, or set "
            "SRE_LLM_PRESET=ollama|openrouter-free|groq "
            "(OpenAI-compatible /v1/chat/completions endpoint)"
        )
    return resolved_url, resolved_key, resolved_model


def _default_http_post(url: str, headers: dict[str, str], body: bytes, timeout_s: float) -> bytes:
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            return resp.read()
    except urllib.error.URLError as exc:
        raise RuntimeError(f"LLM request failed: {exc}") from exc


class LlmAnalyzerProvider:
    """
    OpenAI-compatible chat-completions LLM provider.

    Environment / config:
    - ``SRE_LLM_PRESET`` — ``ollama`` (local free), ``openrouter-free``, or ``groq``
    - ``SRE_LLM_URL`` — e.g. ``https://api.openai.com/v1/chat/completions``
      or Ollama ``http://127.0.0.1:11434/v1/chat/completions``
    - ``SRE_LLM_API_KEY`` — optional Bearer token (ignored by Ollama; required by cloud)
    - ``SRE_LLM_MODEL`` — model id (Ollama default ``llama3.2:3b``)

    Drive-G-1: proposals are filtered to known evidence_ids; invented IDs are dropped.
    Free presets are local/free-tier wiring — not a claim of paid-API parity.
    """

    name = "llm"

    def __init__(
        self,
        *,
        url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        preset: str | None = None,
        timeout_s: float = 60.0,
        temperature: float = 0.0,
        json_mode: bool = True,
        http_post: HttpPost | None = None,
        fallback_phonology: bool = True,
    ) -> None:
        self.url, self.api_key, self.model = resolve_llm_settings(
            url=url,
            api_key=api_key,
            model=model,
            preset=preset,
        )
        self.timeout_s = timeout_s
        self.temperature = temperature
        self.json_mode = json_mode
        self._http_post = http_post or _default_http_post
        self._fallback_phonology = fallback_phonology

    def analyze(self, evidence_list: list[Any]) -> AnalysisBundle:
        cards = _evidence_cards(evidence_list)
        known = evidence_id_set(evidence_list)
        if not cards:
            return AnalysisBundle(
                backend="ml",
                metadata={"provider": self.name, "model": self.model, "empty_input": True},
            )

        payload: dict[str, Any] = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": [
                {"role": "system", "content": _system_prompt()},
                {"role": "user", "content": _user_prompt(cards)},
            ],
        }
        if self.json_mode:
            payload["response_format"] = {"type": "json_object"}
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        raw = self._http_post(
            self.url,
            headers,
            json.dumps(payload).encode("utf-8"),
            self.timeout_s,
        )
        try:
            envelope = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            return self._fallback_bundle(
                evidence_list, reason=f"envelope_json: {exc}"
            )

        try:
            content = self._message_content(envelope)
            parsed = _extract_json(content)
        except (json.JSONDecodeError, ValueError, RuntimeError) as exc:
            # Small free/local models often emit near-JSON; fall back to ngram (FAC-E1).
            return self._fallback_bundle(evidence_list, reason=str(exc))
        bundle = AnalysisBundle(
            lexical_clusters=list(parsed.get("lexical_clusters") or []),
            phonological_shifts=list(parsed.get("phonological_shifts") or []),
            cognate_groups=list(parsed.get("cognate_groups") or []),
            backend="ml",
            metadata={
                "provider": self.name,
                "model": self.model,
                "llm_url": self.url,
                "raw_cluster_count": len(parsed.get("lexical_clusters") or []),
            },
        )
        # Normalize member evidence_ids onto cognate groups if missing
        for group in bundle.cognate_groups:
            if not group.get("evidence_ids"):
                ids = [
                    str(m.get("evidence_id"))
                    for m in (group.get("members") or [])
                    if m.get("evidence_id")
                ]
                group["evidence_ids"] = list(dict.fromkeys(ids))

        anchored = enforce_evidence_anchors(bundle, known_evidence_ids=known)
        if not anchored.lexical_clusters and not anchored.cognate_groups:
            # Model replied but FAC-E1 stripped everything — still produce usable anchors.
            return self._fallback_bundle(
                evidence_list,
                reason="fac_e1_empty_after_filter",
            )
        if self._fallback_phonology and not anchored.phonological_shifts:
            induced = PhonologicalAnalyzer().analyze(evidence_list)
            anchored.phonological_shifts = [
                s for s in induced if (s.get("evidence_ids") or [])
            ]
            anchored.metadata["phonology_fallback"] = "induced"

        dropped = (
            len(bundle.lexical_clusters)
            + len(bundle.cognate_groups)
            + len(bundle.phonological_shifts)
        ) - (
            len(anchored.lexical_clusters)
            + len(anchored.cognate_groups)
            + len(anchored.phonological_shifts)
        )
        anchored.metadata = {
            **anchored.metadata,
            "provider": self.name,
            "model": self.model,
            "fac_e1_dropped_rows": max(0, dropped),
        }
        return anchored

    def _fallback_bundle(
        self, evidence_list: list[Any], *, reason: str
    ) -> AnalysisBundle:
        """Ngram + optional phonology when free/local LLM output is unusable."""
        ngram = CharacterNgramMlProvider().analyze(evidence_list)
        ngram.metadata = {
            **ngram.metadata,
            "provider": self.name,
            "model": self.model,
            "llm_url": self.url,
            "llm_parse_error": reason,
            "analysis_fallback": "ngram",
        }
        if self._fallback_phonology and not ngram.phonological_shifts:
            induced = PhonologicalAnalyzer().analyze(evidence_list)
            ngram.phonological_shifts = [
                s for s in induced if (s.get("evidence_ids") or [])
            ]
            ngram.metadata["phonology_fallback"] = "induced"
        return ngram

    @staticmethod
    def _message_content(envelope: dict[str, Any]) -> str:
        choices = envelope.get("choices") or []
        if not choices:
            # Allow bare analysis JSON for simple mock servers
            if any(
                k in envelope for k in ("lexical_clusters", "cognate_groups", "phonological_shifts")
            ):
                return json.dumps(envelope)
            raise RuntimeError("LLM response missing choices")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("LLM response missing message content")
        return content
