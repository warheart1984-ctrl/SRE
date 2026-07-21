#!/usr/bin/env python3
"""Local OpenAI-compatible mock LLM for SRE analyzer demos."""

from __future__ import annotations

import os
import sys
from http.server import HTTPServer
from pathlib import Path

# Allow running without install: add src/ to path
_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from sre.ai.backends.providers.llm_mock import MockLlmHandler  # noqa: E402


def main() -> None:
    host = os.environ.get("SRE_LLM_HOST", "127.0.0.1")
    port = int(os.environ.get("SRE_LLM_PORT", "8030"))
    server = HTTPServer((host, port), MockLlmHandler)
    print(f"Mock LLM listening on http://{host}:{port}/v1/chat/completions")
    server.serve_forever()


if __name__ == "__main__":
    main()
