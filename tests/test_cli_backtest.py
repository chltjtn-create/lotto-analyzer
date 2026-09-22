"""Regression coverage for shared recommendation and backtest CLI settings."""

from __future__ import annotations

from contextlib import redirect_stdout
from datetime import date, timedelta
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from lotto_analyzer import main as cli
from lotto_analyzer.database import LottoDatabaseManager
from lotto_analyzer.domain.models import LottoDraw
from lotto_analyzer.generator.combination import DEFAULT_RECOMMENDATION_CONSTRAINTS


class BacktestCliTest(unittest.TestCase):
    def test_parser_matches_recommendation_defaults_and_custom_settings(self):
        parser = cli.build_parser()
        for options in (
            [],
            ["--exclude-latest"],
            ["--sum-min", "120", "--sum-max", "150", "--no-exclude-latest",
             "--strategy", "Random", "--count", "3"],
        ):
            with self.subTest(options=options):
                recommendation = parser.parse_args(["recommend", *options])
                backtest = parser.parse_args(["backtest", "11", "15", *options])
                self.assertEqual(cli._constraints_from_args(backtest),
                                 cli._constraints_from_args(recommendation))
                self.assertEqual(backtest.strategy, recommendation.strategy)
                self.assertEqual(backtest.count, recommendation.count)
                if not options:
                    self.assertEqual(cli._constraints_from_args(backtest),
                                     DEFAULT_RECOMMENDATION_CONSTRAINTS)

    def test_custom_cli_settings_reach_backtest_and_json_output(self):
        draws = [
            LottoDraw(
                i, date(2002, 12, 7) + timedelta(weeks=i - 1),
                tuple(sorted(((i * 7 + j * 6) % 45) + 1 for j in range(6))),
                ((i * 7 + 1) % 45) + 1,
            )
            for i in range(1, 16)
        ]
        options = ["--sum-min", "120", "--sum-max", "150", "--no-exclude-latest",
                   "--strategy", "Random", "--count", "3"]
        recommendation = cli.build_parser().parse_args(["recommend", *options])
        expected_constraints = cli._constraints_from_args(recommendation)
        output = StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            database = LottoDatabaseManager(Path(tmp) / "test.db")
            database.save_draws(draws)
            with patch.object(cli, "ensure_project_directories"), \
                 patch.object(cli, "LottoCrawler"), \
                 patch.object(cli, "LottoDatabaseManager", return_value=database), \
                 patch.object(cli, "run_backtest", wraps=cli.run_backtest) as run_backtest, \
                 redirect_stdout(output):
                status = cli.main(["backtest", "11", "15", *options,
                                   "--seed", "19", "--baseline-repeats", "2"])
            run_backtest.assert_called_once_with(
                draws, 11, 15, strategy="Random", constraints=expected_constraints,
                count=3, seed=19, baseline_repeats=2,
            )
        result = json.loads(output.getvalue())
        self.assertEqual(status, 0)
        self.assertEqual(result["summary"]["total_tickets"], 15)
        self.assertEqual(result["summary"]["tickets_per_draw"], 3)
        self.assertEqual(result["summary"]["seed"], 19)
        self.assertEqual(result["summary"]["baseline_repeats"], 2)
        constraints = result["summary"]["settings"]["constraints"]
        self.assertEqual((constraints["sum_min"], constraints["sum_max"]), (120, 150))
        self.assertFalse(constraints["exclude_latest_draw_numbers"])
        self.assertEqual(len(result["rounds"]), 15)
        self.assertTrue(all(120 <= sum(row["generated_numbers"]) <= 150
                            for row in result["rounds"]))


if __name__ == "__main__":
    unittest.main()
