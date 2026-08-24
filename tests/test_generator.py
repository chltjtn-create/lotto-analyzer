"""Tests for condition-based combination generation."""

from __future__ import annotations

import unittest
from datetime import date

from lotto_analyzer.analysis.scoring import calculate_number_scores
from lotto_analyzer.domain.models import LottoDraw
from lotto_analyzer.generator import CombinationConstraints, DISCLAIMER, generate_combinations
from lotto_analyzer.generator.combination import _matches_constraints


def make_draw(draw_no: int, numbers: tuple[int, ...]) -> LottoDraw:
    """Create a valid draw for generator tests."""
    return LottoDraw(draw_no=draw_no, draw_date=date(2024, 1, min(draw_no, 28)), numbers=numbers, bonus=45)


class CombinationGenerationTest(unittest.TestCase):
    """Verify generated combinations satisfy default explainable constraints."""

    def test_generate_balanced_combinations(self) -> None:
        """Generate reproducible combinations with default constraints."""
        draws = [
            make_draw(1, (1, 2, 3, 24, 25, 26)),
            make_draw(2, (5, 6, 7, 28, 29, 30)),
            make_draw(3, (9, 10, 11, 31, 32, 33)),
            make_draw(4, (13, 14, 15, 34, 35, 36)),
        ]
        scores = calculate_number_scores(draws)

        combinations = generate_combinations(
            scores,
            constraints=CombinationConstraints(),
            strategy="Hybrid",
            count=3,
            seed=7,
        )

        self.assertEqual(len(combinations), 3)
        for combination in combinations:
            self.assertEqual(len(combination.numbers), 6)
            odd, even = (int(part) for part in combination.odd_even.split(":"))
            self.assertIn(odd, (2, 3, 4))
            self.assertIn(even, (2, 3, 4))
            low, high = (int(part) for part in combination.high_low.split(":"))
            self.assertIn(low, (2, 3, 4))
            self.assertIn(high, (2, 3, 4))
            self.assertGreaterEqual(combination.total_sum, 100)
            self.assertLessEqual(combination.total_sum, 180)
            self.assertEqual(combination.disclaimer, DISCLAIMER)

    def test_rejects_low_ac_and_arithmetic_and_decade_clustered_combinations(self) -> None:
        """Reject combinations with low AC value, constant gaps, or decade clustering."""
        constraints = CombinationConstraints()
        self.assertFalse(_matches_constraints((1, 2, 3, 4, 5, 6), constraints))
        self.assertFalse(_matches_constraints((5, 10, 15, 20, 25, 30), constraints))
        self.assertFalse(_matches_constraints((11, 12, 14, 16, 18, 19), constraints))

    def test_accepts_a_well_formed_combination(self) -> None:
        """Accept a combination with high AC value, no constant gap, and spread-out decades."""
        constraints = CombinationConstraints()
        self.assertTrue(_matches_constraints((3, 12, 18, 27, 33, 41), constraints))


if __name__ == "__main__":
    unittest.main()
