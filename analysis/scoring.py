"""Number scoring and Hot/Warm/Cold classification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from lotto_analyzer.analysis.frequency import analyze_number_frequency
from lotto_analyzer.domain.models import LottoDraw


class ScoringError(Exception):
    """Raised when number scoring cannot be performed."""


@dataclass(frozen=True, slots=True)
class ScoreWeights:
    """Store final-score weights for number scoring."""

    frequency: float = 0.2
    recency: float = 0.3
    gap: float = 0.3
    momentum: float = 0.2

    def validate(self) -> None:
        """Validate that score weights are non-negative and add up to 1."""
        values = (self.frequency, self.recency, self.gap, self.momentum)
        if any(value < 0 for value in values):
            raise ScoringError("Score weights must be non-negative.")
        if round(sum(values), 6) != 1:
            raise ScoringError("Score weights must add up to 1.")


@dataclass(frozen=True, slots=True)
class NumberScore:
    """Store score values and category for one Lotto number."""

    number: int
    frequency_score: float
    recency_score: float
    gap_score: float
    momentum_score: float
    final_score: float
    category: str

    def to_dict(self) -> dict[str, int | float | str]:
        """Convert the score to a JSON-friendly dictionary."""
        return {
            "number": self.number,
            "frequency_score": round(self.frequency_score, 2),
            "recency_score": round(self.recency_score, 2),
            "gap_score": round(self.gap_score, 2),
            "momentum_score": round(self.momentum_score, 2),
            "final_score": round(self.final_score, 2),
            "category": self.category,
        }


def calculate_number_scores(
    draws: Iterable[LottoDraw],
    weights: ScoreWeights = ScoreWeights(),
) -> dict[int, NumberScore]:
    """Calculate relative scores and Hot/Warm/Cold categories for numbers 1-45."""
    weights.validate()
    stats_by_number = analyze_number_frequency(draws, windows=(10, 30, 100, 300))
    max_total = max(stat.total_count for stat in stats_by_number.values())
    max_gap = max(stat.missing_draws for stat in stats_by_number.values())

    raw_scores: dict[int, dict[str, float]] = {}
    for number, stats in stats_by_number.items():
        frequency_score = _safe_ratio(stats.total_count, max_total) * 100
        recency_score = _calculate_recency_score(stats.recent_counts, stats.recent_available_draws)
        gap_score = _safe_ratio(stats.missing_draws, max_gap) * 100
        momentum_score = _calculate_momentum_score(
            stats.recent_counts,
            stats.recent_available_draws,
        )
        final_score = (
            frequency_score * weights.frequency
            + recency_score * weights.recency
            + gap_score * weights.gap
            + momentum_score * weights.momentum
        )
        raw_scores[number] = {
            "frequency_score": frequency_score,
            "recency_score": recency_score,
            "gap_score": gap_score,
            "momentum_score": momentum_score,
            "final_score": final_score,
        }

    categories = classify_numbers(raw_scores)
    return {
        number: NumberScore(
            number=number,
            frequency_score=values["frequency_score"],
            recency_score=values["recency_score"],
            gap_score=values["gap_score"],
            momentum_score=values["momentum_score"],
            final_score=values["final_score"],
            category=categories[number],
        )
        for number, values in raw_scores.items()
    }


def classify_numbers(raw_scores: dict[int, dict[str, float]]) -> dict[int, str]:
    """Classify numbers into Hot, Warm, and Cold by final-score rank."""
    ranked = sorted(
        raw_scores,
        key=lambda number: (-raw_scores[number]["final_score"], number),
    )
    hot_count = 9
    cold_count = 9
    categories: dict[int, str] = {}
    for index, number in enumerate(ranked):
        if index < hot_count:
            categories[number] = "Hot"
        elif index >= len(ranked) - cold_count:
            categories[number] = "Cold"
        else:
            categories[number] = "Warm"
    return categories


def score_rows(scores_by_number: dict[int, NumberScore]) -> list[dict[str, int | float | str]]:
    """Convert score mapping into rows sorted by final score descending."""
    return [
        scores_by_number[number].to_dict()
        for number in sorted(
            scores_by_number,
            key=lambda item: (-scores_by_number[item].final_score, item),
        )
    ]


def category_groups(scores_by_number: dict[int, NumberScore]) -> dict[str, list[int]]:
    """Return numbers grouped by Hot, Warm, and Cold category."""
    groups = {"Hot": [], "Warm": [], "Cold": []}
    for number, score in sorted(scores_by_number.items()):
        groups[score.category].append(number)
    return groups


def _calculate_recency_score(
    recent_counts: dict[int, int],
    available_draws: dict[int, int],
) -> float:
    """Calculate weighted recent appearance score from recent windows."""
    weights = {10: 0.5, 30: 0.3, 100: 0.2}
    score = 0.0
    for window, weight in weights.items():
        available = available_draws.get(window, 0)
        score += _safe_ratio(recent_counts.get(window, 0), available) * 100 * weight
    return score


def _calculate_momentum_score(
    recent_counts: dict[int, int],
    available_draws: dict[int, int],
) -> float:
    """Calculate a simple recent trend score between short and longer windows."""
    recent_10_rate = _safe_ratio(recent_counts.get(10, 0), available_draws.get(10, 0))
    recent_100_rate = _safe_ratio(recent_counts.get(100, 0), available_draws.get(100, 0))
    return _clip(50 + ((recent_10_rate - recent_100_rate) * 100), 0, 100)


def _safe_ratio(value: int | float, denominator: int | float) -> float:
    """Return value / denominator while protecting against division by zero."""
    if denominator == 0:
        return 0.0
    return float(value) / float(denominator)


def _clip(value: float, low: float, high: float) -> float:
    """Clip a numeric score into a closed range."""
    return max(low, min(high, value))
