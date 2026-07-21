"""Phoneme-aware tokenization of orthographic forms."""

from __future__ import annotations

import re

from .features import DIGRAPHS, Segment, segment

# Sort digraphs by length descending so longer matches take priority
_SORTED_DIGRAPHS = tuple(sorted(DIGRAPHS, key=len, reverse=True))

# Unicode normalization map for common linguistic diacritics and non-IPA symbols
_ORTHOGRAPHIC_NORMALIZATION: dict[str, str] = {
    # Acute/grave accents → length
    "á": "aː",
    "à": "a",
    "â": "a",
    "ä": "a",
    "é": "eː",
    "è": "e",
    "ê": "e",
    "ë": "e",
    "í": "iː",
    "ì": "i",
    "î": "i",
    "ï": "i",
    "ó": "oː",
    "ò": "o",
    "ô": "o",
    "ö": "o",
    "ú": "uː",
    "ù": "u",
    "û": "u",
    "ü": "u",
    "ý": "yː",
    "ỳ": "y",
    "ŷ": "y",
    "ÿ": "y",
    # Macron → length
    "ā": "aː",
    "ē": "eː",
    "ī": "iː",
    "ō": "oː",
    "ū": "uː",
    "ȳ": "yː",
    # Breve → short
    "ă": "a",
    "ĕ": "e",
    "ĭ": "i",
    "ŏ": "o",
    "ŭ": "u",
    # Caron / háček
    "č": "tʃ",
    "ď": "d",
    "ň": "n",
    "ř": "r",
    "š": "ʃ",
    "ť": "t",
    "ž": "ʒ",
    "ǧ": "ɡ",
    "ǩ": "k",
    # Cedilla
    "ç": "tʃ",
    "ş": "ʃ",
    # Tilde
    "ñ": "n",
    "ã": "ã",
    "ẽ": "ẽ",
    "ĩ": "ĩ",
    "õ": "õ",
    "ũ": "ũ",
    # Ring
    "ů": "u",
    # Polish ogonek
    "ą": "ɔ̃",
    "ę": "ɛ̃",
    # Misc Latin
    "æ": "æ",
    "œ": "ø",
    "ø": "ø",
    "ł": "l",
    "þ": "θ",
    "ð": "ð",
    "ƿ": "w",
    # Indic transliteration
    "ṛ": "r",
    "ṝ": "r",
    "ḷ": "l",
    "ḹ": "l",
    "ṃ": "m",
    "ḥ": "h",
    "ṭ": "t",
    "ḍ": "d",
    "ṇ": "n",
    "ṣ": "s",
    "ś": "ʃ",
    "ñ": "n",
    "ṅ": "ŋ",
    "ñ": "ɲ",
    # PIE laryngeals
    "h₁": "h",
    "h₂": "h",
    "h₃": "h",
    # Superscript w for labialization
    "ʷ": "ʷ",
    # Aspiration markers
    "ʰ": "ʰ",
    # Length markers
    "ː": "ː",
}

# Regex to strip remaining non-IPA characters
_ALLOWED_CHARS = re.compile(
    r"[^a-zāēīōūəθðŋɲʃʒʈɖɳʂʐɽɭɬɮçʝχʁħʕʔɦʋɥʎʟʙɾɴɱɢʡɓɗɠʛǀǁǃǂæœøɨʉɘɵɤɯʌɔɛɪʏʊɶpʰbʰtʰdʰcʰkʰgʰkʷgʷŋʷkʷʰgʷʰtʃdʒtɕdʑtsdzpfaːeːiːoːuːyːøːɛːɔːɤːəːɛ̃ɔ̃ãẽõũĩːʷʰ]"
)

# Tri-graphs (3+ characters) that must be tried first
_TRIGRAPHS = tuple(sorted([d for d in _SORTED_DIGRAPHS if len(d) >= 3], key=len, reverse=True))


def normalize_orthography(form: str) -> str:
    """Normalize a linguistic form to the internal IPA segment representation."""
    f = form.lower().strip()
    # Remove proto-language markers
    f = f.replace("*", "").replace("-", "")
    # Remove empty parens (for optional segments in PIE notation)
    f = re.sub(r"\(\)", "", f)
    f = re.sub(r"[0-9₁₂₃]", "", f)
    # Apply character normalization
    for src, dst in _ORTHOGRAPHIC_NORMALIZATION.items():
        f = f.replace(src, dst)
    # Remove any characters not in our segment inventory
    f = _ALLOWED_CHARS.sub("", f)
    return f


def tokenize(form: str) -> list[Segment]:
    """Tokenize a linguistic form into phonological segments (digraph-aware)."""
    f = normalize_orthography(form)
    out: list[Segment] = []
    i = 0
    while i < len(f):
        matched = False
        # Try longest matches first
        for pat in _SORTED_DIGRAPHS:
            if f.startswith(pat, i):
                out.append(segment(pat))
                i += len(pat)
                matched = True
                break
        if matched:
            continue
        out.append(segment(f[i]))
        i += 1
    return out


def tokens_to_str(tokens: list[Segment]) -> str:
    return "".join(t.symbol for t in tokens)
