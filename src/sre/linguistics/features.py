"""Phonological feature representations for phoneme-aware analysis.

Feature primitives used across all linguistics modules.
Segments are defined as (symbol → frozenset of features) for fast Jaccard distance.
"""

from __future__ import annotations

from dataclasses import dataclass

# Feature legend (all features are lowercase strings):
#   airstream: pulmonic, ejective, implosive, click
#   cons:      consonant
#   voc:       vowel
#   syllabic:  can be syllable nucleus
#   place:     labial, dental, alveolar, postalveolar, retroflex, palatal,
#              velar, uvular, pharyngeal, epiglottal, glottal
#   manner:    stop, affricate, fric, nasal, trill, tap, approx, lateral_approx
#   voiced:    vl (voiceless), vd (voiced)
#   aspirated: unaspirated (default), aspirated
#   spread:    spread_glottis (h), constricted_glottis (ʔ, ejectives)
#   sonority:  obstruent, sonorant
#   height:    high, mid, low (for vowels)
#   backness:  front, central, back
#   rounding:  round, unround
#   length:    long (vs default short)
#   nasalized: nasal (for vowels)
#   tense:     tense, lax
#   lateral:   lateral (for consonants)
#   rhotic:    rhotic
#   tone:      high_tone, low_tone, rising_tone, falling_tone

FEATURES: dict[str, frozenset[str]] = {
    # ── Plosives ──────────────────────────────────────────────
    "p": frozenset({"cons", "labial", "stop", "vl", "pulmonic", "obstruent"}),
    "b": frozenset({"cons", "labial", "stop", "vd", "pulmonic", "obstruent"}),
    "pʰ": frozenset({"cons", "labial", "stop", "vl", "aspirated", "pulmonic", "obstruent"}),
    "bʰ": frozenset({"cons", "labial", "stop", "vd", "aspirated", "pulmonic", "obstruent"}),
    "t": frozenset({"cons", "alveolar", "stop", "vl", "pulmonic", "obstruent"}),
    "d": frozenset({"cons", "alveolar", "stop", "vd", "pulmonic", "obstruent"}),
    "tʰ": frozenset({"cons", "alveolar", "stop", "vl", "aspirated", "pulmonic", "obstruent"}),
    "dʰ": frozenset({"cons", "alveolar", "stop", "vd", "aspirated", "pulmonic", "obstruent"}),
    "ʈ": frozenset({"cons", "retroflex", "stop", "vl", "pulmonic", "obstruent"}),
    "ɖ": frozenset({"cons", "retroflex", "stop", "vd", "pulmonic", "obstruent"}),
    "c": frozenset({"cons", "palatal", "stop", "vl", "pulmonic", "obstruent"}),
    "ɟ": frozenset({"cons", "palatal", "stop", "vd", "pulmonic", "obstruent"}),
    "cʰ": frozenset({"cons", "palatal", "stop", "vl", "aspirated", "pulmonic", "obstruent"}),
    "k": frozenset({"cons", "velar", "stop", "vl", "pulmonic", "obstruent"}),
    "g": frozenset({"cons", "velar", "stop", "vd", "pulmonic", "obstruent"}),
    "kʰ": frozenset({"cons", "velar", "stop", "vl", "aspirated", "pulmonic", "obstruent"}),
    "gʰ": frozenset({"cons", "velar", "stop", "vd", "aspirated", "pulmonic", "obstruent"}),
    "kʷ": frozenset({"cons", "labiovelar", "stop", "vl", "pulmonic", "obstruent"}),
    "gʷ": frozenset({"cons", "labiovelar", "stop", "vd", "pulmonic", "obstruent"}),
    "kʷʰ": frozenset({"cons", "labiovelar", "stop", "vl", "aspirated", "pulmonic", "obstruent"}),
    "gʷʰ": frozenset({"cons", "labiovelar", "stop", "vd", "aspirated", "pulmonic", "obstruent"}),
    "q": frozenset({"cons", "uvular", "stop", "vl", "pulmonic", "obstruent"}),
    "ɢ": frozenset({"cons", "uvular", "stop", "vd", "pulmonic", "obstruent"}),
    "ʔ": frozenset({"cons", "glottal", "stop", "vl", "pulmonic", "obstruent"}),
    # ── Affricates ────────────────────────────────────────────
    "pf": frozenset({"cons", "labial", "affricate", "vl", "pulmonic", "obstruent"}),
    "ts": frozenset({"cons", "alveolar", "affricate", "vl", "pulmonic", "obstruent"}),
    "dz": frozenset({"cons", "alveolar", "affricate", "vd", "pulmonic", "obstruent"}),
    "tʃ": frozenset({"cons", "postalveolar", "affricate", "vl", "pulmonic", "obstruent"}),
    "dʒ": frozenset({"cons", "postalveolar", "affricate", "vd", "pulmonic", "obstruent"}),
    "tɕ": frozenset({"cons", "palatal", "affricate", "vl", "pulmonic", "obstruent"}),
    "dʑ": frozenset({"cons", "palatal", "affricate", "vd", "pulmonic", "obstruent"}),
    # ── Fricatives ────────────────────────────────────────────
    "ɸ": frozenset({"cons", "labial", "fric", "vl", "pulmonic", "obstruent"}),
    "β": frozenset({"cons", "labial", "fric", "vd", "pulmonic", "obstruent"}),
    "f": frozenset({"cons", "labiodental", "fric", "vl", "pulmonic", "obstruent"}),
    "v": frozenset({"cons", "labiodental", "fric", "vd", "pulmonic", "obstruent"}),
    "θ": frozenset({"cons", "dental", "fric", "vl", "pulmonic", "obstruent"}),
    "ð": frozenset({"cons", "dental", "fric", "vd", "pulmonic", "obstruent"}),
    "s": frozenset({"cons", "alveolar", "fric", "vl", "pulmonic", "obstruent"}),
    "z": frozenset({"cons", "alveolar", "fric", "vd", "pulmonic", "obstruent"}),
    "ʃ": frozenset({"cons", "postalveolar", "fric", "vl", "pulmonic", "obstruent"}),
    "ʒ": frozenset({"cons", "postalveolar", "fric", "vd", "pulmonic", "obstruent"}),
    "ʂ": frozenset({"cons", "retroflex", "fric", "vl", "pulmonic", "obstruent"}),
    "ʐ": frozenset({"cons", "retroflex", "fric", "vd", "pulmonic", "obstruent"}),
    "ç": frozenset({"cons", "palatal", "fric", "vl", "pulmonic", "obstruent"}),
    "ʝ": frozenset({"cons", "palatal", "fric", "vd", "pulmonic", "obstruent"}),
    "x": frozenset({"cons", "velar", "fric", "vl", "pulmonic", "obstruent"}),
    "ɣ": frozenset({"cons", "velar", "fric", "vd", "pulmonic", "obstruent"}),
    "χ": frozenset({"cons", "uvular", "fric", "vl", "pulmonic", "obstruent"}),
    "ʁ": frozenset({"cons", "uvular", "fric", "vd", "pulmonic", "obstruent"}),
    "ħ": frozenset({"cons", "pharyngeal", "fric", "vl", "pulmonic", "obstruent"}),
    "ʕ": frozenset({"cons", "pharyngeal", "fric", "vd", "pulmonic", "obstruent"}),
    "h": frozenset({"cons", "glottal", "fric", "vl", "pulmonic", "obstruent"}),
    "ɦ": frozenset({"cons", "glottal", "fric", "vd", "pulmonic", "obstruent"}),
    # ── Nasals ────────────────────────────────────────────────
    "m": frozenset({"cons", "labial", "nasal", "vd", "pulmonic", "sonorant"}),
    "ɱ": frozenset({"cons", "labiodental", "nasal", "vd", "pulmonic", "sonorant"}),
    "n": frozenset({"cons", "alveolar", "nasal", "vd", "pulmonic", "sonorant"}),
    "ɳ": frozenset({"cons", "retroflex", "nasal", "vd", "pulmonic", "sonorant"}),
    "ɲ": frozenset({"cons", "palatal", "nasal", "vd", "pulmonic", "sonorant"}),
    "ŋ": frozenset({"cons", "velar", "nasal", "vd", "pulmonic", "sonorant"}),
    "ɴ": frozenset({"cons", "uvular", "nasal", "vd", "pulmonic", "sonorant"}),
    # ── Trills / Taps / Flaps ─────────────────────────────────
    "ʙ": frozenset({"cons", "labial", "trill", "vd", "pulmonic", "sonorant"}),
    "r": frozenset({"cons", "alveolar", "trill", "vd", "pulmonic", "sonorant", "rhotic"}),
    "ɾ": frozenset({"cons", "alveolar", "tap", "vd", "pulmonic", "sonorant", "rhotic"}),
    "ɽ": frozenset({"cons", "retroflex", "tap", "vd", "pulmonic", "sonorant", "rhotic"}),
    # ── Approximants ──────────────────────────────────────────
    "l": frozenset({"cons", "alveolar", "lateral_approx", "vd", "pulmonic", "sonorant", "lateral"}),
    "ɭ": frozenset(
        {"cons", "retroflex", "lateral_approx", "vd", "pulmonic", "sonorant", "lateral"}
    ),
    "ʎ": frozenset({"cons", "palatal", "lateral_approx", "vd", "pulmonic", "sonorant", "lateral"}),
    "ʟ": frozenset({"cons", "velar", "lateral_approx", "vd", "pulmonic", "sonorant", "lateral"}),
    "w": frozenset({"cons", "labial", "approx", "vd", "pulmonic", "sonorant"}),
    "ʋ": frozenset({"cons", "labiodental", "approx", "vd", "pulmonic", "sonorant"}),
    "j": frozenset({"cons", "palatal", "approx", "vd", "pulmonic", "sonorant"}),
    "ɥ": frozenset({"cons", "palatal", "approx", "vd", "pulmonic", "sonorant", "round"}),
    # ── Lateral fricatives ────────────────────────────────────
    "ɬ": frozenset({"cons", "alveolar", "fric", "vl", "pulmonic", "obstruent", "lateral"}),
    "ɮ": frozenset({"cons", "alveolar", "fric", "vd", "pulmonic", "obstruent", "lateral"}),
    # ── Short vowels ──────────────────────────────────────────
    "i": frozenset(
        {"voc", "syllabic", "high", "front", "unround", "tense", "pulmonic", "sonorant"}
    ),
    "y": frozenset({"voc", "syllabic", "high", "front", "round", "tense", "pulmonic", "sonorant"}),
    "ɪ": frozenset({"voc", "syllabic", "high", "front", "unround", "lax", "pulmonic", "sonorant"}),
    "ʏ": frozenset({"voc", "syllabic", "high", "front", "round", "lax", "pulmonic", "sonorant"}),
    "e": frozenset({"voc", "syllabic", "mid", "front", "unround", "tense", "pulmonic", "sonorant"}),
    "ø": frozenset({"voc", "syllabic", "mid", "front", "round", "tense", "pulmonic", "sonorant"}),
    "ɛ": frozenset({"voc", "syllabic", "mid", "front", "unround", "lax", "pulmonic", "sonorant"}),
    "œ": frozenset({"voc", "syllabic", "mid", "front", "round", "lax", "pulmonic", "sonorant"}),
    "æ": frozenset({"voc", "syllabic", "low", "front", "unround", "lax", "pulmonic", "sonorant"}),
    "a": frozenset({"voc", "syllabic", "low", "central", "unround", "lax", "pulmonic", "sonorant"}),
    "ɶ": frozenset({"voc", "syllabic", "low", "front", "round", "lax", "pulmonic", "sonorant"}),
    "ɨ": frozenset(
        {"voc", "syllabic", "high", "central", "unround", "tense", "pulmonic", "sonorant"}
    ),
    "ʉ": frozenset(
        {"voc", "syllabic", "high", "central", "round", "tense", "pulmonic", "sonorant"}
    ),
    "ə": frozenset({"voc", "syllabic", "mid", "central", "unround", "lax", "pulmonic", "sonorant"}),
    "ɵ": frozenset({"voc", "syllabic", "mid", "central", "round", "tense", "pulmonic", "sonorant"}),
    "ɤ": frozenset({"voc", "syllabic", "mid", "back", "unround", "tense", "pulmonic", "sonorant"}),
    "o": frozenset({"voc", "syllabic", "mid", "back", "round", "tense", "pulmonic", "sonorant"}),
    "ɔ": frozenset({"voc", "syllabic", "mid", "back", "round", "lax", "pulmonic", "sonorant"}),
    "ʌ": frozenset({"voc", "syllabic", "mid", "back", "unround", "lax", "pulmonic", "sonorant"}),
    "u": frozenset({"voc", "syllabic", "high", "back", "round", "tense", "pulmonic", "sonorant"}),
    "ʊ": frozenset({"voc", "syllabic", "high", "back", "round", "lax", "pulmonic", "sonorant"}),
    "ɯ": frozenset({"voc", "syllabic", "high", "back", "unround", "tense", "pulmonic", "sonorant"}),
    # ── Long vowels ───────────────────────────────────────────
    "iː": frozenset(
        {"voc", "syllabic", "high", "front", "unround", "tense", "long", "pulmonic", "sonorant"}
    ),
    "yː": frozenset(
        {"voc", "syllabic", "high", "front", "round", "tense", "long", "pulmonic", "sonorant"}
    ),
    "eː": frozenset(
        {"voc", "syllabic", "mid", "front", "unround", "tense", "long", "pulmonic", "sonorant"}
    ),
    "øː": frozenset(
        {"voc", "syllabic", "mid", "front", "round", "tense", "long", "pulmonic", "sonorant"}
    ),
    "ɛː": frozenset(
        {"voc", "syllabic", "mid", "front", "unround", "lax", "long", "pulmonic", "sonorant"}
    ),
    "aː": frozenset(
        {"voc", "syllabic", "low", "central", "unround", "lax", "long", "pulmonic", "sonorant"}
    ),
    "ɔː": frozenset(
        {"voc", "syllabic", "mid", "back", "round", "lax", "long", "pulmonic", "sonorant"}
    ),
    "oː": frozenset(
        {"voc", "syllabic", "mid", "back", "round", "tense", "long", "pulmonic", "sonorant"}
    ),
    "uː": frozenset(
        {"voc", "syllabic", "high", "back", "round", "tense", "long", "pulmonic", "sonorant"}
    ),
    "ɤː": frozenset(
        {"voc", "syllabic", "mid", "back", "unround", "tense", "long", "pulmonic", "sonorant"}
    ),
    "əː": frozenset(
        {"voc", "syllabic", "mid", "central", "unround", "lax", "long", "pulmonic", "sonorant"}
    ),
    # ── Nasal vowels ──────────────────────────────────────────
    "ẽ": frozenset({"voc", "syllabic", "mid", "front", "unround", "nasal", "pulmonic", "sonorant"}),
    "ɛ̃": frozenset(
        {"voc", "syllabic", "mid", "front", "unround", "lax", "nasal", "pulmonic", "sonorant"}
    ),
    "ã": frozenset(
        {"voc", "syllabic", "low", "central", "unround", "lax", "nasal", "pulmonic", "sonorant"}
    ),
    "ɔ̃": frozenset(
        {"voc", "syllabic", "mid", "back", "round", "lax", "nasal", "pulmonic", "sonorant"}
    ),
    "õ": frozenset(
        {"voc", "syllabic", "mid", "back", "round", "tense", "nasal", "pulmonic", "sonorant"}
    ),
    "ũ": frozenset(
        {"voc", "syllabic", "high", "back", "round", "tense", "nasal", "pulmonic", "sonorant"}
    ),
    "ĩ": frozenset(
        {"voc", "syllabic", "high", "front", "unround", "tense", "nasal", "pulmonic", "sonorant"}
    ),
    # ── Legacy aliases (backward compat with shortened symbols) ──
    # ā = aː, ē = eː, ī = iː, ō = oː, ū = uː (defined below)
}

# Legacy long-vowel aliases for backward compatibility
_LEGACY_ALIASES: dict[str, str] = {
    "ā": "aː",
    "ē": "eː",
    "ī": "iː",
    "ō": "oː",
    "ū": "uː",
}

# Multi-character tokens that must be checked before single characters.
DIGRAPHS: tuple[str, ...] = (
    "kʷʰ",
    "gʷʰ",  # labiovelar aspirates (3-char)
    "kʷ",
    "gʷ",
    "ŋʷ",
    "kʰ",
    "gʰ",
    "pʰ",
    "bʰ",
    "tʰ",
    "dʰ",
    "cʰ",  # aspirates + labiovelars
    "tʃ",
    "dʒ",
    "tɕ",
    "dʑ",
    "ts",
    "dz",
    "pf",  # affricates
    "aː",
    "eː",
    "iː",
    "oː",
    "uː",
    "yː",
    "øː",
    "ɛː",
    "ɔː",
    "ɤː",
    "əː",  # long vowels
    "ɛ̃",
    "ɔ̃",
    "ã",
    "ẽ",
    "õ",
    "ũ",
    "ĩ",  # nasal vowels
    "ae",
    "ai",
    "au",
    "ei",
    "oi",
    "ou",
    "ea",
    "eu",
    "ia",
    "ie",
    "uo",  # common diphthongs
    "ɸ",
    "β",
    "θ",
    "ð",
    "ʃ",
    "ʒ",
    "ʂ",
    "ʐ",
    "ç",
    "ʝ",
    "χ",
    "ʁ",
    "ħ",
    "ʕ",
    "ɦ",  # fricatives
    "ŋ",
    "ɲ",
    "ɳ",
    "ɴ",
    "ɱ",  # nasals
    "ʎ",
    "ʟ",
    "ɭ",  # lateral approx
    "ʙ",
    "ɾ",
    "ɽ",  # trills/taps
    "ʔ",
    "ɢ",
    "ʡ",  # other stops
    "æ",
    "œ",
    "ɨ",
    "ʉ",
    "ɘ",
    "ɵ",
    "ɤ",
    "ɯ",
    "ʌ",
    "ɔ",
    "ɛ",
    "ɪ",
    "ʏ",
    "ʊ",
    "ə",
    "ɶ",  # vowels
    "ɓ",
    "ɗ",
    "ɠ",
    "ʛ",  # implosives
    "ɬ",
    "ɮ",  # lateral fricatives
    "ʋ",
    "ɥ",  # approximants
    "ǀ",
    "ǁ",
    "ǃ",
    "ǂ",  # clicks
)


@dataclass(frozen=True)
class Segment:
    symbol: str
    features: frozenset[str]

    @property
    def is_vowel(self) -> bool:
        return "voc" in self.features

    @property
    def is_consonant(self) -> bool:
        return "cons" in self.features


def feature_distance(a: Segment, b: Segment) -> float:
    """Jaccard distance between two segment feature sets."""
    if a.symbol == b.symbol:
        return 0.0
    if not a.features and not b.features:
        return 1.0
    inter = len(a.features & b.features)
    union = len(a.features | b.features) or 1
    return 1.0 - (inter / union)


def segment(symbol: str) -> Segment:
    """Look up or synthesize a Segment for the given symbol string."""
    sym = symbol.lower()
    # Check legacy aliases
    if sym in _LEGACY_ALIASES:
        sym = _LEGACY_ALIASES[sym]
    feats = FEATURES.get(sym, frozenset())
    return Segment(symbol=sym, features=feats)
