"""Tests for chart and Excel report exports."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from datetime import date
from pathlib import Path

from lotto_analyzer.analysis.frequency import analyze_number_frequency
from lotto_analyzer.analysis.pattern import analyze_patterns
from lotto_analyzer.analysis.scoring import calculate_number_scores
from lotto_analyzer.domain.models import LottoDraw
from lotto_analyzer.report.chart import export_all_charts
from lotto_analyzer.report.excel_export import export_excel_report


def make_draw(draw_no: int, numbers: tuple[int, ...]) -> LottoDraw:
    """Create a valid draw for report tests."""
    return LottoDraw(draw_no=draw_no, draw_date=date(2024, 1, draw_no), numbers=numbers, bonus=45)


class ReportExportTest(unittest.TestCase):
    """Verify optional report exports when dependencies are available."""

    def test_export_charts_when_matplotlib_available(self) -> None:
        """Export all chart PNGs when matplotlib is installed."""
        if importlib.util.find_spec("matplotlib") is None:
            self.skipTest("matplotlib is not installed")
        draws = [
            make_draw(1, (1, 2, 3, 24, 25, 26)),
            make_draw(2, (5, 6, 7, 28, 29, 30)),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            paths = export_all_charts(
                analyze_number_frequency(draws),
                calculate_number_scores(draws),
                analyze_patterns(draws),
                Path(temp_dir),
            )

            self.assertEqual(len(paths), 4)
            self.assertTrue(all(path.exists() for path in paths))

    def test_export_excel_when_openpyxl_available(self) -> None:
        """Export the Excel workbook when openpyxl is installed."""
        if importlib.util.find_spec("openpyxl") is None:
            self.skipTest("openpyxl is not installed")
        draws = [
            make_draw(1, (1, 2, 3, 24, 25, 26)),
            make_draw(2, (5, 6, 7, 28, 29, 30)),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            path = export_excel_report(
                draws,
                analyze_number_frequency(draws),
                analyze_patterns(draws),
                calculate_number_scores(draws),
                output_path=Path(temp_dir) / "lotto_report.xlsx",
            )

            self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()
