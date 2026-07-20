"""Run SRE API with uvicorn: python -m sre.api"""

from __future__ import annotations

import os


def main() -> None:
    import uvicorn

    host = os.environ.get("SRE_API_HOST", "127.0.0.1")
    port = int(os.environ.get("SRE_API_PORT", "8010"))
    uvicorn.run(
        "sre.api.app:app",
        host=host,
        port=port,
        reload=os.environ.get("SRE_API_RELOAD", "").lower() in {"1", "true", "yes"},
    )


if __name__ == "__main__":
    main()
