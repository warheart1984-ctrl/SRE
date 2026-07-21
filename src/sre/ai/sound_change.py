"""Pairwise sound-change induction for cognate form sets.

Also provides a SoundChangeApplier that can apply inferred or known
sound changes forward (proto → daughter) to test reconstruction hypotheses.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass


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
        if i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + (0 if a[i - 1] == b[j - 1] else 1):
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


class SoundChangeRule:
    """A single sound change rule (e.g. 'p → f / #_')."""

    def __init__(
        self,
        from_seg: str,
        to_seg: str,
        left_ctx: str = "",
        right_ctx: str = "",
        *,
        name: str = "",
    ) -> None:
        self.from_seg = from_seg
        self.to_seg = to_seg
        self.left_ctx = left_ctx
        self.right_ctx = right_ctx
        self.name = name or f"{from_seg}→{to_seg}"

    def applies(self, segment: str, left: str, right: str) -> bool:
        """Check if this rule applies in the given context."""
        if segment != self.from_seg:
            return False
        if self.left_ctx and left != self.left_ctx:
            return False
        if self.right_ctx and right != self.right_ctx:
            return False
        return True

    @classmethod
    def from_branch_transform(cls, transform: tuple[str, str, str]) -> SoundChangeRule:
        """Create a rule from a BRANCH_TRANSFORMS entry (proto_seg, daughter_seg, name)."""
        return cls(
            from_seg=transform[0],
            to_seg=transform[1],
            name=transform[2],
        )


class SoundChangeApplier:
    """Apply sound changes forward from a proto-form to predict daughter forms."""

    def __init__(self, rules: list[SoundChangeRule] | None = None) -> None:
        self.rules = rules or []

    @classmethod
    def from_branch_transforms(
        cls,
        transforms: list[tuple[str, str, str]],
    ) -> SoundChangeApplier:
        """Build an applier from a BRANCH_TRANSFORMS-style list."""
        return cls(rules=[SoundChangeRule.from_branch_transform(t) for t in transforms])

    def apply(self, proto_form: str) -> str:
        """Apply all rules in sequence to a proto-form string."""
        from ..linguistics.tokenization import tokenize

        segments = tokenize(proto_form)
        result_chars: list[str] = []
        n = len(segments)

        for i, seg in enumerate(segments):
            left = segments[i - 1].symbol if i > 0 else "#"
            right = segments[i + 1].symbol if i + 1 < n else "#"
            applied = False
            for rule in self.rules:
                if rule.applies(seg.symbol, left, right):
                    result_chars.append(rule.to_seg)
                    applied = True
                    break
            if not applied:
                result_chars.append(seg.symbol)

        return "".join(result_chars)

    def apply_to_languages(
        self,
        proto_form: str,
        branch_transforms: dict[str, list[tuple[str, str, str]]],
    ) -> dict[str, str]:
        """Apply branch-specific transforms to predict daughter forms."""
        predicted: dict[str, str] = {}
        for branch, transforms in branch_transforms.items():
            applier = self.from_branch_transforms(transforms)
            predicted[branch] = applier.apply(proto_form)
        return predicted

    def score_prediction(
        self, proto_form: str, target_form: str, rules: list[SoundChangeRule]
    ) -> dict[str, Any]:
        """
        Score how well a set of rules predicts a target form from a proto-form.
        Returns accuracy metrics and alignment details.
        """
        from ..linguistics.alignment import weighted_align
        from ..linguistics.tokenization import tokenize, tokens_to_str

        applier = SoundChangeApplier(rules)
        predicted = applier.apply(proto_form)
        pt = tokens_to_str(tokenize(predicted))
        tt = tokens_to_str(tokenize(target_form))
        path, cost = weighted_align(tokenize(predicted), tokenize(target_form))
        max_len = max(len(pt), len(tt), 1)
        similarity = 1.0 - (cost / (max_len * 1.1))
        return {
            "predicted": predicted,
            "target": target_form,
            "alignment_cost": round(cost, 4),
            "similarity": round(similarity, 4),
            "perfect_match": predicted == target_form,
            "edit_ops": len(path),
        }
