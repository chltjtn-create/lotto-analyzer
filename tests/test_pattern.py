"""Tests for draw pattern analysis."""

from __future__ import annotations

import unittest
from datetime import date

from lotto_analyzer.analysis.pattern import analyze_draw_pattern, analyze_patterns, pattern_rows
from lotto_analyzer.domain.models import LottoDraw


def make_draw(draw_no: int, numbers: tuple[int, ...]) -> LottoDraw:
    """Create a valid draw for pattern tests."""
    bonus = next(number for number in range(1, 46) if number not in numbers)
    return LottoDraw(draw_no=draw_no, draw_date=date(2024, 1, draw_no), numbers=numbers, bonus=bonus)


class PatternAnalysisTest(unittest.TestCase):
    """Verify per-draw and aggregate pattern values."""

    def test_analyze_draw_pattern(self) -> None:
        """Calculate expected pattern values for one draw."""
        pattern = analyze_draw_pattern(make_draw(1, (1, 2, 3, 11, 22, 45)))

        self.assertEqual(pattern.odd_even_ratio, "4:2")
        self.assertEqual(pattern.high_low_ratio, "5:1")
        self.assertEqual(pattern.consecutive_pairs, ((1, 2), (2, 3)))
        self.assertEqual(pattern.total_sum, 84)
        self.assertEqual(pattern.section_counts["1-10"], 3)
        self.assertEqual(pattern.max_same_last_digit, 2)

    def test_analyze_patterns_summary(self) -> None:
        """Aggregate pattern frequencies across draws."""
        draws = [
            make_draw(1, (1, 2, 3, 11, 22, 44)),
            make_draw(2, (5, 8, 13, 24, 31, 42)),
        ]

        summary = analyze_patterns(draws)
        rows = pattern_rows(summary)

        self.assertEqual(summary.odd_even_frequency["3:3"], 2)
        self.assertEqual(summary.high_low_frequency["5:1"], 1)
        self.assertEqual(summary.high_low_frequency["3:3"], 1)
        self.assertEqual(summary.consecutive_draw_count, 1)
        self.assertEqual(len(rows), 2)


if __name__ == "__main__":
    unittest.main()
