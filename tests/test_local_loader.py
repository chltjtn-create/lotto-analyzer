"""Tests for local Excel data loading."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from lotto_analyzer.collector.local_loader import load_draws_from_excel


class LocalLoaderTest(unittest.TestCase):
    """Verify local Excel import for the workspace data format."""

    def test_load_draws_from_excel(self) -> None:
        """Load draw rows from an Excel workbook using expected columns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "lotto.xlsx"
            workbook = Workbook()
            worksheet = workbook.active
            worksheet.append(["회차", "추첨일"])
            worksheet.append([None] * 20)
            worksheet.append([1, "2002.12.07", None, None, None, None, None, None, None, None, None, None, 10, 23, 29, 33, 37, 40, 16, "10 23 29 33 37 40"])
            workbook.save(path)

            draws = load_draws_from_excel(path)

            self.assertEqual(len(draws), 1)
            self.assertEqual(draws[0].draw_no, 1)
            self.assertEqual(draws[0].numbers, (10, 23, 29, 33, 37, 40))
            self.assertEqual(draws[0].bonus, 16)


if __name__ == "__main__":
    unittest.main()
