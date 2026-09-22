"""Regression coverage for collection, immutable forecasts and evaluation."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from lotto_analyzer.analysis.backtest import BacktestError, run_backtest
from lotto_analyzer.analysis.evaluation import evaluate_recommendation, make_recommendation_batch
from lotto_analyzer.analysis.frequency import analyze_number_frequency, FrequencyAnalysisError
from lotto_analyzer.analysis.pattern import analyze_patterns
from lotto_analyzer.analysis.scoring import calculate_number_scores
from lotto_analyzer.automation import weekly_update as weekly
from lotto_analyzer.collector.crawler import (
    LottoCrawler, LottoDataError, LottoNetworkError, _parse_result_page_html,
    latest_expected_draw_no,
)
from lotto_analyzer.database import LottoDatabaseError, LottoDatabaseManager
from lotto_analyzer.domain.models import LottoDraw
from lotto_analyzer.generator.combination import generate_from_history
from lotto_analyzer.report.excel_export import export_excel_report
from lotto_analyzer.tests.test_collector import record_for_draw


def history(count=45):
    return [
        LottoDraw(
            i, date(2002, 12, 7) + timedelta(weeks=i - 1),
            tuple(sorted(((i * 7 + j * 6) % 45) + 1 for j in range(6))),
            ((i * 7 + 1) % 45) + 1,
        )
        for i in range(1, count + 1)
    ]


class CollectionReliabilityTest(unittest.TestCase):
    def test_json_requires_requested_round_and_date(self):
        with self.assertRaises(LottoDataError):
            LottoCrawler(fetch_json=lambda _: record_for_draw(2)).fetch_draw(999)
        payload = record_for_draw(2)
        payload["ltRflYmd"] = "20021207"
        with self.assertRaises(LottoDataError):
            LottoCrawler(fetch_json=lambda _: payload).fetch_draw(2)

    def test_html_ignores_unrelated_balls_and_requires_round(self):
        balls = "".join(f'<span class="ball_645">{n}</span>' for n in (10,23,29,33,37,40,16))
        region = '<div class="win_result"><h4>1회 당첨결과</h4><p>2002년 12월 7일 추첨</p>' + balls + "</div>"
        draw = _parse_result_page_html(1, '<span class="ball_645">45</span>' + region)
        self.assertEqual(draw.numbers, (10,23,29,33,37,40))
        for invalid in (region.replace("1회", "2회"), region.replace("<h4>1회 당첨결과</h4>", ""),
                        region.replace("2002년 12월 7일 추첨", ""), region + region):
            with self.subTest(html=invalid), self.assertRaises(LottoDataError):
                _parse_result_page_html(1, invalid)

    def test_saturday_and_utc_boundary(self):
        self.assertEqual(latest_expected_draw_no(datetime(2002,12,14,20,59)), 1)
        self.assertEqual(latest_expected_draw_no(datetime(2002,12,14,21,0)), 2)
        self.assertEqual(latest_expected_draw_no(datetime(2002,12,14,11,59,tzinfo=timezone.utc)), 1)
        self.assertEqual(latest_expected_draw_no(datetime(2002,12,14,12,0,tzinfo=timezone.utc)), 2)


class StorageReliabilityTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = LottoDatabaseManager(Path(self.temp.name) / "test.db")
        self.draws = history(10)
        self.db.save_draws(self.draws)

    def batch(self, count=5):
        return make_recommendation_batch(11, generate_from_history(self.draws, count=count, seed=3))

    def test_smaller_batch_retains_archive_but_replaces_active(self):
        old = self.batch()
        self.db.replace_recommendations(old)
        new = self.batch(1)
        self.db.replace_recommendations(new)
        self.assertEqual(self.db.list_recommendations(11), new)
        all_records = self.db.list_recommendations(11, include_archived=True)
        self.assertEqual(len(all_records), 6)
        self.assertEqual(sum(not r.is_active for r in all_records), 5)
        self.assertEqual({r.recommendation_id for r in all_records if not r.is_active},
                         {r.recommendation_id for r in old})

    def test_recommendations_are_immutable_and_retry_safe(self):
        record = self.batch(1)[0]
        self.db.save_recommendation(record)
        self.db.save_recommendation(record)
        changed = replace(record, combination=replace(record.combination, score=0))
        with self.assertRaises(LottoDatabaseError):
            self.db.save_recommendation(changed)
        self.assertEqual(self.db.list_recommendations(), [record])

    def test_replacement_retry_preserves_the_active_batch(self):
        records = self.batch()
        self.db.replace_recommendations(records)
        self.assertEqual(self.db.replace_recommendations(reversed(records)), len(records))
        self.assertEqual(self.db.list_recommendations(11), records)
        self.assertEqual(len(self.db.list_recommendations(include_archived=True)), len(records))
        self.db.save_draw(history(11)[-1])
        self.assertEqual(self.db.replace_recommendations(records), len(records))
        self.assertEqual(self.db.list_recommendations(11), records)

    def test_retrying_an_archived_batch_cannot_replace_the_current_batch(self):
        old = self.batch()
        current = self.batch(1)
        self.db.replace_recommendations(old)
        self.db.replace_recommendations(current)
        with self.assertRaises(LottoDatabaseError):
            self.db.replace_recommendations(old)
        self.assertEqual(self.db.list_recommendations(11), current)
        self.assertEqual(len(self.db.list_recommendations(include_archived=True)), 6)

    def test_failed_replacement_rolls_back_archive_change(self):
        original = self.batch()
        self.db.replace_recommendations(original)
        replacement = [replace(original[0], combination=replace(original[0].combination, score=0))]
        with self.assertRaises(LottoDatabaseError):
            self.db.replace_recommendations(replacement)
        self.assertEqual(len(self.db.list_recommendations()), 5)
        self.assertTrue(all(r.is_active for r in self.db.list_recommendations()))

    def test_correcting_draw_immediately_recalculates_evaluation(self):
        record = self.batch(1)[0]
        self.db.save_recommendation(record)
        numbers = record.combination.numbers
        unused = [n for n in range(1,46) if n not in numbers]
        actual = LottoDraw(11, date(2003,2,15), numbers, unused[0])
        self.db.save_draw(actual)
        self.db.save_evaluation(evaluate_recommendation(record, actual))
        corrected = replace(actual, numbers=tuple(unused[:6]), bonus=unused[6])
        self.db.save_draw(corrected)
        result = self.db.list_evaluations()[0]
        self.assertEqual(result.match_count, 0)
        self.assertEqual(result.actual_numbers, corrected.numbers)

    def test_announced_forecasts_cannot_be_replaced(self):
        record = self.batch(1)[0]
        self.db.save_recommendation(record)
        actual = history(11)[-1]
        self.db.save_draw(actual)
        with self.assertRaises(LottoDatabaseError):
            self.db.replace_recommendations(self.batch(1))
        self.assertEqual(self.db.list_recommendations(), [record])


class BacktestReliabilityTest(unittest.TestCase):
    def test_matches_production_budget_and_exclusions(self):
        draws = history()
        summary = run_backtest(draws, 11, 40, count=5, seed=7, baseline_repeats=3)
        self.assertEqual(summary.total_rounds, 30)
        self.assertEqual(summary.total_tickets, 150)
        self.assertEqual(len(summary.rounds), 150)
        self.assertIsNotNone(summary.difference_ci95)
        for target in range(11, 41):
            training = draws[:target-1]
            expected = generate_from_history(training, count=5, seed=7+target)
            actual = [r.generated for r in summary.rounds if r.target_draw_no == target]
            self.assertEqual(actual, expected)
            self.assertTrue(all(not set(c.numbers) & set(training[-1].numbers) for c in actual))
        self.assertAlmostEqual(summary.mean_match_difference,
                               summary.average_match_count-summary.random_average_match_count)

    def test_future_data_does_not_change_predictions_or_baseline(self):
        draws = history()
        short = run_backtest(draws[:30], 21, 30, count=2, seed=17)
        long = run_backtest(draws, 21, 30, count=2, seed=17)
        self.assertEqual(short, long)

    def test_missing_and_duplicate_rounds_are_rejected(self):
        draws = history(20)
        for invalid in (draws[:10]+draws[11:], draws+[draws[-1]]):
            with self.assertRaises(BacktestError):
                run_backtest(invalid, 10, 20)
        with self.assertRaises(FrequencyAnalysisError):
            analyze_number_frequency(draws[:10]+draws[11:])

    def test_excel_preserves_summary_and_ticket_details(self):
        from openpyxl import load_workbook
        draws = history(15)
        summary = run_backtest(draws, 11, 15, count=2)
        with tempfile.TemporaryDirectory() as tmp:
            path = export_excel_report(
                draws, analyze_number_frequency(draws), analyze_patterns(draws),
                calculate_number_scores(draws), backtest_summary=summary,
                output_path=Path(tmp)/"report.xlsx",
            )
            wb = load_workbook(path, read_only=True)
            try:
                rows = list(wb["백테스트"].values)
                self.assertEqual(len(rows), 11)
                self.assertIn("target_draw_no", rows[0])
                self.assertEqual(rows[1][0], 11)
                self.assertTrue(all(any(v is not None for v in row) for row in rows[1:]))
                self.assertIn("total_tickets", next(wb["백테스트요약"].values))
            finally:
                wb.close()


class WeeklyReliabilityTest(unittest.TestCase):
    def test_evaluation_includes_archived_batches_and_repairs_stale_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = LottoDatabaseManager(Path(tmp)/"data.db")
            draws = history(10)
            db.save_draws(draws)
            old = make_recommendation_batch(11, generate_from_history(draws, count=2, seed=3))
            current = make_recommendation_batch(11, generate_from_history(draws, count=1, seed=4))
            db.replace_recommendations(old)
            db.replace_recommendations(current)
            actual = history(11)[-1]
            db.save_draw(actual)
            evaluations = weekly._evaluate_due_recommendations(db, draws + [actual])
            self.assertEqual(len(evaluations), 3)
            self.assertEqual(len(db.list_evaluations()), 1)
            self.assertEqual(len(db.list_evaluations(include_archived=True)), 3)
            self.assertEqual(weekly._evaluate_due_recommendations(db, draws + [actual]), [])
            archived_evaluation = evaluate_recommendation(old[0], actual)
            db.save_evaluation(replace(archived_evaluation, match_count=-1))
            repaired = weekly._evaluate_due_recommendations(db, draws + [actual])
            self.assertEqual(repaired, [archived_evaluation])

    def test_failed_collection_reports_error_and_never_generates(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = LottoDatabaseManager(Path(tmp)/"data.db")
            db.save_draws(history(1))
            with patch.object(weekly, "LOG_DIR", Path(tmp)), \
                 patch.object(weekly, "load_dotenv"), \
                 patch.object(weekly, "ensure_project_directories"), \
                 patch.object(weekly, "LottoDatabaseManager", return_value=db), \
                 patch.object(weekly, "latest_expected_draw_no", return_value=3), \
                 patch.object(weekly.LottoCrawler, "fetch_draw", side_effect=LottoNetworkError("offline")), \
                 patch.object(weekly, "_generate_next_recommendations") as generate:
                result = weekly.run_weekly_update()
            self.assertTrue(result.errors)
            self.assertEqual(result.generated_recommendations, 0)
            generate.assert_not_called()
            self.assertEqual(db.list_recommendations(), [])

    def test_existing_batch_is_not_counted_as_new(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = LottoDatabaseManager(Path(tmp)/"data.db")
            draws = history(10)
            db.save_draws(draws)
            with patch.object(weekly, "require_current_history"):
                first = weekly._generate_next_recommendations(db, draws, 5, "Hybrid")
                second = weekly._generate_next_recommendations(db, draws, 5, "Hybrid")
            self.assertEqual(len(first), 5)
            self.assertEqual(second, [])
            self.assertEqual(len(db.list_recommendations()), 5)


if __name__ == "__main__":
    unittest.main()
