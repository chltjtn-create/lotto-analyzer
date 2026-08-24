"""Tests for SQLite storage and backup exports."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from lotto_analyzer.analysis.evaluation import RecommendationEvaluation, RecommendationRecord
from lotto_analyzer.database import LottoDatabaseManager
from lotto_analyzer.domain.models import LottoDraw
from lotto_analyzer.generator import GeneratedCombination


def make_draw(draw_no: int) -> LottoDraw:
    """Create a valid LottoDraw with deterministic test numbers."""
    return LottoDraw(
        draw_no=draw_no,
        draw_date=date(2024, 1, min(draw_no, 28)),
        numbers=(1, 2, 3, 4, 5, 6),
        bonus=7,
    )


class LottoDatabaseManagerTest(unittest.TestCase):
    """Verify database persistence and backup behavior."""

    def test_initialize_database_creates_file(self) -> None:
        """Create the SQLite database file and schema."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "lotto.db"
            manager = LottoDatabaseManager(db_path)

            manager.initialize_database()

            self.assertTrue(db_path.exists())

    def test_save_and_get_draw(self) -> None:
        """Save one draw and load it back as a LottoDraw."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = LottoDatabaseManager(Path(temp_dir) / "lotto.db")
            original = make_draw(1)

            manager.save_draw(original)
            loaded = manager.get_draw(1)

            self.assertEqual(loaded, original)

    def test_duplicate_save_keeps_single_row(self) -> None:
        """Saving the same draw twice should not create duplicates."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = LottoDatabaseManager(Path(temp_dir) / "lotto.db")
            draw = make_draw(1)

            manager.save_draw(draw)
            manager.save_draw(draw)

            self.assertEqual(manager.count_draws(), 1)

    def test_save_draws_and_latest_draw(self) -> None:
        """Save many draws and return the highest draw number."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = LottoDatabaseManager(Path(temp_dir) / "lotto.db")

            processed_count = manager.save_draws([make_draw(1), make_draw(2), make_draw(3)])

            self.assertEqual(processed_count, 3)
            self.assertEqual(manager.get_latest_draw_no(), 3)
            self.assertEqual([draw.draw_no for draw in manager.list_draws()], [1, 2, 3])

    def test_missing_draw_returns_none(self) -> None:
        """Return None when a requested draw is not stored."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = LottoDatabaseManager(Path(temp_dir) / "lotto.db")

            self.assertIsNone(manager.get_draw(999))

    def test_export_to_csv(self) -> None:
        """Export stored draws to a CSV file with expected headers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            manager = LottoDatabaseManager(temp_path / "lotto.db")
            manager.save_draws([make_draw(1), make_draw(2)])

            csv_path = manager.export_to_csv(temp_path / "lotto.csv")

            with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
                rows = list(csv.DictReader(csv_file))

            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["draw_no"], "1")
            self.assertEqual(rows[0]["bonus"], "7")

    def test_export_to_json(self) -> None:
        """Export stored draws to a JSON file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            manager = LottoDatabaseManager(temp_path / "lotto.db")
            manager.save_draws([make_draw(1), make_draw(2)])

            json_path = manager.export_to_json(temp_path / "lotto.json")

            with json_path.open("r", encoding="utf-8") as json_file:
                rows = json.load(json_file)

            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[1]["draw_no"], 2)
            self.assertEqual(rows[1]["num6"], 6)

    def test_save_recommendation_and_evaluation(self) -> None:
        """Save and load recommendation history with evaluation results."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = LottoDatabaseManager(Path(temp_dir) / "lotto.db")
            combination = GeneratedCombination(
                numbers=(1, 2, 3, 24, 25, 26),
                score=77.7,
                odd_even="3:3",
                high_low="3:3",
                total_sum=81,
                hot_count=2,
                warm_count=3,
                cold_count=1,
                strategy="Hybrid",
            )
            record = RecommendationRecord(
                recommendation_id="rec-1",
                target_draw_no=10,
                created_date=date(2024, 1, 1),
                combination=combination,
            )
            evaluation = RecommendationEvaluation(
                recommendation_id="rec-1",
                target_draw_no=10,
                recommended_numbers=combination.numbers,
                actual_numbers=(1, 2, 3, 30, 31, 32),
                bonus=24,
                matched_numbers=(1, 2, 3),
                match_count=3,
                bonus_matched=True,
                result_label="5등",
            )

            manager.save_recommendation(record)
            manager.save_evaluation(evaluation)

            self.assertEqual(manager.list_recommendations(10)[0].recommendation_id, "rec-1")
            self.assertEqual(manager.list_evaluations()[0].match_count, 3)


if __name__ == "__main__":
    unittest.main()
