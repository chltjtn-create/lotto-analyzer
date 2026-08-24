"""Shared project configuration values."""

from __future__ import annotations

from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
REPORT_OUTPUT_DIR = BASE_DIR / "report" / "output"
LOTTO_DB_PATH = DATA_DIR / "lotto.db"
LOTTO_CSV_PATH = DATA_DIR / "lotto.csv"
LOTTO_JSON_PATH = DATA_DIR / "lotto.json"
DEFAULT_LOCAL_EXCEL_PATH = WORKSPACE_DIR / "로또 당첨번호 연속.xlsx"

DHLottery_API_URL = "https://www.dhlottery.co.kr/lt645/selectPstLt645Info.do"
DHLottery_API_QUERY_PARAM = "srchLtEpsd"
DHLottery_RESULT_PAGE_URL = "https://www.dhlottery.co.kr/gameResult.do"
DEFAULT_HTTP_TIMEOUT_SECONDS = 10.0
FIRST_LOTTO_DRAW_DATE = date(2002, 12, 7)


def ensure_project_directories() -> None:
    """Create runtime directories used by later project stages."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
