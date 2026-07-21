"""Evaluation metrics for reconstruction accuracy."""

from __future__ import annotations

from ..linguistics.features import feature_distance, segment
from ..linguistics.tokenization import tokenize


def segment_accuracy(
    true_proto: str,
    reconstructed_proto: str,
    *,
    feature_weighted: bool = True,
) -> dict[str, float]:
    """Compare true vs reconstructed proto-form at segment level.

    Returns precision, recall, f1, and edit-distance-based accuracy.
    """
    true_toks = tokenize(true_proto)
    recon_toks = tokenize(reconstructed_proto)

    true_symbols = [t.symbol for t in true_toks]
    recon_symbols = [t.symbol for t in recon_toks]

    # Length-normalised character accuracy (like Levenshtein similarity)
    from ..ai.sound_change import levenshtein_align

    alignment = levenshtein_align(true_proto, reconstructed_proto)
    matches = sum(1 for op, _, _ in alignment if op == "eq")
    total = len(alignment)
    edit_accuracy = 1.0 if total == 0 else matches / total

    # Segment-level precision / recall
    true_set = set(true_symbols)
    recon_set = set(recon_symbols)
    true_pos = len(true_set & recon_set)
    precision = true_pos / max(len(recon_set), 1)
    recall = true_pos / max(len(true_set), 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-10)

    # Feature-weighted accuracy
    fw_accuracy = 0.0
    if feature_weighted and len(true_symbols) == len(recon_symbols):
        fw_total = 0.0
        for ts, rs in zip(true_symbols, recon_symbols, strict=True):
            sa = segment(ts)
            sb = segment(rs)
            fw_total += 1.0 - feature_distance(sa, sb)
        fw_accuracy = fw_total / max(len(true_symbols), 1)

    return {
        "edit_accuracy": round(edit_accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "feature_weighted_accuracy": round(fw_accuracy, 4),
        "true_length": len(true_symbols),
        "reconstructed_length": len(recon_symbols),
    }


def sound_change_precision_recall(
    true_changes: list[tuple[str, str]],
    inferred_changes: list[dict],
) -> dict[str, float]:
    """Compare true (simulated) sound changes to inferred ones.

    Each true change is ``(from_segment, to_segment)``.
    Each inferred change is a dict with ``from`` / ``to`` keys.
    Returns precision, recall, F1.
    """
    true_set = set(true_changes)
    inferred_set = {(c.get("from", ""), c.get("to", "")) for c in inferred_changes}
    true_pos = len(true_set & inferred_set)
    precision = true_pos / max(len(inferred_set), 1)
    recall = true_pos / max(len(true_set), 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-10)

    return {
        "change_precision": round(precision, 4),
        "change_recall": round(recall, 4),
        "change_f1": round(f1, 4),
        "true_changes": len(true_set),
        "inferred_changes": len(inferred_set),
    }
