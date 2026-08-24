"""Pattern analysis for Lotto 6/45 draw data."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from statistics import mean, median
from typing import Iterable

from lotto_analyzer.domain.models import LottoDraw

SECTIONS = ((1, 10), (11, 20), (21, 30), (31, 40), (41, 45))


class PatternAnalysisError(Exception):
    """Raised when draw pattern analysis cannot be performed."""


@dataclass(frozen=True, slots=True)
class DrawPattern:
    """Store pattern values calculated for one draw."""

    draw_no: int
    odd_count: int
    even_count: int
    low_count: int
    high_count: int
    consecutive_pairs: tuple[tuple[int, int], ...]
    last_digit_counts: dict[int, int]
    total_sum: int
    section_counts: dict[str, int]

    @property
    def odd_even_ratio(self) -> str:
        """Return the odd/even ratio as text."""
        return f"{self.odd_count}:{self.even_count}"

    @property
    def high_low_ratio(self) -> str:
        """Return the high/low ratio as text in low:high order."""
        return f"{self.low_count}:{self.high_count}"

    @property
    def consecutive_pair_count(self) -> int:
        """Return the number of consecutive pairs in the draw."""
        return len(self.consecutive_pairs)

    @property
    def max_same_last_digit(self) -> int:
        """Return the largest same-last-digit group size."""
        return max(self.last_digit_counts.values(), default=0)

    def to_dict(self) -> dict[str, object]:
        """Convert the draw pattern to a report-friendly dictionary."""
        row: dict[str, object] = {
            "draw_no": self.draw_no,
            "odd_even": self.odd_even_ratio,
            "odd_count": self.odd_count,
            "even_count": self.even_count,
            "high_low": self.high_low_ratio,
            "low_count": self.low_count,
            "high_count": self.high_count,
            "consecutive_pairs": ",".join(
                f"{first}-{second}" for first, second in self.consecutive_pairs
            ),
            "consecutive_pair_count": self.consecutive_pair_count,
            "max_same_last_digit": self.max_same_last_digit,
            "total_sum": self.total_sum,
        }
        row.update({f"section_{key}": value for key, value in self.section_counts.items()})
        return row


@dataclass(frozen=True, slots=True)
class PatternSummary:
    """Store aggregate pattern analysis across many draws."""

    patterns: list[DrawPattern]
    odd_even_frequency: dict[str, int]
    high_low_frequency: dict[str, int]
    consecutive_draw_count: int
    consecutive_rate: float
    last_digit_frequency: dict[int, int]
    section_totals: dict[str, int]
    sum_min: int
    sum_max: int
    sum_average: float
    sum_median: float

    def to_dict(self) -> dict[str, object]:
        """Convert the summary to a JSON-friendly dictionary."""
        return {
            "draw_count": len(self.patterns),
            "odd_even_frequency": self.odd_even_frequency,
            "high_low_frequency": self.high_low_frequency,
            "consecutive_draw_count": self.consecutive_draw_count,
            "consecutive_rate": self.consecutive_rate,
            "last_digit_frequency": self.last_digit_frequency,
            "section_totals": self.section_totals,
            "sum_min": self.sum_min,
            "sum_max": self.sum_max,
            "sum_average": round(self.sum_average, 2),
            "sum_median": self.sum_median,
        }


def analyze_draw_pattern(draw: LottoDraw) -> DrawPattern:
    """Calculate odd/even, high/low, consecutive, digit, sum, and section patterns."""
    numbers = tuple(sorted(draw.numbers))
    odd_count = sum(1 for number in numbers if number % 2 == 1)
    even_count = 6 - odd_count
    low_count = sum(1 for number in numbers if number <= 22)
    high_count = 6 - low_count

    return DrawPattern(
        draw_no=draw.draw_no,
        odd_count=odd_count,
        even_count=even_count,
        low_count=low_count,
        high_count=high_count,
        consecutive_pairs=_find_consecutive_pairs(numbers),
        last_digit_counts=dict(Counter(number % 10 for number in numbers)),
        total_sum=sum(numbers),
        section_counts=_count_sections(numbers),
    )


def analyze_patterns(draws: Iterable[LottoDraw]) -> PatternSummary:
    """Analyze pattern rows and aggregate frequencies for many draws."""
    patterns = [analyze_draw_pattern(draw) for draw in sorted(draws, key=lambda item: item.draw_no)]
    if not patterns:
        raise PatternAnalysisError("At least one draw is required for pattern analysis.")

    odd_even_frequency = dict(Counter(pattern.odd_even_ratio for pattern in patterns))
    high_low_frequency = dict(Counter(pattern.high_low_ratio for pattern in patterns))
    consecutive_draw_count = sum(1 for pattern in patterns if pattern.consecutive_pair_count > 0)
    last_digit_frequency: Counter[int] = Counter()
    section_totals: Counter[str] = Counter()
    sums = [pattern.total_sum for pattern in patterns]

    for pattern in patterns:
        last_digit_frequency.update(pattern.last_digit_counts)
        section_totals.update(pattern.section_counts)

    return PatternSummary(
        patterns=patterns,
        odd_even_frequency=odd_even_frequency,
        high_low_frequency=high_low_frequency,
        consecutive_draw_count=consecutive_draw_count,
        consecutive_rate=round(consecutive_draw_count / len(patterns), 4),
        last_digit_frequency=dict(sorted(last_digit_frequency.items())),
        section_totals=dict(section_totals),
        sum_min=min(sums),
        sum_max=max(sums),
        sum_average=mean(sums),
        sum_median=median(sums),
    )


def pattern_rows(summary: PatternSummary) -> list[dict[str, object]]:
    """Return per-draw pattern rows sorted by draw number."""
    return [pattern.to_dict() for pattern in summary.patterns]


def _find_consecutive_pairs(numbers: tuple[int, ...]) -> tuple[tuple[int, int], ...]:
    """Find adjacent number pairs such as 7-8 or 31-32."""
    pairs = []
    for first, second in zip(numbers, numbers[1:]):
        if second - first == 1:
            pairs.append((first, second))
    return tuple(pairs)


def _count_sections(numbers: tuple[int, ...]) -> dict[str, int]:
    """Count how many numbers fall into each configured number section."""
    counts = {f"{start}-{end}": 0 for start, end in SECTIONS}
    for number in numbers:
        for start, end in SECTIONS:
            if start <= number <= end:
                counts[f"{start}-{end}"] += 1
                break
    return counts
