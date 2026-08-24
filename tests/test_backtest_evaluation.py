"""Tests for recommendation evaluation and backtesting."""

from __future__ import annotations

import unittest
from datetime import date

from lotto_analyzer.analysis.backtest import run_backtest
from lotto_analyzer.analysis.evaluation import RecommendationRecord, evaluate_recommendation, lotto_result_label
from lotto_analyzer.analysis.scoring import calculate_number_scores
from lotto_analyzer.domain.models import LottoDraw
from lotto_analyzer.generator import CombinationConstraints, generate_combinations


def make_draw(draw_no: int, numbers: tuple[int, ...], bonus: int = 45) -> LottoDraw:
    """Create a valid draw for backtest tests."""
    return LottoDraw(draw_no=draw_no, draw_date=date(2024, 1, min(draw_no, 28)), numbers=numbers, bonus=bonus)


class EvaluationAndBacktestTest(unittest.TestCase):
    """Verify recommendation evaluation and walk-forward backtesting."""

    def test_lotto_result_labels(self) -> None:
        """Map match counts to official-style result labels."""
        self.assertEqual(lotto_result_label(6, False), "1등")
        self.assertEqual(lotto_result_label(5, True), "2등")
        self.assertEqual(lotto_result_label(5, False), "3등")
        self.assertEqual(lotto_result_label(3, False), "5등")

    def test_evaluate_recommendation(self) -> None:
        """Compare a recommendation against an actual draw."""
        history = [make_draw(1, (1, 2, 3, 24, 25, 26))]
        scores = calculate_number_scores(history)
        generated = generate_combinations(
            scores,
            constraints=CombinationConstraints(
                odd_count=None,
                even_count=None,
                low_count=None,
                high_count=None,
                sum_min=21,
                sum_max=255,
                max_consecutive_pairs=6,
                max_same_last_digit=6,
                min_ac_value=None,
                exclude_arithmetic_sequence=False,
                max_per_decade=None,
            ),
            strategy="Random",
            count=1,
            seed=1,
        )[0]
        record = RecommendationRecord("test-1", 2, date(2024, 1, 1), generated)
        fillers = tuple(number for number in range(1, 46) if number not in generated.numbers)[:3]
        actual = make_draw(2, generated.numbers[:3] + fillers, bonus=generated.numbers[3])

        evaluation = evaluate_recommendation(record, actual)

        self.assertEqual(evaluation.match_count, 3)
        self.assertTrue(evaluation.bonus_matched)

    def test_run_backtest(self) -> None:
        """Run a loose-constraint backtest across multiple target draws."""
        draws = [
            make_draw(1, (1, 2, 3, 24, 25, 26)),
            make_draw(2, (5, 6, 7, 28, 29, 30)),
            make_draw(3, (9, 10, 11, 31, 32, 33)),
            make_draw(4, (13, 14, 15, 34, 35, 36)),
            make_draw(5, (17, 18, 19, 37, 38, 39)),
        ]

        summary = run_backtest(
            draws,
            3,
            5,
            strategy="Random",
            constraints=CombinationConstraints(
                odd_count=None,
                even_count=None,
                low_count=None,
                high_count=None,
                sum_min=21,
                sum_max=255,
                max_consecutive_pairs=6,
                max_same_last_digit=6,
                min_ac_value=None,
                exclude_arithmetic_sequence=False,
                max_per_decade=None,
            ),
            seed=3,
        )

        self.assertEqual(summary.total_rounds, 3)
        self.assertEqual(len(summary.rounds), 3)


if __name__ == "__main__":
    unittest.main()
