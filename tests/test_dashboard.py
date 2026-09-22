"""Exercise the actual Streamlit entry point using isolated databases."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from lotto_analyzer.analysis.evaluation import evaluate_recommendation, make_recommendation_batch
from lotto_analyzer.database import LottoDatabaseManager
from lotto_analyzer.domain.models import LottoDraw
from lotto_analyzer.generator.combination import generate_from_history
from lotto_analyzer.tests.test_reliability import history


@unittest.skipUnless(importlib.util.find_spec("streamlit"), "Streamlit is not installed")
class DashboardTest(unittest.TestCase):
    def setUp(self):
        import streamlit as st
        from streamlit.testing.v1 import AppTest

        st.cache_data.clear()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = LottoDatabaseManager(Path(self.temp.name)/"ui.db")
        self.db.initialize_database()
        patcher = patch("lotto_analyzer.database.db_manager.LottoDatabaseManager", return_value=self.db)
        patcher.start()
        self.addCleanup(patcher.stop)
        clock = patch(
            "lotto_analyzer.collector.crawler.latest_expected_draw_no",
            side_effect=lambda: self.db.get_latest_draw_no() or 1,
        )
        clock.start()
        self.addCleanup(clock.stop)
        self.app = AppTest.from_file(
            str(Path(__file__).resolve().parents[1]/"dashboard"/"app.py"), default_timeout=30
        )

    def navigate(self, name):
        option = next(value for value in self.app.sidebar.radio[0].options if name in value)
        self.app.sidebar.radio[0].set_value(option).run()
        self.assertFalse(self.app.exception)

    def press(self, label):
        button = next(button for button in self.app.button if label in button.label)
        button.click().run()
        self.assertFalse(self.app.exception)

    def test_empty_database_can_import_and_reach_home(self):
        self.app.run()
        self.assertFalse(self.app.exception)
        self.navigate("데이터 업데이트")
        self.assertTrue(self.app.text_input(key="xls_path"))
        self.app.text_input(key="xls_path").set_value("fixture.xlsx")
        with patch("lotto_analyzer.collector.local_loader.load_draws_from_excel", return_value=history(15)):
            self.press("엑셀 가져오기")
        self.assertEqual(self.db.count_draws(), 15)
        self.navigate("홈")

    def test_generation_replaces_batch_and_archive_is_visible(self):
        self.db.save_draws(history())
        self.app.run()
        self.navigate("조합 생성")
        self.app.checkbox(key="save_rec").set_value(True)
        self.press("조합 생성")
        self.assertFalse(self.app.warning)
        self.assertEqual(len(self.db.list_recommendations()), 5)
        self.app.number_input(key="cnt").set_value(1)
        self.press("조합 생성")
        self.assertEqual(len(self.db.list_recommendations()), 1)
        self.assertEqual(len(self.db.list_recommendations(include_archived=True)), 6)
        self.navigate("추천 이력")
        self.app.checkbox(key="show_archived").check().run()
        self.assertFalse(self.app.exception)

    def test_backtest_runs_requested_budget(self):
        self.db.save_draws(history())
        self.app.run()
        self.navigate("백테스트")
        self.app.number_input(key="bt_rounds").set_value(10)
        self.app.number_input(key="bt_count").set_value(2)
        self.press("백테스트 실행")
        values = {metric.label: metric.value for metric in self.app.metric}
        self.assertEqual(values["테스트 회차"], "10회")
        self.assertEqual(values["평가 게임"], "20게임")
        self.assertIn("균등 무작위 평균 적중", values)

    def test_history_top_prize_counts_toward_fifth_or_better(self):
        draws = history()
        self.db.save_draws(draws)
        record = make_recommendation_batch(46, generate_from_history(draws, count=1, seed=5))[0]
        self.db.save_recommendation(record)
        numbers = record.combination.numbers
        actual = LottoDraw(46, history(46)[-1].draw_date, numbers,
                           next(n for n in range(1,46) if n not in numbers))
        self.db.save_draw(actual)
        self.db.save_evaluation(evaluate_recommendation(record, actual))
        self.app.run()
        self.navigate("추천 이력")
        values = {metric.label: metric.value for metric in self.app.metric}
        self.assertEqual(values["5등 이상 (5등+)"], "1건")

    def test_statistics_pages_render(self):
        self.db.save_draws(history())
        self.app.run()
        for page in ("번호 통계", "과열", "패턴", "데이터 업데이트"):
            self.navigate(page)
        self.assertIn("Hot Mix", self.app.selectbox(key="wk_strat").options)
        self.assertIn("Cold Mix", self.app.selectbox(key="wk_strat").options)


if __name__ == "__main__":
    unittest.main()
