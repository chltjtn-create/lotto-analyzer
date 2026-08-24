"""Number frequency analysis for Lotto 6/45 draw data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from lotto_analyzer.domain.models import LottoDraw


class FrequencyAnalysisError(Exception):
    """Raised when frequency analysis cannot be performed."""


@dataclass(frozen=True, slots=True)
class NumberFrequencyStats:
    """Store frequency statistics for one Lotto number."""

    number: int
    total_count: int
    recent_counts: dict[int, int]
    recent_available_draws: dict[int, int]
    missing_draws: int
    last_seen_draw_no: int | None
    appeared_in_latest_draw: bool
    analyzed_draws: int
    latest_draw_no: int

    def to_dict(self) -> dict[str, int | bool | None]:
        """Convert the statistics to a JSON-friendly dictionary."""
        row: dict[str, int | bool | None] = {
            "number": self.number,
            "total_count": self.total_count,
            "missing_draws": self.missing_draws,
            "last_seen_draw_no": self.last_seen_draw_no,
            "appeared_in_latest_draw": self.appeared_in_latest_draw,
            "analyzed_draws": self.analyzed_draws,
            "latest_draw_no": self.latest_draw_no,
        }
        for window in sorted(self.recent_counts):
            row[f"recent_{window}_count"] = self.recent_counts[window]
            row[f"recent_{window}_available_draws"] = self.recent_available_draws[window]
        return row


def analyze_number_frequency(
    draws: Iterable[LottoDraw],
    windows: tuple[int, ...] = (10, 30, 100, 300),
) -> dict[int, NumberFrequencyStats]:
    """Analyze total, recent, and missing-draw counts for numbers 1 through 45."""
    normalized_draws = _normalize_draws(draws)
    _validate_windows(windows)

    if not normalized_draws:
        raise FrequencyAnalysisError("At least one draw is required for frequency analysis.")

    latest_draw = normalized_draws[-1]
    latest_numbers = set(latest_draw.numbers)
    total_counts = _count_numbers(normalized_draws)
    last_seen = _find_last_seen_draws(normalized_draws)

    results: dict[int, NumberFrequencyStats] = {}
    for number in range(1, 46):
        recent_counts, available_draws = _count_recent_windows(
            number,
            normalized_draws,
            windows,
        )
        last_seen_draw_no = last_seen.get(number)
        missing_draws = _calculate_missing_draws(number, normalized_draws, last_seen_draw_no)

        results[number] = NumberFrequencyStats(
            number=number,
            total_count=total_counts[number],
            recent_counts=recent_counts,
            recent_available_draws=available_draws,
            missing_draws=missing_draws,
            last_seen_draw_no=last_seen_draw_no,
            appeared_in_latest_draw=number in latest_numbers,
            analyzed_draws=len(normalized_draws),
            latest_draw_no=latest_draw.draw_no,
        )

    return results


def format_number_stats(stats: NumberFrequencyStats) -> str:
    """Format one number's statistics for simple console output."""
    lines = [
        f"번호 {stats.number}",
        "",
        f"전체 : {stats.total_count}회",
    ]
    for window in sorted(stats.recent_counts):
        lines.append(f"최근{window}회 : {stats.recent_counts[window]}회")
    lines.append(f"미출현 : {stats.missing_draws}회차")
    return "\n".join(lines)


def stats_to_rows(stats_by_number: dict[int, NumberFrequencyStats]) -> list[dict[str, int | bool | None]]:
    """Convert a stats mapping into sorted row dictionaries."""
    return [stats_by_number[number].to_dict() for number in sorted(stats_by_number)]


def _normalize_draws(draws: Iterable[LottoDraw]) -> list[LottoDraw]:
    """Return draws sorted by draw number while checking duplicate draw numbers."""
    normalized_draws = sorted(draws, key=lambda draw: draw.draw_no)
    draw_numbers = [draw.draw_no for draw in normalized_draws]
    if len(draw_numbers) != len(set(draw_numbers)):
        raise FrequencyAnalysisError("Draw numbers must not contain duplicates.")
    return normalized_draws


def _validate_windows(windows: tuple[int, ...]) -> None:
    """Validate recent-window sizes before analysis starts."""
    if not windows:
        raise FrequencyAnalysisError("At least one recent window is required.")
    if any(not isinstance(window, int) for window in windows):
        raise FrequencyAnalysisError("Recent windows must be integers.")
    if any(window < 1 for window in windows):
        raise FrequencyAnalysisError("Recent windows must be greater than 0.")
    if len(windows) != len(set(windows)):
        raise FrequencyAnalysisError("Recent windows must not contain duplicates.")


def _count_numbers(draws: list[LottoDraw]) -> dict[int, int]:
    """Count total appearances for each main Lotto number."""
    counts = {number: 0 for number in range(1, 46)}
    for draw in draws:
        for number in draw.numbers:
            counts[number] += 1
    return counts


def _find_last_seen_draws(draws: list[LottoDraw]) -> dict[int, int]:
    """Find the latest draw number where each Lotto number appeared."""
    last_seen: dict[int, int] = {}
    for draw in draws:
        for number in draw.numbers:
            last_seen[number] = draw.draw_no
    return last_seen


def _count_recent_windows(
    number: int,
    draws: list[LottoDraw],
    windows: tuple[int, ...],
) -> tuple[dict[int, int], dict[int, int]]:
    """Count a number's appearances in each recent draw window."""
    recent_counts: dict[int, int] = {}
    available_draws: dict[int, int] = {}

    for window in windows:
        recent_draws = draws[-window:]
        recent_counts[window] = sum(1 for draw in recent_draws if number in draw.numbers)
        available_draws[window] = len(recent_draws)

    return recent_counts, available_draws


def _calculate_missing_draws(
    number: int,
    draws: list[LottoDraw],
    last_seen_draw_no: int | None,
) -> int:
    """Calculate how many analyzed draws passed since a number last appeared."""
    if last_seen_draw_no is None:
        return len(draws)

    missing_count = 0
    for draw in reversed(draws):
        if number in draw.numbers:
            break
        missing_count += 1
    return missing_count
