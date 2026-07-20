"""Weighted sequence alignment over phonological segments."""

from __future__ import annotations

from dataclasses import dataclass

from .features import Segment, feature_distance


@dataclass
class AlignCell:
    op: str  # eq|sub|del|ins
    a: Segment | None
    b: Segment | None
    cost: float


def weighted_align(
    a: list[Segment],
    b: list[Segment],
    *,
    sub_weight: float = 1.0,
    indel_weight: float = 1.1,
) -> tuple[list[AlignCell], float]:
    """Needleman–Wunsch style alignment with feature-aware substitution cost."""
    n, m = len(a), len(b)
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    back: list[list[str]] = [["eq"] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = i * indel_weight
        back[i][0] = "del"
    for j in range(1, m + 1):
        dp[0][j] = j * indel_weight
        back[0][j] = "ins"
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            sub = dp[i - 1][j - 1] + sub_weight * feature_distance(a[i - 1], b[j - 1])
            delete = dp[i - 1][j] + indel_weight
            insert = dp[i][j - 1] + indel_weight
            best = min(sub, delete, insert)
            dp[i][j] = best
            if best == sub:
                back[i][j] = "eq" if a[i - 1].symbol == b[j - 1].symbol else "sub"
            elif best == delete:
                back[i][j] = "del"
            else:
                back[i][j] = "ins"
    # traceback
    i, j = n, m
    path: list[AlignCell] = []
    while i > 0 or j > 0:
        op = back[i][j] if i > 0 and j > 0 else ("del" if i > 0 else "ins")
        if op in {"eq", "sub"} and i > 0 and j > 0:
            cost = sub_weight * feature_distance(a[i - 1], b[j - 1])
            path.append(AlignCell(op=op, a=a[i - 1], b=b[j - 1], cost=cost))
            i -= 1
            j -= 1
        elif op == "del" or (j == 0 and i > 0):
            path.append(AlignCell(op="del", a=a[i - 1], b=None, cost=indel_weight))
            i -= 1
        else:
            path.append(AlignCell(op="ins", a=None, b=b[j - 1], cost=indel_weight))
            j -= 1
    path.reverse()
    return path, dp[n][m]
