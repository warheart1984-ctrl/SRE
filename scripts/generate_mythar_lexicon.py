#!/usr/bin/env python3
"""Regenerate data/mythar_lexicon_v01.json from embedded Mythar data."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sre.mythar import write_lexicon_json


def main() -> int:
    path = write_lexicon_json()
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
