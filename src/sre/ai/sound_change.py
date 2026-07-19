"""Pairwise sound-change induction for cognate form sets."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class EditOp:
    op: str  # sub | del | ins | eq
    a: str
    b: str
    left: str
    right: str

    @property
    def rule_key(self) -> str:
        if self.op == "sub":
            ctx = f"{self.left}_{self.right}" if (self.left or self.right) else "_"
            return f"{self.a} → {self.b} / {ctx}"
        if self.op == "del":
            return f"{self.a} → ∅ / {self.left}_{self.right}"
        if self.op == "ins":
            return f"∅ → {self.b} / {self.left}_{self.right}"
        return f"{self.a} = {self.b}"


def levenshtein_align(a: str, b: str) -> list[tuple[str, str, str]]:
    """
    Return alignment as list of (op, a_char_or_empty, b_char_or_empty).
    op in {eq, sub, del, ins}.
    """
    a = a.lower()
    b = b.lower()
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = i
    for j in range(1, m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + cost,
            )
    # backtrace
    i, j = n, m
    ops_rev: list[tuple[str, str, str]] = []
    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + (
            0 if a[i - 1] == b[j - 1] else 1
        ):
            if a[i - 1] == b[j - 1]:
                ops_rev.append(("eq", a[i - 1], b[j - 1]))
            else:
                ops_rev.append(("sub", a[i - 1], b[j - 1]))
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            ops_rev.append(("del", a[i - 1], ""))
            i -= 1
        else:
            ops_rev.append(("ins", "", b[j - 1]))
            j -= 1
    return list(reversed(ops_rev))


def ops_with_context(alignment: list[tuple[str, str, str]]) -> list[EditOp]:
    out: list[EditOp] = []
    for idx, (op, ca, cb) in enumerate(alignment):
        if op == "eq":
            continue
        left = alignment[idx - 1][1] if idx > 0 else "#"
        right = alignment[idx + 1][1] if idx + 1 < len(alignment) else "#"
        # Prefer vocalic context markers
        if left not in {"#", ""} and left in "aeiou":
            left = "V"
        elif left not in {"#", ""}:
            left = "C"
        if right not in {"#", ""} and right in "aeiou":
            right = "V"
        elif right not in {"#", ""}:
            right = "C"
        out.append(EditOp(op=op, a=ca or "∅", b=cb or "∅", left=left, right=right))
    return out


def induce_sound_changes(
    pairs: Iterable[tuple[str, str, str, str]],
    *,
    min_support: int = 1,
) -> list[dict]:
    """
    Induce ranked sound-change rules from (form_a, form_b, id_a, id_b) pairs.

    Returns list of {rule, support, evidence_ids, pairs, score, source}.
    """
    rule_support: Counter[str] = Counter()
    rule_evidence: dict[str, set[str]] = defaultdict(set)
    rule_pairs: dict[str, list[tuple[str, str]]] = defaultdict(list)

    for form_a, form_b, id_a, id_b in pairs:
        if not form_a or not form_b or form_a == form_b:
            continue
        alignment = levenshtein_align(form_a, form_b)
        for edit in ops_with_context(alignment):
            key = edit.rule_key
            rule_support[key] += 1
            rule_evidence[key].update([id_a, id_b])
            rule_pairs[key].append((form_a, form_b))

    ranked: list[dict] = []
    for rule, support in rule_support.most_common():
        if support < min_support:
            continue
        evidence_ids = sorted(rule_evidence[rule])
        # Score: support * specificity (contextful rules beat bare ones)
        specificity = 1.5 if "/" in rule and "_" in rule else 1.0
        score = support * specificity
        ranked.append(
            {
                "rule": rule,
                "support": support,
                "score": score,
                "evidence_ids": evidence_ids,
                "pairs": rule_pairs[rule][:5],
                "source": "induced",
            }
        )
    ranked.sort(key=lambda r: (-r["score"], -r["support"], r["rule"]))
    return ranked


def cognate_form_pairs(
    members: list[dict],
) -> list[tuple[str, str, str, str]]:
    """Build pairwise form comparisons from cognate group members."""
    forms = [
        (str(m.get("form") or "").lower(), str(m.get("evidence_id") or ""))
        for m in members
        if m.get("form")
    ]
    pairs: list[tuple[str, str, str, str]] = []
    for i in range(len(forms)):
        for j in range(i + 1, len(forms)):
            fa, ia = forms[i]
            fb, ib = forms[j]
            pairs.append((fa, fb, ia, ib))
    return pairs
