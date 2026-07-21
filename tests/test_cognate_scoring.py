"""Statistical cognate scoring tests."""

from __future__ import annotations

import unittest

from sre.ai.cognate_scoring import cognate_pair_score, rank_cognate_groups, score_cognate_group


class TestCognateScoring(unittest.TestCase):
    def test_identical_forms_score_high(self) -> None:
        self.assertGreaterEqual(cognate_pair_score("pater", "pater"), 0.99)

    def test_related_forms_score_above_unrelated(self) -> None:
        related = cognate_pair_score("pater", "padre")
        unrelated = cognate_pair_score("pater", "xyzq")
        self.assertGreater(related, unrelated)

    def test_group_ranking(self) -> None:
        groups = [
            {
                "group_id": "weak",
                "members": [{"form": "aaa"}, {"form": "zzz"}],
            },
            {
                "group_id": "strong",
                "members": [{"form": "pater"}, {"form": "padre"}],
            },
        ]
        ranked = rank_cognate_groups(groups, min_score=0.0)
        self.assertEqual(ranked[0]["group_id"], "strong")
        self.assertGreaterEqual(len(ranked), 2)
        self.assertGreater(ranked[0]["cognate_score"], ranked[1]["cognate_score"])

    def test_single_member_group_score_zero(self) -> None:
        self.assertEqual(score_cognate_group([{"form": "solo"}]), 0.0)


if __name__ == "__main__":
    unittest.main()
