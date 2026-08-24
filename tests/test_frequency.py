"""Tests for number frequency analysis."""

from __future__ import annotations

import unittest
from datetime import date

from lotto_analyzer.analysis.frequency import (
    FrequencyAnalysisError,
    analyze_number_frequency,
    format_number_stats,
    stats_to_rows,
)
from lotto_analyzer.domain.models import LottoDraw


def make_draw(draw_no: int, numbers: tuple[int, ...]) -> LottoDraw:
    """Create a valid LottoDraw for frequency tests."""
    return LottoDraw(
        draw_no=draw_no,
        draw_date=date(2024, 1, min(draw_no, 28)),
        numbers=numbers,
        bonus=45 if 45 not in numbers else 44,
    )


def sample_draws() -> list[LottoDraw]:
    """Return a small deterministic draw history for analysis tests."""
    return [
        make_draw(1, (1, 2, 3, 4, 5, 6)),
        make_draw(2, (1, 7, 8, 9, 10, 11)),
        make_draw(3, (2, 12, 13, 14, 15, 16)),
        make_draw(4, (1, 2, 17, 18, 19, 20)),
        make_draw(5, (21, 22, 23, 24, 25, 26)),
    ]


class FrequencyAnalysisTest(unittest.TestCase):
    """Verify total, recent, and missing counts."""

    def test_analyze_all_45_numbers(self) -> None:
        """Return one result row for every Lotto number."""
        stats = analyze_number_frequency(sample_draws(), windows=(2, 3))

        self.assertEqual(len(stats), 45)
        self.assertEqual(stats[1].total_count, 3)
        self.assertEqual(stats[1].recent_counts[2], 1)
        self.assertEqual(stats[1].recent_counts[3], 1)
        self.assertEqual(stats[1].missing_draws, 1)
        self.assertEqual(stats[1].last_seen_draw_no, 4)
        self.assertFalse(stats[1].appeared_in_latest_draw)

    def test_number_in_latest_has_zero_missing_draws(self) -> None:
        """Report zero missing draws when a number appears in the latest draw."""
        stats = analyze_number_frequency(sample_draws(), windows=(10,))

        self.assertEqual(stats[21].missing_draws, 0)
        self.assertTrue(stats[21].appeared_in_latest_draw)
        self.assertEqual(stats[21].recent_counts[10], 1)
        self.assertEqual(stats[21].recent_available_draws[10], 5)

    def test_number_never_seen_uses_total_analyzed_draws_as_missing(self) -> None:
        """Report total analyzed draw count when a number never appeared."""
        stats = analyze_number_frequency(sample_draws(), windows=(2,))

        self.assertEqual(stats[30].total_count, 0)
        self.assertEqual(stats[30].missing_draws, 5)
        self.assertIsNone(stats[30].last_seen_draw_no)

    def test_unsorted_input_is_sorted_before_analysis(self) -> None:
        """Sort draws by draw number before recent-window analysis."""
        draws = list(reversed(sample_draws()))

        stats = analyze_number_frequency(draws, windows=(1,))

        self.assertEqual(stats[21].recent_counts[1], 1)
        self.assertEqual(stats[1].recent_counts[1], 0)
        self.assertEqual(stats[1].latest_draw_no, 5)

    def test_duplicate_draw_numbers_are_rejected(self) -> None:
        """Reject duplicated draw numbers to avoid ambiguous history."""
        draws = [sample_draws()[0], sample_draws()[0]]

        with self.assertRaises(FrequencyAnalysisError):
            analyze_number_frequency(draws)

    def test_empty_draws_are_rejected(self) -> None:
        """Reject empty analysis input."""
        with self.assertRaises(FrequencyAnalysisError):
            analyze_number_frequency([])

    def test_invalid_windows_are_rejected(self) -> None:
        """Reject zero or duplicated recent-window values."""
        with self.assertRaises(FrequencyAnalysisError):
            analyze_number_frequency(sample_draws(), windows=(0,))
        with self.assertRaises(FrequencyAnalysisError):
            analyze_number_frequency(sample_draws(), windows=(10, 10))

    def test_format_and_rows_helpers(self) -> None:
        """Convert stats to user-facing text and sorted row dictionaries."""
        stats = analyze_number_frequency(sample_draws(), windows=(2,))

        text = format_number_stats(stats[1])
        rows = stats_to_rows(stats)

        self.assertIn("번호 1", text)
        self.assertIn("최근2회 : 1회", text)
        self.assertEqual(rows[0]["number"], 1)
        self.assertEqual(rows[-1]["number"], 45)


if __name__ == "__main__":
    unittest.main()
