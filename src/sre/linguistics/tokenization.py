"""Phoneme-aware tokenization of orthographic forms."""

from __future__ import annotations

import re
from .features import Segment, segment

# Multi-character digraphs checked before single chars
_DIGRAPHS = ("kw", "gw", "kh", "gh", "ph", "th", "bh", "dh", "ch", "sh")


def normalize_orthography(form: str) -> str:
    f = form.lower().strip()
    f = f.replace("*", "").replace("-", "")
    replacements = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ā": "ā",
        "ē": "ē",
        "ī": "ī",
        "ō": "ō",
        "ū": "ū",
        "æ": "ai",
        "œ": "oe",
        "ø": "o",
        "ł": "l",
        "č": "ch",
        "š": "sh",
        "ž": "z",
        "ṛ": "r",
        "ḷ": "l",
        "ṃ": "m",
        "ḥ": "h",
        "ṭ": "t",
        "ḍ": "d",
        "ṇ": "n",
        "ś": "s",
        "ṣ": "s",
    }
    for src, dst in replacements.items():
        f = f.replace(src, dst)
    f = re.sub(r"[^a-zāēīōūəθðŋ]", "", f)
    return f


def tokenize(form: str) -> list[Segment]:
    """Tokenize into phonological segments (digraph-aware)."""
    f = normalize_orthography(form)
    out: list[Segment] = []
    i = 0
    while i < len(f):
        matched = False
        for dig in _DIGRAPHS:
            if f.startswith(dig, i):
                out.append(segment(dig))
                i += len(dig)
                matched = True
                break
        if matched:
            continue
        out.append(segment(f[i]))
        i += 1
    return out


def tokens_to_str(tokens: list[Segment]) -> str:
    return "".join(t.symbol for t in tokens)
