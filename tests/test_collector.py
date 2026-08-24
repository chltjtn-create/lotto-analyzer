"""Tests for stage-one Lotto data collection."""

from __future__ import annotations

import unittest
from datetime import date
from typing import Any, Mapping

from lotto_analyzer.collector.crawler import (
    LottoCrawler,
    LottoDataError,
    LottoDrawNotFoundError,
    estimate_latest_draw_no,
)
from lotto_analyzer.domain.models import LottoDraw
from lotto_analyzer.domain.validators import DrawValidationError


def payload_for_draw(draw_no: int) -> dict[str, Any]:
    """Create a valid fake Donghaeng Lottery payload (legacy shape) for tests."""
    return {
        "returnValue": "success",
        "drwNo": draw_no,
        "drwNoDate": "2002-12-07",
        "drwtNo1": 10,
        "drwtNo2": 23,
        "drwtNo3": 29,
        "drwtNo4": 33,
        "drwtNo5": 37,
        "drwtNo6": 40,
        "bnusNo": 16,
    }


def record_for_draw(draw_no: int) -> dict[str, Any]:
    """Create a valid fake Donghaeng Lottery draw record (2026-01 redesign shape) for tests."""
    return {
        "ltEpsd": draw_no,
        "ltRflYmd": "20021207",
        "tm1WnNo": 10,
        "tm2WnNo": 23,
        "tm3WnNo": 29,
        "tm4WnNo": 33,
        "tm5WnNo": 37,
        "tm6WnNo": 40,
        "bnsWnNo": 16,
    }


class LottoDrawModelTest(unittest.TestCase):
    """Verify LottoDraw parsing and validation rules."""

    def test_parse_dhlottery_payload(self) -> None:
        """Parse a valid legacy-shape lottery payload into a LottoDraw."""
        draw = LottoDraw.from_dhlottery_payload(payload_for_draw(1))

        self.assertEqual(draw.draw_no, 1)
        self.assertEqual(draw.draw_date, date(2002, 12, 7))
        self.assertEqual(draw.numbers, (10, 23, 29, 33, 37, 40))
        self.assertEqual(draw.bonus, 16)

    def test_parse_dhlottery_new_payload(self) -> None:
        """Parse a valid 2026-01 redesign-shape lottery record into a LottoDraw."""
        draw = LottoDraw.from_dhlottery_new_payload(record_for_draw(1))

        self.assertEqual(draw.draw_no, 1)
        self.assertEqual(draw.draw_date, date(2002, 12, 7))
        self.assertEqual(draw.numbers, (10, 23, 29, 33, 37, 40))
        self.assertEqual(draw.bonus, 16)

    def test_reject_duplicate_winning_numbers(self) -> None:
        """Reject a draw when winning numbers contain duplicates."""
        with self.assertRaises(DrawValidationError):
            LottoDraw(
                draw_no=1,
                draw_date=date(2002, 12, 7),
                numbers=(1, 2, 3, 4, 5, 5),
                bonus=6,
            )

    def test_reject_bonus_duplicate(self) -> None:
        """Reject a draw when the bonus duplicates a winning number."""
        with self.assertRaises(DrawValidationError):
            LottoDraw(
                draw_no=1,
                draw_date=date(2002, 12, 7),
                numbers=(1, 2, 3, 4, 5, 6),
                bonus=6,
            )


class LottoCrawlerTest(unittest.TestCase):
    """Verify crawler behavior with injected fake responses."""

    def test_fetch_draw_with_fake_payload(self) -> None:
        """Fetch one draw through an injected record provider."""
        crawler = LottoCrawler(fetch_json=lambda draw_no: record_for_draw(draw_no))

        draw = crawler.fetch_draw(1)

        self.assertEqual(draw.draw_no, 1)
        self.assertEqual(draw.numbers[0], 10)

    def test_fetch_range_returns_ordered_draws(self) -> None:
        """Fetch a closed range and preserve ascending draw order."""
        crawler = LottoCrawler(fetch_json=lambda draw_no: record_for_draw(draw_no))

        draws = crawler.fetch_range(1, 3)

        self.assertEqual([draw.draw_no for draw in draws], [1, 2, 3])

    def test_empty_record_raises_not_found(self) -> None:
        """Convert an empty (not-yet-announced) record list into a not-found exception."""
        crawler = LottoCrawler(fetch_json=lambda draw_no: None)

        with self.assertRaises(LottoDrawNotFoundError):
            crawler.fetch_draw(9999)

    def test_invalid_payload_raises_data_error(self) -> None:
        """Reject records that do not contain required fields."""
        crawler = LottoCrawler(fetch_json=lambda draw_no: {})

        with self.assertRaises(LottoDataError):
            crawler.fetch_draw(1)

    def test_html_result_page_fallback(self) -> None:
        """Parse draw data from official result-page style HTML when JSON fails."""
        html = """
        <div class="win_result">
            <p class="desc">(2002년 12월 07일 추첨)</p>
            <span class="ball_645 lrg ball1">10</span>
            <span class="ball_645 lrg ball2">23</span>
            <span class="ball_645 lrg ball3">29</span>
            <span class="ball_645 lrg ball4">33</span>
            <span class="ball_645 lrg ball5">37</span>
            <span class="ball_645 lrg ball5">40</span>
            <span class="ball_645 lrg ball1">16</span>
        </div>
        """
        crawler = LottoCrawler(
            fetch_json=lambda draw_no: (_ for _ in ()).throw(LottoDataError("not json")),
            fetch_html=lambda draw_no: html,
        )

        draw = crawler.fetch_draw(1)

        self.assertEqual(draw.draw_no, 1)
        self.assertEqual(draw.numbers, (10, 23, 29, 33, 37, 40))
        self.assertEqual(draw.bonus, 16)

    def test_estimate_latest_draw_no(self) -> None:
        """Estimate latest draw numbers from elapsed whole weeks."""
        self.assertEqual(estimate_latest_draw_no(date(2002, 12, 7)), 1)
        self.assertEqual(estimate_latest_draw_no(date(2002, 12, 14)), 2)
        self.assertEqual(estimate_latest_draw_no(date(2002, 12, 13)), 1)


if __name__ == "__main__":
    unittest.main()
