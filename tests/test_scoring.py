"""Tests for number scoring and classification."""

from __future__ import annotations

import unittest
from datetime import date

from lotto_analyzer.analysis.scoring import ScoreWeights, ScoringError, calculate_number_scores, category_groups
from lotto_analyzer.domain.models import LottoDraw


def make_draw(draw_no: int, numbers: tuple[int, ...]) -> LottoDraw:
    """Create a valid draw for scoring tests."""
    return LottoDraw(draw_no=draw_no, draw_date=date(2024, 1, min(draw_no, 28)), numbers=numbers, bonus=45)


class ScoringTest(unittest.TestCase):
    """Verify score rows and category splits."""

    def test_calculate_scores_for_all_numbers(self) -> None:
        """Calculate scores for every number from draw history."""
        draws = [
            make_draw(1, (1, 2, 3, 4, 5, 6)),
            make_draw(2, (1, 7, 8, 9, 10, 11)),
            make_draw(3, (1, 12, 13, 14, 15, 16)),
            make_draw(4, (21, 22, 23, 24, 25, 26)),
        ]

        scores = calculate_number_scores(draws)
        groups = category_groups(scores)

        self.assertEqual(len(scores), 45)
        self.assertEqual(len(groups["Hot"]), 9)
        self.assertEqual(len(groups["Cold"]), 9)
        self.assertGreaterEqual(scores[1].final_score, 0)
        self.assertIn(scores[1].category, {"Hot", "Warm", "Cold"})

    def test_invalid_weights_are_rejected(self) -> None:
        """Reject score weights that do not add up to 1."""
        with self.assertRaises(ScoringError):
            ScoreWeights(frequency=1, recency=1, gap=1, momentum=1).validate()


if __name__ == "__main__":
    unittest.main()
