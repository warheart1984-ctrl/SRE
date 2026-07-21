"""Statistical cognate similarity (stdlib-only; no ML dependency)."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from .sound_change import levenshtein_align


def levenshtein_distance(a: str, b: str) -> int:
    """Edit distance via existing alignment backtrace."""
    alignment = levenshtein_align(a, b)
    return sum(1 for op, _, _ in alignment if op != "eq")


def normalized_similarity(a: str, b: str) -> float:
    """Return similarity in [0, 1] from normalized edit distance."""
    a = a.lower().strip()
    b = b.lower().strip()
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    dist = levenshtein_distance(a, b)
    denom = max(len(a), len(b), 1)
    return max(0.0, 1.0 - dist / denom)


def bigram_profile(form: str) -> Counter[str]:
    form = f"^{form.lower()}$"
    return Counter(form[i : i + 2] for i in range(len(form) - 1))


def bigram_similarity(a: str, b: str) -> float:
    """Dice coefficient on character bigram profiles."""
    pa = bigram_profile(a)
    pb = bigram_profile(b)
    if not pa and not pb:
        return 1.0
    overlap = sum((pa & pb).values())
    total = sum(pa.values()) + sum(pb.values())
    if total == 0:
        return 0.0
    return (2.0 * overlap) / total


def cognate_pair_score(form_a: str, form_b: str) -> float:
    """
    Blend edit-distance and bigram similarity for cognate ranking.

    Weighted toward edit distance for short forms; bigrams help longer strings.
    """
    edit_sim = normalized_similarity(form_a, form_b)
    ngram_sim = bigram_similarity(form_a, form_b)
    max_len = max(len(form_a), len(form_b), 1)
    edit_weight = 0.7 if max_len <= 5 else 0.55
    return edit_weight * edit_sim + (1.0 - edit_weight) * ngram_sim


def score_cognate_group(members: Iterable[dict]) -> float:
    """Mean pairwise cognate score for a group (>=1 member → 0)."""
    forms = [str(m.get("form") or "").lower() for m in members if m.get("form")]
    if len(forms) < 2:
        return 0.0
    total = 0.0
    pairs = 0
    for i in range(len(forms)):
        for j in range(i + 1, len(forms)):
            total += cognate_pair_score(forms[i], forms[j])
            pairs += 1
    return total / pairs if pairs else 0.0


def rank_cognate_groups(groups: list[dict], *, min_score: float = 0.35) -> list[dict]:
    """Attach ``cognate_score`` and filter weak groups."""
    ranked: list[dict] = []
    for group in groups:
        members = list(group.get("members") or [])
        score = score_cognate_group(members)
        enriched = dict(group)
        enriched["cognate_score"] = round(score, 4)
        if len(members) >= 2 and score >= min_score:
            ranked.append(enriched)
        elif len(members) == 1:
            enriched["cognate_score"] = 0.0
            ranked.append(enriched)
    ranked.sort(key=lambda g: (-float(g.get("cognate_score") or 0), g.get("group_id", "")))
    return ranked
