"""Domain models used across the Lotto analyzer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Mapping

from lotto_analyzer.domain.validators import validate_draw_values


@dataclass(frozen=True, slots=True)
class LottoDraw:
    """Represent one verified Lotto 6/45 draw."""

    draw_no: int
    draw_date: date
    numbers: tuple[int, ...]
    bonus: int

    def __post_init__(self) -> None:
        """Validate the draw immediately after dataclass construction."""
        normalized_numbers = validate_draw_values(
            self.draw_no,
            self.draw_date,
            self.numbers,
            self.bonus,
        )
        object.__setattr__(self, "numbers", normalized_numbers)

    @classmethod
    def from_dhlottery_payload(cls, payload: Mapping[str, Any]) -> "LottoDraw":
        """Build a LottoDraw from the official Donghaeng Lottery payload."""
        draw_no = int(payload["drwNo"])
        draw_date = date.fromisoformat(str(payload["drwNoDate"]))
        numbers = tuple(int(payload[f"drwtNo{index}"]) for index in range(1, 7))
        bonus = int(payload["bnusNo"])
        return cls(draw_no=draw_no, draw_date=draw_date, numbers=numbers, bonus=bonus)

    @classmethod
    def from_dhlottery_new_payload(cls, record: Mapping[str, Any]) -> "LottoDraw":
        """Build a LottoDraw from the redesigned (2026-01) Donghaeng Lottery payload."""
        draw_no = int(record["ltEpsd"])
        draw_date = datetime.strptime(str(record["ltRflYmd"]), "%Y%m%d").date()
        numbers = tuple(int(record[f"tm{index}WnNo"]) for index in range(1, 7))
        bonus = int(record["bnsWnNo"])
        return cls(draw_no=draw_no, draw_date=draw_date, numbers=numbers, bonus=bonus)

    def to_dict(self) -> dict[str, Any]:
        """Convert the draw to a JSON/CSV-friendly dictionary."""
        return {
            "draw_no": self.draw_no,
            "draw_date": self.draw_date.isoformat(),
            "num1": self.numbers[0],
            "num2": self.numbers[1],
            "num3": self.numbers[2],
            "num4": self.numbers[3],
            "num5": self.numbers[4],
            "num6": self.numbers[5],
            "bonus": self.bonus,
        }
