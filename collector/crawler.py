"""Crawler for Donghaeng Lottery Lotto 6/45 draw data."""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from lotto_analyzer.config import (
    DEFAULT_HTTP_TIMEOUT_SECONDS,
    DHLottery_API_QUERY_PARAM,
    DHLottery_API_URL,
    DHLottery_RESULT_PAGE_URL,
    FIRST_LOTTO_DRAW_DATE,
)
from lotto_analyzer.domain.models import LottoDraw
from lotto_analyzer.domain.validators import DrawValidationError, validate_draw_no

JsonFetcher = Callable[[int], Mapping[str, Any] | None]
HtmlFetcher = Callable[[int], str]


class LottoCrawlerError(Exception):
    """Base exception for crawler failures."""


class LottoNetworkError(LottoCrawlerError):
    """Raised when the crawler cannot receive a usable HTTP response."""


class LottoDataError(LottoCrawlerError):
    """Raised when the received payload cannot be parsed or validated."""


class LottoDrawNotFoundError(LottoCrawlerError):
    """Raised when a requested draw number does not exist."""


class LottoCrawler:
    """Fetch and validate Lotto 6/45 draw data from Donghaeng Lottery."""

    def __init__(
        self,
        endpoint_url: str = DHLottery_API_URL,
        result_page_url: str = DHLottery_RESULT_PAGE_URL,
        timeout_seconds: float = DEFAULT_HTTP_TIMEOUT_SECONDS,
        fetch_json: JsonFetcher | None = None,
        fetch_html: HtmlFetcher | None = None,
    ) -> None:
        """Create a crawler with an optional injected JSON fetcher for tests."""
        self.endpoint_url = endpoint_url
        self.result_page_url = result_page_url
        self.timeout_seconds = timeout_seconds
        self._fetch_json = fetch_json
        self._fetch_html = fetch_html

    def fetch_draw(self, draw_no: int) -> LottoDraw:
        """Fetch one draw and return a validated LottoDraw object."""
        validate_draw_no(draw_no)
        try:
            record = self._request_record(draw_no)
        except LottoDataError:
            return self._request_result_page_draw(draw_no)

        if record is None:
            raise LottoDrawNotFoundError(f"Draw {draw_no} was not found.")

        try:
            return LottoDraw.from_dhlottery_new_payload(record)
        except (KeyError, TypeError, ValueError, DrawValidationError) as exc:
            raise LottoDataError(f"Invalid payload for draw {draw_no}: {exc}") from exc

    def fetch_range(
        self,
        start_draw: int,
        end_draw: int,
        skip_missing: bool = False,
    ) -> list[LottoDraw]:
        """Fetch a closed range of draw numbers in ascending order."""
        validate_draw_no(start_draw)
        validate_draw_no(end_draw)
        if start_draw > end_draw:
            raise LottoDataError("start_draw must be less than or equal to end_draw.")

        draws: list[LottoDraw] = []
        for draw_no in range(start_draw, end_draw + 1):
            try:
                draws.append(self.fetch_draw(draw_no))
            except LottoDrawNotFoundError:
                if not skip_missing:
                    raise
        return draws

    def collect_until_latest(self, start_draw: int = 1) -> list[LottoDraw]:
        """Fetch draws from start_draw through the latest available draw."""
        latest_draw = self.find_latest_draw_no()
        return self.fetch_range(start_draw, latest_draw)

    def find_latest_draw_no(self, reference_date: date | None = None) -> int:
        """Find the highest draw number available from the lottery endpoint."""
        estimated_latest = estimate_latest_draw_no(reference_date)
        high = max(1, estimated_latest + 5)

        if not self._draw_exists(1):
            raise LottoDataError("Could not verify draw 1 from the lottery endpoint.")

        while self._draw_exists(high):
            high *= 2

        low = 1
        while low + 1 < high:
            mid = (low + high) // 2
            if self._draw_exists(mid):
                low = mid
            else:
                high = mid
        return low

    def _draw_exists(self, draw_no: int) -> bool:
        """Return whether a draw exists while preserving real crawler errors."""
        try:
            self.fetch_draw(draw_no)
        except LottoDrawNotFoundError:
            return False
        return True

    def _request_record(self, draw_no: int) -> Mapping[str, Any] | None:
        """Request the raw draw record for one draw number, or None if not yet announced."""
        if self._fetch_json is not None:
            return self._fetch_json(draw_no)

        query = urlencode({DHLottery_API_QUERY_PARAM: draw_no})
        url = f"{self.endpoint_url}?{query}"
        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "lotto-analyzer/0.1",
            },
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                raw_body = response.read().decode(charset)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise LottoNetworkError(f"Failed to fetch draw {draw_no}: {exc}") from exc

        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise LottoDataError(
                f"Lottery endpoint did not return JSON for draw {draw_no}."
            ) from exc

        try:
            records = payload["data"]["list"]
        except (KeyError, TypeError) as exc:
            raise LottoDataError(f"Lottery endpoint returned an unexpected shape for draw {draw_no}.") from exc

        if not records:
            return None
        return records[0]

    def _request_result_page_draw(self, draw_no: int) -> LottoDraw:
        """Request and parse one draw from the official result HTML page."""
        html = self._request_result_page_html(draw_no)
        return _parse_result_page_html(draw_no, html)

    def _request_result_page_html(self, draw_no: int) -> str:
        """Request official draw-result HTML for one draw number."""
        if self._fetch_html is not None:
            return self._fetch_html(draw_no)

        query = urlencode({"method": "byWin", "drwNo": draw_no})
        url = f"{self.result_page_url}?{query}"
        request = Request(
            url,
            headers={
                "Accept": "text/html,application/xhtml+xml",
                "User-Agent": "lotto-analyzer/0.1",
            },
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(charset, errors="replace")
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise LottoNetworkError(f"Failed to fetch result page for draw {draw_no}: {exc}") from exc


def estimate_latest_draw_no(reference_date: date | None = None) -> int:
    """Estimate the latest possible draw number from the first draw date."""
    current_date = reference_date or date.today()
    if current_date < FIRST_LOTTO_DRAW_DATE:
        return 0
    elapsed_days = (current_date - FIRST_LOTTO_DRAW_DATE).days
    return (elapsed_days // 7) + 1


def _parse_result_page_html(draw_no: int, html: str) -> LottoDraw:
    """Parse draw numbers from the official draw-result HTML page."""
    if "서비스 접근 대기" in html or "접속이 차단" in html:
        raise LottoDataError("Lottery result page returned an access wait/block page.")

    numbers = [int(item) for item in re.findall(r'class="[^"]*ball_645[^"]*"[^>]*>\s*(\d{1,2})\s*<', html)]
    if len(numbers) < 7:
        raise LottoDataError(f"Could not parse draw numbers from result page for draw {draw_no}.")

    draw_date = _parse_result_page_date(html) or (
        FIRST_LOTTO_DRAW_DATE + timedelta(days=(draw_no - 1) * 7)
    )
    return LottoDraw(
        draw_no=draw_no,
        draw_date=draw_date,
        numbers=tuple(numbers[:6]),
        bonus=numbers[6],
    )


def _parse_result_page_date(html: str) -> date | None:
    """Parse the draw date from result-page text when available."""
    match = re.search(r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일\s*추첨', html)
    if not match:
        return None
    year, month, day = (int(match.group(index)) for index in range(1, 4))
    return datetime(year, month, day).date()
