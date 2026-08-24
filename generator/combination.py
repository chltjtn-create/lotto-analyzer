"""Condition-based Lotto 6/45 combination generation."""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date
from typing import Iterable

from lotto_analyzer.analysis.pattern import analyze_draw_pattern
from lotto_analyzer.analysis.scoring import NumberScore
from lotto_analyzer.domain.models import LottoDraw

DISCLAIMER = "본 결과는 통계 분석 기반 참고자료이며\n당첨을 보장하지 않습니다."


class CombinationGenerationError(Exception):
    """Raised when combinations cannot be generated with the provided conditions."""


def _validate_count_bound(name: str, value: int | tuple[int, int] | None) -> None:
    """Validate that a count constraint is None, an exact count, or a min/max range."""
    if value is None:
        return
    if isinstance(value, tuple):
        low, high = value
        if not (0 <= low <= high <= 6):
            raise CombinationGenerationError(f"{name} range must satisfy 0 <= min <= max <= 6.")
        return
    if not 0 <= value <= 6:
        raise CombinationGenerationError(f"{name} must be between 0 and 6.")


def _count_matches(value: int | tuple[int, int] | None, actual: int) -> bool:
    """Check whether an actual count satisfies an exact count, a range, or no constraint."""
    if value is None:
        return True
    if isinstance(value, tuple):
        low, high = value
        return low <= actual <= high
    return actual == value


@dataclass(frozen=True, slots=True)
class CombinationConstraints:
    """Store user-selectable constraints for generated combinations."""

    odd_count: int | tuple[int, int] | None = (2, 4)
    even_count: int | tuple[int, int] | None = (2, 4)
    low_count: int | tuple[int, int] | None = (2, 4)
    high_count: int | tuple[int, int] | None = (2, 4)
    sum_min: int = 100
    sum_max: int = 180
    max_consecutive_pairs: int = 1
    max_same_last_digit: int = 2
    min_ac_value: int | None = 4
    exclude_arithmetic_sequence: bool = True
    max_per_decade: int | None = 3
    exclude_latest_draw_numbers: bool = False

    def validate(self) -> None:
        """Validate combination constraint values."""
        for name in ("odd_count", "even_count", "low_count", "high_count"):
            _validate_count_bound(name, getattr(self, name))
        if self.sum_min > self.sum_max:
            raise CombinationGenerationError("sum_min must be less than or equal to sum_max.")
        if self.max_consecutive_pairs < 0:
            raise CombinationGenerationError("max_consecutive_pairs must be non-negative.")
        if self.max_same_last_digit < 1:
            raise CombinationGenerationError("max_same_last_digit must be at least 1.")
        if self.min_ac_value is not None and not 0 <= self.min_ac_value <= 10:
            raise CombinationGenerationError("min_ac_value must be between 0 and 10.")
        if self.max_per_decade is not None and not 1 <= self.max_per_decade <= 6:
            raise CombinationGenerationError("max_per_decade must be between 1 and 6.")


@dataclass(frozen=True, slots=True)
class GeneratedCombination:
    """Store one generated combination and its explainable metadata."""

    numbers: tuple[int, ...]
    score: float
    odd_even: str
    high_low: str
    total_sum: int
    hot_count: int
    warm_count: int
    cold_count: int
    strategy: str
    disclaimer: str = DISCLAIMER

    def to_dict(self) -> dict[str, object]:
        """Convert the generated combination to a report-friendly dictionary."""
        return {
            "numbers": list(self.numbers),
            "score": round(self.score, 2),
            "odd_even": self.odd_even,
            "high_low": self.high_low,
            "total_sum": self.total_sum,
            "hot_count": self.hot_count,
            "warm_count": self.warm_count,
            "cold_count": self.cold_count,
            "strategy": self.strategy,
            "disclaimer": self.disclaimer,
        }


def generate_combinations(
    scores_by_number: dict[int, NumberScore],
    latest_draw: LottoDraw | None = None,
    constraints: CombinationConstraints = CombinationConstraints(),
    strategy: str = "Hybrid",
    count: int = 5,
    seed: int | None = None,
    max_attempts: int = 20000,
    excluded_combinations: Iterable[tuple[int, ...]] = (),
) -> list[GeneratedCombination]:
    """Generate unique combinations that satisfy constraints and strategy rules."""
    constraints.validate()
    if count < 1:
        raise CombinationGenerationError("count must be greater than 0.")
    if not scores_by_number:
        raise CombinationGenerationError("scores_by_number is required.")

    rng = random.Random(seed)
    pool = _build_candidate_pool(scores_by_number, latest_draw, constraints)
    if len(pool) < 6:
        raise CombinationGenerationError("Not enough candidate numbers to generate combinations.")

    excluded = {tuple(sorted(combo)) for combo in excluded_combinations}
    generated: dict[tuple[int, ...], GeneratedCombination] = {}
    attempts = 0
    strategy_name = _normalize_strategy(strategy)

    while len(generated) < count and attempts < max_attempts:
        attempts += 1
        numbers = _pick_numbers(pool, scores_by_number, strategy_name, rng)
        if numbers in generated or numbers in excluded:
            continue
        if not _matches_constraints(numbers, constraints):
            continue
        generated[numbers] = _build_generated_combination(numbers, scores_by_number, strategy_name)

    if len(generated) < count:
        raise CombinationGenerationError(
            f"Could only generate {len(generated)} combinations with the provided conditions."
        )

    return list(generated.values())


def _build_candidate_pool(
    scores_by_number: dict[int, NumberScore],
    latest_draw: LottoDraw | None,
    constraints: CombinationConstraints,
) -> list[int]:
    """Build a candidate number pool, optionally excluding the latest draw numbers."""
    excluded = set(latest_draw.numbers) if latest_draw and constraints.exclude_latest_draw_numbers else set()
    return [number for number in range(1, 46) if number in scores_by_number and number not in excluded]


def _normalize_strategy(strategy: str) -> str:
    """Normalize and validate a generation strategy name."""
    allowed = {"Random", "Balanced", "Hot Mix", "Cold Mix", "Hybrid"}
    normalized = strategy.strip()
    if normalized not in allowed:
        raise CombinationGenerationError(f"Unsupported strategy: {strategy}")
    return normalized


def _pick_numbers(
    pool: list[int],
    scores_by_number: dict[int, NumberScore],
    strategy: str,
    rng: random.Random,
) -> tuple[int, ...]:
    """Pick six candidate numbers according to the requested strategy."""
    if strategy == "Random":
        return tuple(sorted(rng.sample(pool, 6)))

    grouped = _group_pool_by_category(pool, scores_by_number)
    if strategy == "Hot Mix":
        numbers = _sample_category_mix(grouped, {"Hot": 3, "Warm": 2, "Cold": 1}, rng)
    elif strategy == "Cold Mix":
        numbers = _sample_category_mix(grouped, {"Hot": 1, "Warm": 3, "Cold": 2}, rng)
    elif strategy == "Balanced":
        numbers = _sample_category_mix(grouped, {"Hot": 2, "Warm": 2, "Cold": 2}, rng)
    else:
        numbers = _sample_category_mix(grouped, {"Hot": 2, "Warm": 3, "Cold": 1}, rng)

    return tuple(sorted(_fill_to_six(numbers, pool, rng)))


def _sample_category_mix(
    grouped: dict[str, list[int]],
    mix: dict[str, int],
    rng: random.Random,
) -> list[int]:
    """Sample numbers by category, falling back gracefully when a category is small."""
    selected: list[int] = []
    for category, wanted_count in mix.items():
        candidates = [number for number in grouped.get(category, []) if number not in selected]
        selected.extend(rng.sample(candidates, min(wanted_count, len(candidates))))
    return selected


def _fill_to_six(selected: list[int], pool: list[int], rng: random.Random) -> list[int]:
    """Fill a partial selection with random unique numbers until it has six numbers."""
    remaining = [number for number in pool if number not in selected]
    selected.extend(rng.sample(remaining, 6 - len(selected)))
    return selected


def _ac_value(numbers: tuple[int, ...]) -> int:
    """Calculate the arithmetic complexity (AC) value of a sorted number combination."""
    sorted_numbers = sorted(numbers)
    diffs = {
        sorted_numbers[j] - sorted_numbers[i]
        for i in range(len(sorted_numbers))
        for j in range(i + 1, len(sorted_numbers))
    }
    return len(diffs) - (len(sorted_numbers) - 1)


def _is_arithmetic_sequence(numbers: tuple[int, ...]) -> bool:
    """Return whether sorted numbers form a sequence with a constant gap."""
    sorted_numbers = sorted(numbers)
    diffs = {second - first for first, second in zip(sorted_numbers, sorted_numbers[1:])}
    return len(diffs) == 1


def _max_decade_count(numbers: tuple[int, ...]) -> int:
    """Return the largest count of numbers sharing the same ten's-place decade."""
    decade_counts: dict[int, int] = {}
    for number in numbers:
        decade = (number - 1) // 10
        decade_counts[decade] = decade_counts.get(decade, 0) + 1
    return max(decade_counts.values(), default=0)


def _matches_constraints(numbers: tuple[int, ...], constraints: CombinationConstraints) -> bool:
    """Return whether the numbers satisfy all configured constraints."""
    odd_count = sum(1 for number in numbers if number % 2 == 1)
    even_count = 6 - odd_count
    low_count = sum(1 for number in numbers if number <= 22)
    high_count = 6 - low_count
    total_sum = sum(numbers)
    consecutive_pairs = sum(1 for first, second in zip(numbers, numbers[1:]) if second - first == 1)
    last_digit_counts: dict[int, int] = {}
    for number in numbers:
        last_digit_counts[number % 10] = last_digit_counts.get(number % 10, 0) + 1

    return (
        _count_matches(constraints.odd_count, odd_count)
        and _count_matches(constraints.even_count, even_count)
        and _count_matches(constraints.low_count, low_count)
        and _count_matches(constraints.high_count, high_count)
        and constraints.sum_min <= total_sum <= constraints.sum_max
        and consecutive_pairs <= constraints.max_consecutive_pairs
        and max(last_digit_counts.values(), default=0) <= constraints.max_same_last_digit
        and (constraints.min_ac_value is None or _ac_value(numbers) >= constraints.min_ac_value)
        and (not constraints.exclude_arithmetic_sequence or not _is_arithmetic_sequence(numbers))
        and (constraints.max_per_decade is None or _max_decade_count(numbers) <= constraints.max_per_decade)
    )


def _build_generated_combination(
    numbers: tuple[int, ...],
    scores_by_number: dict[int, NumberScore],
    strategy: str,
) -> GeneratedCombination:
    """Build metadata for a generated combination."""
    fake_draw = LottoDraw(draw_no=1, draw_date=date.today(), numbers=numbers, bonus=_bonus_for(numbers))
    pattern = analyze_draw_pattern(fake_draw)
    categories = [scores_by_number[number].category for number in numbers]
    score = sum(scores_by_number[number].final_score for number in numbers) / 6
    return GeneratedCombination(
        numbers=numbers,
        score=score,
        odd_even=pattern.odd_even_ratio,
        high_low=pattern.high_low_ratio,
        total_sum=pattern.total_sum,
        hot_count=categories.count("Hot"),
        warm_count=categories.count("Warm"),
        cold_count=categories.count("Cold"),
        strategy=strategy,
    )


def _group_pool_by_category(
    pool: Iterable[int],
    scores_by_number: dict[int, NumberScore],
) -> dict[str, list[int]]:
    """Group candidate numbers by score category."""
    grouped = {"Hot": [], "Warm": [], "Cold": []}
    for number in pool:
        grouped[scores_by_number[number].category].append(number)
    return grouped


def _bonus_for(numbers: tuple[int, ...]) -> int:
    """Pick any valid bonus number not present in a generated combination."""
    used = set(numbers)
    for number in range(1, 46):
        if number not in used:
            return number
    raise CombinationGenerationError("Could not find a valid bonus number.")
