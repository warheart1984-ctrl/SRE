"""Entry point: python -m sre <command> [options]"""

from __future__ import annotations

from .cli.main import cli

if __name__ == "__main__":
    cli()
