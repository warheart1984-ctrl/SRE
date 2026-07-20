"""Phonological feature representations for phoneme-aware analysis."""

from __future__ import annotations

from dataclasses import dataclass

# Simplified IPA-ish segment inventory used by the correspondence engine.
FEATURES: dict[str, frozenset[str]] = {
    "p": frozenset({"cons", "labial", "stop", "vl"}),
    "b": frozenset({"cons", "labial", "stop", "vd"}),
    "t": frozenset({"cons", "coronal", "stop", "vl"}),
    "d": frozenset({"cons", "coronal", "stop", "vd"}),
    "k": frozenset({"cons", "velar", "stop", "vl"}),
    "g": frozenset({"cons", "velar", "stop", "vd"}),
    "kw": frozenset({"cons", "labiovelar", "stop", "vl"}),
    "gw": frozenset({"cons", "labiovelar", "stop", "vd"}),
    "m": frozenset({"cons", "labial", "nasal", "vd"}),
    "n": frozenset({"cons", "coronal", "nasal", "vd"}),
    "ŋ": frozenset({"cons", "velar", "nasal", "vd"}),
    "s": frozenset({"cons", "coronal", "fric", "vl"}),
    "z": frozenset({"cons", "coronal", "fric", "vd"}),
    "h": frozenset({"cons", "glottal", "fric", "vl"}),
    "f": frozenset({"cons", "labial", "fric", "vl"}),
    "v": frozenset({"cons", "labial", "fric", "vd"}),
    "θ": frozenset({"cons", "dental", "fric", "vl"}),
    "ð": frozenset({"cons", "dental", "fric", "vd"}),
    "x": frozenset({"cons", "velar", "fric", "vl"}),
    "l": frozenset({"cons", "coronal", "approx", "vd", "lateral"}),
    "r": frozenset({"cons", "coronal", "approx", "vd", "rhotic"}),
    "j": frozenset({"cons", "palatal", "approx", "vd"}),
    "w": frozenset({"cons", "labial", "approx", "vd"}),
    "i": frozenset({"voc", "high", "front"}),
    "e": frozenset({"voc", "mid", "front"}),
    "a": frozenset({"voc", "low", "central"}),
    "o": frozenset({"voc", "mid", "back", "round"}),
    "u": frozenset({"voc", "high", "back", "round"}),
    "ə": frozenset({"voc", "mid", "central"}),
    "ā": frozenset({"voc", "low", "central", "long"}),
    "ē": frozenset({"voc", "mid", "front", "long"}),
    "ī": frozenset({"voc", "high", "front", "long"}),
    "ō": frozenset({"voc", "mid", "back", "round", "long"}),
    "ū": frozenset({"voc", "high", "back", "round", "long"}),
}


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
    if a.symbol == b.symbol:
        return 0.0
    if not a.features and not b.features:
        return 1.0
    inter = len(a.features & b.features)
    union = len(a.features | b.features) or 1
    return 1.0 - (inter / union)


def segment(symbol: str) -> Segment:
    sym = symbol.lower()
    feats = FEATURES.get(sym, frozenset())
    return Segment(symbol=sym, features=feats)
